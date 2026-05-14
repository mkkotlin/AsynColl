from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Board, List, Card
from .serializers import BoardSerializer, ListSerializer, CardSerializer


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