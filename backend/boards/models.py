"""
Database models for collaborative board management.

This module defines the core data models for a Trello-like collaboration
board system with support for boards, lists, cards, and activity tracking.
"""

from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    Represents a collaborative board containing lists and cards.
    
    Attributes:
        name (str): The display name of the board (max 200 characters).
        owner (User): The user who created and owns this board.
    """
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class List(models.Model):
    """
    Represents a list within a board (e.g., 'To Do', 'In Progress', 'Done').
    
    Attributes:
        name (str): The display name of the list (max 200 characters).
        board (Board): The parent board this list belongs to.
    """
    name = models.CharField(max_length=200)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')

    def __str__(self):
        return self.name


class Card(models.Model):
    """
    Represents a task card within a list.
    
    Attributes:
        title (str): The card's title (max 200 characters).
        description (str): Detailed description of the card (optional).
        list (List): The list this card belongs to.
        position (int): The card's order within the list (0-indexed).
        assigned_to (User): The user assigned to this card (optional).
        created_at (datetime): Timestamp of card creation.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='cards')
    position = models.PositiveIntegerField(default=0)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['position']


class ActivityLog(models.Model):
    """
    Tracks user actions performed on a board for audit and notification purposes.
    
    Attributes:
        board (Board): The board where the activity occurred.
        user (User): The user who performed the action (optional if user deleted).
        action (str): Description of the action taken (max 200 characters).
        card (Card): The card involved in the action (optional if card deleted).
        created_at (datetime): Timestamp of the activity.
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action