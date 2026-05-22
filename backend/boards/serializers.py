"""
Serializers for converting board app models to/from JSON.

This module provides DRF serializers for API endpoints, handling serialization
of boards, lists, cards, activity logs, and users with proper nested relationships.
"""

from rest_framework import serializers
from boards.models import Board, List, Card, ActivityLog
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes User model with essential fields only.
    
    Used for read-only user representations in nested relationships.
    Fields:
        id: Unique user identifier.
        username: Unique username for login.
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class CardSerializer(serializers.ModelSerializer):
    """
    Serializes Card model with nested user assignment information.
    
    Provides both read-only user object for GET requests and write access
    to assigned_to via ID in PATCH/PUT requests.
    
    Fields:
        assigned_to: Read-only nested UserSerializer for GET requests.
        assigned_to_id: Write-only field for updating card assignment.
        Other card fields included via '__all__'.
    """
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Card
        fields = '__all__'


class ListSerializer(serializers.ModelSerializer):
    """
    Serializes List model with nested cards information.
    
    Includes all cards in the list for GET requests to support
    displaying complete board structure in a single API call.
    
    Fields:
        cards: Read-only nested CardSerializer for all list cards.
        Other list fields included via '__all__'.
    """
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = '__all__'


class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Serializes ActivityLog model with nested user information.
    
    Provides user details for each logged activity for audit trails
    and user notifications.
    
    Fields:
        user: Read-only nested UserSerializer for the activity performer.
        Other activity log fields included via '__all__'.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = '__all__'


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializes Board model with complete nested structure.
    
    Provides the full board structure including all lists and their cards,
    plus activity history for comprehensive board representation.
    
    Fields:
        lists: Read-only nested ListSerializer for all board lists.
        activities: Read-only nested ActivityLogSerializer for board activity history.
        Other board fields included via '__all__'.
    """
    lists = ListSerializer(many=True, read_only=True)
    activities = ActivityLogSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = '__all__'
