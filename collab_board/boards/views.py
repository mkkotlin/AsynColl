from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, NotFound
from boards.models import Board, List, Card
from boards.serializers import CardSerializer, BoardSerializer, ListSerializer

# Create your views here.
class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

class  ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        board_id = self.request.query_params.get('board')

        if board_id is not None:
            try:
                board_id = int(board_id)
            except ValueError:
                raise ValidationError({"board": "Board must be integer or number"})
            
            # If valid id not found
            if not Board.objects.filter(id=board_id).exists():
                raise NotFound({"board": f"Board id: {board_id} does not exists"})
                
            queryset = queryset.filter(board_id=board_id)
        return queryset.order_by('id')

class  CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        list_id = self.request.query_params.get('list')
        board_id = self.request.query_params.get('board')

        if list_id is not None:
            try:
                list_id = int(list_id)
            except ValueError:
                raise NotFound({"list": "Invalid list id"})
            queryset = queryset.filter(list_id=list_id)
        
        if board_id is not None:
            try:
                board_id = int(board_id)
            except ValueError:
                raise NotFound({"board": "Invalid board id"})
            queryset = queryset.filter(list__board_id=board_id)
        return queryset.order_by('position')