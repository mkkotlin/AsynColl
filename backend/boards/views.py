from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Board, List, Card
from .serializers import BoardSerializer, ListSerializer, CardSerializer, UserSerializer
from django.contrib.auth.models import User


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.prefetch_related('lists__cards')


class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer

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

    def partial_update(self, request, *args, **kwargs):
        card = self.get_object()

        # existing field
        new_list = request.data.get('list')
        new_position = request.data.get('position')

        # new field
        assigned_user = request.data.get('assigned_to_id')

        if new_list:
            card.list_id = new_list

        if new_position is not None:
            card.position = new_position

        if assigned_user is not None:
            card.assigned_to_id = assigned_user

        card.save()

        serializer = self.get_serializer(card)
        return Response(serializer.data, status=status.HTTP_200_OK)