from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Board, List, Card, ActivityLog
from .serializers import BoardSerializer, ListSerializer, CardSerializer, UserSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view



class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Board.objects.prefetch_related('lists__cards', 'activities')


class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = [IsAuthenticated]

    # 🔥 REORDER API
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        card_ids = request.data.get('card_ids', [])

        for index, card_id in enumerate(card_ids):
            Card.objects.filter(id=card_id).update(position=index)

        return Response({"status": "reordered"}, status=status.HTTP_200_OK)


class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]


    def partial_update(self, request, *args, **kwargs):
        card = self.get_object()

        user = request.user if request.user.is_authenticated else None

        old_list = card.list
        old_assigned = card.assigned_to

        new_list = request.data.get('list')
        new_assigned = request.data.get('assigned_to_id')

        # Apply updates
        if new_list:
            card.list_id = new_list

        if new_assigned is not None:
            card.assigned_to_id = new_assigned

        card.save()

        # 🔥 Create activity log
        if new_list:
            ActivityLog.objects.create(
                board=card.list.board,
                user=user,
                action=f" moved '{card.title}' to list {card.list.name}",
                card=card
            )

        if new_assigned is not None:
            ActivityLog.objects.create(
                board=card.list.board,
                user=user,
                action=f" assigned '{card.title}'",
                card=card
            )

        serializer = self.get_serializer(card)
        return Response(serializer.data)
    
@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if User.objects.filter(username=username).exists():
        return Response({"error": "Usermame already exists"},status = status.HTTP_400_BAB_REQUEST )
    
    user = User.objects.create_user(username=username, password=password)
    return Response({"message":"User created successfully"})
    
    