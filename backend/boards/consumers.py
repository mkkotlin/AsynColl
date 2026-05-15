"""
WebSocket Consumer for Real-Time Board Synchronization
========================================================

This module implements asynchronous WebSocket handling using Django Channels.
WebSocket connections enable real-time synchronization of board updates across
multiple connected clients without continuous polling.

Architecture:
- Uses Django Channels' AsyncWebsocketConsumer for async WebSocket handling
- Groups clients by board_id to broadcast updates to board subscribers
- Maintains group subscriptions for automatic client management
- Handles connection lifecycle (connect, disconnect, receive)

Flow:
1. Client establishes WebSocket connection to /ws/board/<board_id>/
2. Consumer subscribes to board_<board_id> group
3. When one client makes changes (via REST API), activity logged
4. Changes broadcast to all connected clients in board_<board_id> group
5. Connected clients receive updates in real-time
6. Upon disconnect, consumer leaves group

Note on Data Flow:
- WebSocket is receive-only for board updates from other users
- Updates originate from REST API endpoints (views.py)
- ActivityLog records all changes
- Changes are broadcast via Django Channels group_send()
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class BoardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time board update synchronization.
    
    Handles WebSocket connections for a specific board, allowing multiple
    clients to receive real-time updates of changes made by other users.
    
    Connection URL Pattern:
        ws://localhost:8000/ws/board/<board_id>/
    
    Example:
        ws://localhost:8000/ws/board/5/  -> Subscribe to board 5 updates
    
    Client Communication Protocol:
    
    1. RECEIVING (from server to client - activity updates):
        Message Format (JSON):
        {
            "type": "board_update",
            "board_id": 5,
            "action": "card_moved",
            "card_id": 42,
            "message": {
                "type": "moved",
                "card_title": "Fix bug",
                "from_list": "To Do",
                "to_list": "In Progress",
                "user": "alice"
            }
        }
    
    2. SENDING (from client to server - currently not used):
        Client can optionally send messages that will be broadcast to all
        other connected clients in the same board group.
    
    Implementation Details:
    
    Group Management:
        - Each board has a group name: f'board_{board_id}'
        - Multiple WebSocket connections for same board join same group
        - Messages sent to group are delivered to all members
    
    Channel Layers:
        - In development: InMemoryChannelLayer (configured in settings.py)
        - In production: RedisChannelLayer (recommended for persistence)
        - Settings location: collab_board/settings.py CHANNEL_LAYERS config
    
    Lifecycle:
        1. connect(): Client WebSocket connects
           - Extract board_id from URL
           - Create group name: f'board_{board_id}'
           - Add consumer to group
           - Accept connection
        
        2. receive(): Client sends data (optional)
           - Parse JSON message
           - Broadcast to all group members
           - Used for real-time cursor positions, etc. (future feature)
        
        3. disconnect(): Client closes connection
           - Remove consumer from group
           - Automatic cleanup by framework
        
        4. board_update(): Server broadcasts update (internal method)
           - Called by group_send() when activity logged
           - Serializes and sends update to client
    
    Performance Considerations:
        - Each open WebSocket = one consumer instance
        - Groups are lightweight (just subscribes/unsubscribes)
        - Scales to thousands of concurrent connections (with Redis)
        - Broadcasts are sent asynchronously (doesn't block HTTP responses)
    
    Error Handling (Future Enhancement):
        Currently no error handling for:
        - JSON parsing errors
        - Group message send failures
        - Consider adding try-except blocks in receive() and board_update()
    
    Security (Current):
        - No authentication verification on WebSocket connection
        - Any client can connect to any board_id
        Recommendations for production:
        - Add JWT token verification in connect()
        - Check if user has board access permissions
        - Log suspicious connection attempts
    """

    async def connect(self):
        """
        Handle WebSocket connection and subscribe to board update group.
        
        Process:
        1. Extract board_id from URL parameters
        2. Create group name using board_id (e.g., 'board_5')
        3. Subscribe this consumer to the group
        4. Accept the WebSocket connection
        
        At this point, the client can receive messages sent to the group
        via the board_update() handler. Multiple clients connecting to the
        same board will all be in the same group.
        
        Group Mechanics:
            board_<id> group acts like a mailbox:
            - Multiple subscribers (consumers) read from it
            - Any subscriber can send messages to it
            - All subscribers receive those messages
        
        Example Flow:
            Client 1 connects to /ws/board/5/
            → Joins group 'board_5'
            
            Client 2 connects to /ws/board/5/
            → Also joins group 'board_5'
            
            Server logs activity: card moved
            → Sends to group 'board_5'
            
            Both clients receive the update instantly
        
        Raises:
            No explicit error handling; errors would terminate connection
        """
        # Extract board_id from WebSocket URL parameters
        # URL pattern: /ws/board/<int:board_id>/
        # scope['url_route']['kwargs'] contains URL parameters
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        
        # Create group name for this board
        # Format: 'board_<board_id>' (e.g., 'board_5' for board 5)
        self.room_group_name = f'board_{self.board_id}'

        # Subscribe this consumer to the board's group
        # Now when messages are sent to this group, this consumer receives them
        await self.channel_layer.group_add(
            self.room_group_name,        # Which group to join
            self.channel_name            # Which consumer (this one)
        )

        # Accept the WebSocket connection from the client
        # After this, client can send and receive messages
        await self.accept()

    async def disconnect(self, closed_code):
        """
        Handle WebSocket disconnection and remove from group.
        
        Process:
        1. Unsubscribe consumer from board group
        2. Allow garbage collection of consumer instance
        3. Framework handles cleanup
        
        Unsubscribe from Group:
            This ensures we stop receiving group messages when connection closes.
            Necessary for memory management (many connections/disconnections).
        
        closed_code Values:
            1000: Normal closure - client closed connection
            1001: Going away - client navigated away
            1002: Protocol error - invalid data
            1003: Unsupported data
            4000+: Custom codes (app-defined)
        
        Use Cases:
            - Client closes browser tab
            - Client loses network connection
            - Server shuts down connection (timeout, etc.)
            - Client sends close frame
        
        Args:
            closed_code: WebSocket close code (int)
                Reference: https://tools.ietf.org/html/rfc6455#section-7.4.1
        """
        # Unsubscribe from the board's group
        # Prevents memory leaks and wasted broadcasts to disconnected clients
        await self.channel_layer.group_discard(
            self.room_group_name,       # Which group to leave
            self.channel_name           # Which consumer (this one)
        )

    async def receive(self, text_data):
        """
        Receive data from WebSocket and broadcast to group.
        
        This method handles incoming messages from connected clients.
        When a client sends data through the WebSocket, it's broadcast
        to all other connected clients in the same board group.
        
        Current Use Cases:
        - Broadcasting real-time updates (future feature)
        - Client-to-client messages (future feature)
        - Cursor positions (future feature)
        
        Process:
        1. Parse incoming JSON message from client
        2. Create group message envelope with type 'board_update'
        3. Send to all group members
        4. All consumers receive via board_update() handler
        
        Message Format (from client):
            {
                "action": "card_moved",
                "card_id": 42,
                "from_list": 5,
                "to_list": 6
            }
        
        Args:
            text_data: Raw string data from WebSocket
                Should be valid JSON
                Raises exception if invalid (not caught here)
        
        Future Enhancements:
            - Add error handling for invalid JSON
            - Validate message schema before broadcast
            - Add rate limiting to prevent spam
            - Implement message signing for security
        """
        # Parse incoming JSON data from client
        # Raises JSONDecodeError if not valid JSON (not currently caught)
        data = json.loads(text_data)

        # Send message to all consumers in the group
        # The 'type' determines which handler receives it
        await self.channel_layer.group_send(
            self.room_group_name,       # Send to which group
            {
                'type': 'board_update',  # Route to board_update() handler
                'message': data          # Pass original message data
            }
        )

    async def board_update(self, event):
        """
        Send board update message to connected WebSocket client.
        
        This is an internal handler called by group_send() when a message
        with type='board_update' is sent to the group. It serializes and
        sends the message to the connected client.
        
        Flow:
        1. view.py creates activity (card moved, assigned, etc.)
        2. Signal/hook sends message to board_<id> group
        3. Group delivers to all subscribed consumers
        4. This handler receives it
        5. Send to client via self.send()
        6. Client receives update and updates UI
        
        Event Structure:
            {
                'type': 'board_update',        # Handler name
                'message': {...}               # Data to send
            }
        
        Args:
            event: Dictionary from group_send() containing 'type' and 'message'
                'type': Always 'board_update' (determines which handler)
                'message': JSON-serializable data to send to client
        
        Example:
            # From views.py after creating ActivityLog:
            await channel_layer.group_send(
                'board_5',
                {
                    'type': 'board_update',
                    'message': {
                        'action': 'card_moved',
                        'card_id': 42,
                        'user': 'alice'
                    }
                }
            )
            
            # Triggers board_update() handler which sends to client:
            # {"action": "card_moved", "card_id": 42, "user": "alice"}
        
        Note: message is already serializable (comes from client or API)
        """
        # Extract message from event
        message = event['message']

        # Send JSON message to the connected WebSocket client
        # json.dumps() converts Python dict to JSON string
        await self.send(text_data=json.dumps(message))