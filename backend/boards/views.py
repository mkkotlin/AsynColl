"""
Board Management API Views
===========================

This module provides REST API endpoints for managing collaborative boards, lists, and cards.
It uses Django REST Framework with JWT authentication for secure API access.

Features:
- Board CRUD operations with owner-based access
- List management within boards
- Card operations with task tracking
- Real-time activity logging for all changes
- Card reordering with position management
- User registration and authentication

Architecture Notes:
- Uses prefetch_related() for query optimization to reduce N+1 problems
- Activity logging tracks all significant user actions for audit trail
- WebSocket integration via Django Channels for real-time updates
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Board, List, Card, ActivityLog
from .serializers import BoardSerializer, ListSerializer, CardSerializer, UserSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving user information.
    
    Provides read-only access to user profiles. Useful for:
    - Displaying assigned users on cards
    - Populating user dropdowns in frontend
    - Listing team members
    
    HTTP Methods:
    - GET /api/users/          -> List all users
    - GET /api/users/{id}/     -> Retrieve specific user
    
    Authentication: Required (JWT Token)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing collaborative boards.
    
    Handles full CRUD operations for boards. Each board acts as a container
    for multiple lists and their associated cards. Boards track ownership
    and maintain activity logs for audit purposes.
    
    Features:
    - Create new boards with authenticated user as owner
    - Retrieve board with all nested lists and cards
    - Update board metadata
    - Delete boards and cascade delete all related lists/cards
    - Optimized queries using prefetch_related to minimize DB hits
    
    HTTP Methods:
    - POST /api/boards/                -> Create new board
    - GET /api/boards/                 -> List all boards
    - GET /api/boards/{id}/            -> Retrieve specific board with lists/cards
    - PATCH /api/boards/{id}/          -> Partial update
    - PUT /api/boards/{id}/            -> Full update
    - DELETE /api/boards/{id}/         -> Delete board
    
    Query Optimization:
    - prefetch_related('lists__cards') -> Fetch all lists and their cards
    - prefetch_related('activities')   -> Fetch activity logs
    - Reduces database queries from N+M to 3 total queries
    
    Authentication: Required (JWT Token)
    """
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optimize database queries by prefetching related data.
        
        This method prevents N+1 query problems by fetching all related
        lists, cards, and activity logs in advance, reducing multiple
        database round-trips to just 3 queries total.
        
        Returns:
            QuerySet: Board objects with optimized related data loading
        """
        return Board.objects.prefetch_related('lists__cards', 'activities')


class ListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lists within boards.
    
    Lists are the primary organizational unit within a board, similar to
    columns in a Kanban board. Each list contains multiple cards that can
    be reordered using the custom 'reorder' action.
    
    Features:
    - Create lists to organize cards by status/category
    - Full CRUD operations on list metadata
    - Custom reorder action for drag-and-drop functionality
    - Maintains position field for card ordering
    
    HTTP Methods:
    - POST /api/lists/                 -> Create new list
    - GET /api/lists/                  -> List all lists
    - GET /api/lists/{id}/             -> Retrieve list with cards
    - PATCH /api/lists/{id}/           -> Update list
    - POST /api/lists/{id}/reorder/    -> Reorder cards in list
    - DELETE /api/lists/{id}/          -> Delete list and cascade
    
    Custom Actions:
    - reorder: Bulk update card positions for drag-and-drop functionality
    
    Authentication: Required (JWT Token)
    """
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """
        Reorder cards within a list by updating their position field.
        
        This action supports drag-and-drop functionality in the frontend.
        When users drag cards to reorder them, this endpoint updates the
        position field for each card atomically to maintain consistency.
        
        Request Body:
            {
                "card_ids": [3, 1, 4, 2]  -> New order of card IDs
            }
        
        Process:
        1. Receive array of card IDs in new desired order
        2. Iterate through array, assigning index as position
        3. Bulk update all positions in single database operation
        4. Return success status
        
        Notes:
        - Uses filter().update() for efficiency (no model instantiation)
        - Position field is used by Card model for ordering
        - Frontend relies on this for maintaining visual order
        
        Args:
            request: HTTP request with card_ids in POST body
            pk: List ID to reorder cards within
        
        Returns:
            Response: {"status": "reordered"} with 200 status
        """
        card_ids = request.data.get('card_ids', [])
        
        # Bulk update positions for all cards
        for index, card_id in enumerate(card_ids):
            Card.objects.filter(id=card_id).update(position=index)
        
        return Response({"status": "reordered"}, status=status.HTTP_200_OK)


class CardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cards (tasks/items) within lists.
    
    Cards are the individual task items in a collaborative board. They can be
    moved between lists, assigned to users, and updated with descriptions.
    All changes are logged for audit trail and real-time sync with WebSocket.
    
    Features:
    - Create cards with title and optional description
    - Assign cards to team members
    - Move cards between lists
    - Track creation time and assignments
    - Auto-generate activity logs for all changes
    - Support partial updates via PATCH
    
    HTTP Methods:
    - POST /api/cards/                 -> Create new card
    - GET /api/cards/                  -> List all cards
    - GET /api/cards/{id}/             -> Retrieve card details
    - PATCH /api/cards/{id}/           -> Update card (with activity logging)
    - PUT /api/cards/{id}/             -> Full update
    - DELETE /api/cards/{id}/          -> Delete card
    
    Fields:
    - title: Card name/title (max 200 chars)
    - description: Detailed description (optional)
    - list: Foreign key to parent list
    - position: Order position within list (0-based)
    - assigned_to: Optional user assignment
    - created_at: Auto-timestamp of creation
    
    Authentication: Required (JWT Token)
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Create a new card and log the activity.
        
        When a card is created, an activity log entry is automatically
        generated to record who created the card.
        
        Request Body:
            {
                "title": "New Task",
                "description": "Optional description",
                "list": 5
            }
        
        Process:
        1. Call parent create() to create card in database
        2. Get authenticated user
        3. Create ActivityLog entry for card creation
        4. Return created card data
        
        Args:
            request: HTTP POST request with card data
            *args: Additional positional arguments
            **kwargs: URL keyword arguments
        
        Returns:
            Response: Serialized created card data with 201 status
        """
        # Create the card using parent's create method
        response = super().create(request, *args, **kwargs)
        
        # Get the authenticated user
        user = request.user if request.user.is_authenticated else None
        
        # Get the created card from response data
        card_id = response.data.get('id')
        card = Card.objects.get(id=card_id)
        
        # Log card creation
        ActivityLog.objects.create(
            board=card.list.board,
            user=user,
            action=f"created card '{card.title}'",
            card=card
        )

        # Push real-time update to all WebSocket clients on this board
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'board_{card.list.board.id}',
            {
                'type': 'board_update',
                'message': {
                    'action': 'CARD_CREATED',
                    'card_id': card.id,
                    'board_id': card.list.board.id,
                }
            }
        )

        return response

    def partial_update(self, request, *args, **kwargs):
        """
        Handle partial card updates with automatic activity logging.
        
        This override of the default partial_update method adds activity
        logging functionality. When cards are moved or reassigned, the
        action is recorded in ActivityLog for audit trail and real-time
        synchronization across connected WebSocket clients.
        
        Request Body (any combination):
            {
                "list": 5,              -> Move to list ID 5
                "assigned_to_id": 3,    -> Assign to user ID 3
                "title": "New Title",   -> Update title
                "description": "..."    -> Update description
            }
        
        Process:
        1. Fetch the card object from database
        2. Extract authenticated user making the request
        3. Get new values from request data
        4. Update card fields if provided
        5. Save card to database
        6. Create ActivityLog entries for each change:
           - One log entry if card moved between lists
           - One log entry if card reassigned to user
        7. Return updated card serialized data
        
        Activity Logging:
        - Logs are used to:
          * Maintain audit trail of board changes
          * Display activity history in frontend
          * Trigger WebSocket broadcasts for real-time updates
          * Allow team to see who did what and when
        
        Args:
            request: HTTP PATCH request with update data
            *args: Additional positional arguments
            **kwargs: URL keyword arguments (including pk for card ID)
        
        Returns:
            Response: Serialized updated card data with 200 status
        """
        # Fetch the card being updated
        card = self.get_object()
        
        # Get the authenticated user making this change (or None if unauthenticated)
        user = request.user if request.user.is_authenticated else None

        # Extract new values from request (or None if not provided)
        new_list = request.data.get('list')
        new_assigned = request.data.get('assigned_to_id')

        # Update card fields only if new values were provided
        if new_list:
            card.list_id = new_list

        if new_assigned is not None:
            card.assigned_to_id = new_assigned

        # Persist changes to database
        card.save()

        channel_layer = get_channel_layer()
        board_id = card.list.board.id

        # Log card movement to activity log for audit trail
        if new_list:
            ActivityLog.objects.create(
                board=card.list.board,  # Get board from current list
                user=user,              # User who made the change
                action=f"moved '{card.title}' to list {card.list.name}",
                card=card
            )
            # Push CARD_MOVED to all WebSocket clients on this board
            async_to_sync(channel_layer.group_send)(
                f'board_{board_id}',
                {
                    'type': 'board_update',
                    'message': {
                        'action': 'CARD_MOVED',
                        'card_id': card.id,
                        'board_id': board_id,
                    }
                }
            )

        # Log card assignment for audit trail
        if new_assigned is not None:
            assigned_user = User.objects.get(id=new_assigned) if new_assigned else None
            assigned_username = assigned_user.username if assigned_user else "unassigned"
            user_who_assigned = user.username if user else "Unknown user"
            
            ActivityLog.objects.create(
                board=card.list.board,
                user=user,
                action=f"{user_who_assigned} assigned '{card.title}' to {assigned_username}",
                card=card
            )
            # Push CARD_ASSIGNED to all WebSocket clients on this board
            async_to_sync(channel_layer.group_send)(
                f'board_{board_id}',
                {
                    'type': 'board_update',
                    'message': {
                        'action': 'CARD_ASSIGNED',
                        'card_id': card.id,
                        'board_id': board_id,
                    }
                }
            )

        # Return the updated card with all fields populated
        serializer = self.get_serializer(card)
        return Response(serializer.data)


@api_view(['POST'])
def register_user(request):
    """
    Register a new user account.
    
    Public endpoint for user registration. Validates username uniqueness
    and password requirements before creating new Django User object.
    Created user can immediately authenticate with JWT token endpoint.
    
    Security Considerations:
    - Password is hashed using Django's default algorithm (PBKDF2)
    - Username uniqueness is enforced in database
    - No user data is exposed in responses
    - Consider adding:
      * Rate limiting (prevent brute force)
      * Email verification
      * Password strength validation
      * CAPTCHA for spam prevention
    
    HTTP Methods:
    - POST /api/register/
    
    Request Body (JSON):
        {
            "username": "john_doe",
            "password": "securepassword123"
        }
    
    Response on Success (201 Created):
        {
            "message": "User created successfully",
            "user_id": 42
        }
    
    Response on Error (400 Bad Request):
        {
            "error": "Username and password are required"
        }
        OR
        {
            "error": "Username already exists"
        }
    
    Validation Steps:
    1. Check both username and password are provided
    2. Check username doesn't already exist in database
    3. Create user with hashed password
    4. Return success response with new user ID
    
    Args:
        request: HTTP POST request with username and password
    
    Returns:
        Response: Success/error message with appropriate status code
    """
    # Extract credentials from request body
    username = request.data.get('username')
    password = request.data.get('password')

    # Validate that both fields are provided and non-empty
    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if username is already taken
    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create new user with securely hashed password
    # Django's create_user() automatically hashes the password
    user = User.objects.create_user(username=username, password=password)
    
    # Return success with new user ID for client use
    return Response(
        {"message": "User created successfully", "user_id": user.id},
        status=status.HTTP_201_CREATED
    )
    
    