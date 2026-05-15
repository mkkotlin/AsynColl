"""
WebSocket Routing Configuration for Django Channels
====================================================

This module configures WebSocket URL patterns for real-time communication.
When a client connects to a WebSocket URL, the request is routed to the
appropriate consumer based on the URL pattern.

WebSocket URLs vs HTTP URLs:
- HTTP: /api/boards/1/          -> Handled by REST view
- WS:   /ws/board/1/            -> Handled by WebSocket consumer

Consumers in this module:
- BoardConsumer: Real-time board updates for synchronized state
"""

from django.urls import path
from . import consumers

# WebSocket URL patterns
# Format: path('<route>', <consumer>.as_asgi())
# The as_asgi() converts ASGI-compatible consumer to ASGI application

websocket_urlpatterns = [
    # WebSocket endpoint for board updates
    # URL: ws://host:port/ws/board/<board_id>/
    # Example: ws://localhost:8000/ws/board/5/
    # 
    # Parameters:
    # - <int:board_id>: Board ID (integer constraint)
    # 
    # Routing:
    # - Client connects: BoardConsumer.connect() called
    # - Client sends data: BoardConsumer.receive() called
    # - Client disconnects: BoardConsumer.disconnect() called
    # - Server broadcasts: BoardConsumer.board_update() called
    # 
    # Usage in Frontend (JavaScript):
    # ```javascript
    # const boardId = 5;
    # const boardWs = new WebSocket(`ws://${host}/ws/board/${boardId}/`);
    # 
    # boardWs.onmessage = (event) => {
    #     const data = JSON.parse(event.data);
    #     console.log("Board update:", data);
    #     updateBoardUI(data);
    # };
    # ```
    path('ws/board/<int:board_id>/', consumers.BoardConsumer.as_asgi()),
]