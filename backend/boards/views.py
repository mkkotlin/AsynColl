"""
REST API views for board, list, and card management.

This module provides ViewSets for handling CRUD operations and custom actions
on boards, lists, cards, and users. Includes user registration and activity tracking.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Board, List, Card, ActivityLog
from .serializers import BoardSerializer, ListSerializer, CardSerializer, UserSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for user listing and retrieval.
    
    Only authenticated users can access this endpoint. Provides basic user
    information for populating assignee lists and user references.
    
    Methods:
        list: Get all users.
        retrieve: Get a specific user by ID.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class BoardViewSet(viewsets.ModelViewSet):
    """
    Full CRUD API endpoint for boards.
    
    Authenticated users can create, read, update, and delete boards.
    Implements optimized querying with prefetch_related to reduce database hits.
    
    Methods:
        list: Get all boards.
        create: Create a new board.
        retrieve: Get a specific board with its lists, cards, and activities.
        update: Update board details.
        destroy: Delete a board.
    """
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optimize queryset with prefetch_related to eager-load nested data.
        
        Returns:
            QuerySet: Boards with pre-fetched lists, cards, and activities.
        """
        return Board.objects.prefetch_related('lists__cards', 'activities')


class ListViewSet(viewsets.ModelViewSet):
    """
    Full CRUD API endpoint for lists within boards.
    
    Authenticated users can manage lists and includes a custom reorder action
    for bulk-updating card positions.
    
    Methods:
        list: Get all lists.
        create: Create a new list.
        retrieve: Get a specific list with its cards.
        update: Update list details.
        destroy: Delete a list.
        reorder: Bulk update card positions within a list (custom action).
    """
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """
        Reorder cards within this list by updating their position field.
        
        Args:
            request: HTTP request containing card_ids list in request.data.
            pk: List ID to reorder cards in.
        
        Expected request payload:
            {"card_ids": [3, 1, 2]}
        
        Returns:
            Response: Success status with HTTP 200 OK.
        """
        card_ids = request.data.get('card_ids', [])

        for index, card_id in enumerate(card_ids):
            Card.objects.filter(id=card_id).update(position=index)

        return Response({"status": "reordered"}, status=status.HTTP_200_OK)


class CardViewSet(viewsets.ModelViewSet):
    """
    Full CRUD API endpoint for cards within lists.
    
    Authenticated users can manage cards. Includes custom partial_update to handle
    card moves between lists and assignment changes with activity logging.
    
    Methods:
        list: Get all cards.
        create: Create a new card.
        retrieve: Get a specific card.
        update: Replace a card.
        partial_update: Update card fields and log activities (custom implementation).
        destroy: Delete a card.
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        """
        Update card and create activity logs for list changes or assignments.
        
        Tracks when a card is moved to a different list or reassigned to a user,
        creating corresponding ActivityLog entries for audit trail and notifications.
        
        Args:
            request: HTTP PATCH request with updated card data.
            *args: Additional positional arguments.
            **kwargs: URL parameters (card ID).
        
        Returns:
            Response: Updated card data with HTTP 200 OK.
        """
        card = self.get_object()
        user = request.user if request.user.is_authenticated else None

        old_list = card.list
        old_assigned = card.assigned_to

        new_list = request.data.get('list')
        new_assigned = request.data.get('assigned_to_id')

        # Apply updates to card
        if new_list:
            card.list_id = new_list

        if new_assigned is not None:
            card.assigned_to_id = new_assigned

        card.save()

        # Log activity for list changes
        if new_list:
            ActivityLog.objects.create(
                board=card.list.board,
                user=user,
                action=f"moved '{card.title}' to list {card.list.name}",
                card=card
            )

        # Log activity for assignment changes
        if new_assigned is not None:
            ActivityLog.objects.create(
                board=card.list.board,
                user=user,
                action=f"assigned '{card.title}'",
                card=card
            )

        serializer = self.get_serializer(card)
        return Response(serializer.data)


@api_view(['POST'])
def register_user(request):
    """
    Register a new user account.
    
    Validates that the username is not already taken, then creates a new user
    with the provided credentials.
    
    Args:
        request: HTTP POST request with username and password in request.data.
    
    Expected request payload:
        {"username": "newuser", "password": "securepass"}
    
    Returns:
        Response: Success message with HTTP 201 CREATED, or error with HTTP 400 BAD_REQUEST.
    
    Raises:
        HTTP 400: If username already exists.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(username=username, password=password)
    return Response({"message": "User created successfully"})
    
    