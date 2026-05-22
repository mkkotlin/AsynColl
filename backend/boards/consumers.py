"""
WebSocket consumers for real-time board collaboration.

Handles WebSocket connections for live board updates using Django Channels,
allowing multiple clients to see changes in real-time without polling.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class BoardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time board updates.
    
    Manages WebSocket connections for a specific board, allowing multiple
    clients to receive live updates when any user makes changes to the board.
    
    Attributes:
        board_id: The ID of the board this connection is for.
        room_group_name: Channel group name for this board (format: board_<id>).
    """

    async def connect(self):
        """
        Handle new WebSocket connection.
        
        Extracts the board ID from the URL, creates a group channel for that board,
        and accepts the connection.
        """
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.room_group_name = f'board_{self.board_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, closed_code):
        """
        Handle WebSocket disconnection.
        
        Removes this connection from the board's channel group to stop receiving
        updates.
        
        Args:
            closed_code: The WebSocket close code (e.g., 1000 for normal closure).
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket message from client.
        
        Broadcasts the received message to all connected clients in this board's
        channel group, enabling real-time synchronization of updates.
        
        Args:
            text_data: JSON-formatted message data from the client.
        """
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'board_update',
                'message': data
            }
        )

    async def board_update(self, event):
        """
        Send a board update message to the client.
        
        Called by the channel layer when a message is broadcast to this channel group.
        Sends the update data to the connected WebSocket client.
        
        Args:
            event: Dictionary containing 'message' key with the update data.
        """
        await self.send(text_data=json.dumps(event['message']))