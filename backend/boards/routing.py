"""
WebSocket URL routing configuration.

Defines URL patterns for WebSocket connections using Django Channels,
enabling real-time communication for collaborative board features.
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/board/<int:board_id>/', consumers.BoardConsumer.as_asgi()),
]