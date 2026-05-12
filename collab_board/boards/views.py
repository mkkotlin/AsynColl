from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, NotFound
from boards.models import Board, List, Card
from boards.serializers import CardSerializer, BoardSerializer, ListSerializer
from rest_framework.response import Response

# Create your views here.
# Board View
class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

# List View
class  ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    
    # List filter
    def get_queryset(self):
        queryset = super().get_queryset()
        board_id = self.request.query_params.get('board')

        # validation and response
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

# Card View
class  CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        list_id = self.request.query_params.get('list')
        board_id = self.request.query_params.get('board')

        # validation and response
        if list_id is not None:
            try:
                list_id = int(list_id)
            except ValueError:
                raise ValidationError({"list": "Id must be integer or number"})

            # If valid id not found
            if not List.objects.filter(id=list_id).exists():
                raise NotFound({"list":f"List id {list_id} does not exists"})
            
            queryset = queryset.filter(list_id=list_id)
        
        if board_id is not None:
            try:
                board_id = int(board_id)
            except ValueError:
                raise ValidationError({"board": "Id must be integer or number"})
            
            if not queryset.filter(list__board_id=board_id).exists():
                raise NotFound({"board":f"Board id {board_id} does not exists"})
            
            queryset = queryset.filter(list__board_id=board_id)
        return queryset.order_by('position')
    

    # move card between list
    # update method
    def update(self, request, *args, **kwargs):
        card = self.get_object()

        new_list = request.data.get('list')
        new_position = request.data.get('position')

        if new_list:
            card.list_id = new_list

        if new_position is not None:
            card.position = new_position

        card.save()

        serializer = self.get_serializer(card)
        return Response(serializer.data,)