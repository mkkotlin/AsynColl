from django.shortcuts import render
from rest_framework import viewsets
from boards.models import Board, List, Card
from boards.serializers import CardSerializer, BoardSerializer, ListSerializer

# Create your views here.
class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

class  ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer

class  CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer