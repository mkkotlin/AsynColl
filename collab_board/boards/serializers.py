from rest_framework import serializers
from boards.models import Board, List, Card


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'  

class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = '__all__'  

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'  