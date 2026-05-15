"""
Django REST Framework Serializers for Board API
================================================

Serializers handle the conversion between Python objects and JSON representations.
They also validate incoming data and handle nested relationships efficiently.

Architecture:
- UserSerializer: Basic user profile info
- CardSerializer: Individual task with assigned user details
- ListSerializer: List with nested cards (read-only cards)
- ActivityLogSerializer: Action log with user information
- BoardSerializer: Complete board with nested lists, cards, and activity

Serialization Strategy:
- Read-only fields use nested serializers for complete data
- Write-only fields use PrimaryKeyRelatedField for clean API contracts
- Nested relationships use many=True for collections
"""

from rest_framework import serializers
from boards.models import Board, List, Card, ActivityLog
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - exposes id and username.
    
    This minimal serializer is used for:
    - Displaying who is assigned to a card
    - Showing who performed an activity
    - Populating user dropdowns in frontend
    
    Fields:
        id: Django User ID (read-only)
            Used as foreign key reference when assigning cards
        
        username: Login name/display name
            Human-readable identifier for the user
    
    Usage:
        1. As nested read-only in CardSerializer for assigned_to field
        2. As nested read-only in ActivityLogSerializer for user field
        3. Standalone endpoint for fetching list of team members
    
    Note: Intentionally excludes:
        - password (security - never expose hashed password)
        - email (privacy)
        - first_name, last_name (optional, not used in this app)
        - is_staff, is_superuser (admin-only info)
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class CardSerializer(serializers.ModelSerializer):
    """
    Serializer for Card model with dual representation of assigned user.
    
    This serializer demonstrates a common pattern:
    - Read-only nested serializer (assigned_to) for API responses
    - Write-only PrimaryKeyRelatedField (assigned_to_id) for updates
    
    This dual representation provides:
    - Complete user info when fetching cards (good UX)
    - Simple integer IDs when updating assignments (clean API)
    
    Read-Only Fields (API Response):
        assigned_to: Nested UserSerializer with full user details
            Example: {"id": 3, "username": "alice"}
            Displayed in GET responses for frontend convenience
    
    Write-Only Fields (API Request):
        assigned_to_id: Integer user ID for assignment
            Example: {"assigned_to_id": 3}
            Accepted in PATCH/PUT requests for clean client code
    
    Included Fields:
        - id: Card ID (read-only, auto-generated)
        - title: Card title/name (max 200 chars)
        - description: Detailed card content (optional)
        - list: ID of parent list (required)
        - position: Sort order within list (default 0)
        - assigned_to: Nested user object (read-only)
        - assigned_to_id: User ID for updates (write-only)
        - created_at: Creation timestamp (read-only, auto-set)
    
    Response Format (GET):
        {
            "id": 42,
            "title": "Fix login bug",
            "description": "Users report 500 error on login",
            "list": 5,
            "position": 0,
            "assigned_to": {"id": 3, "username": "alice"},
            "created_at": "2026-05-15T10:00:00Z"
        }
    
    Update Format (PATCH):
        {
            "assigned_to_id": 3,
            "list": 5,
            "position": 1
        }
    """
    # Read-only nested serializer for responses
    assigned_to = UserSerializer(read_only=True)
    
    # Write-only PrimaryKeyRelatedField for updates
    # Maps incoming ID to the actual User object via 'source' parameter
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),  # Validates that user_id exists
        source='assigned_to',          # Maps to the assigned_to field
        write_only=True,               # Only used for input, not in responses
        required=False,                # Optional field
        allow_null=True                # Can explicitly set to null
    )

    class Meta:
        model = Card
        fields = '__all__'


class ListSerializer(serializers.ModelSerializer):
    """
    Serializer for List model with nested cards.
    
    Lists are displayed with all their cards in a single API response.
    This reduces frontend API calls (one request gets list + all cards).
    
    Nested Relationships:
        cards: Array of CardSerializer objects (read-only)
            Populated automatically by DRF from related_name='cards'
            Displays complete card info (users, positions, etc.)
    
    Benefits of Nested Serialization:
        - Single API call returns complete board view
        - Frontend receives data in expected hierarchy
        - Reduces number of HTTP requests
    
    Included Fields:
        - id: List ID (read-only, auto-generated)
        - name: List name/title (max 200 chars)
        - board: Parent board ID
        - cards: Array of CardSerializer objects (read-only, nested)
    
    Response Format (GET):
        {
            "id": 5,
            "name": "In Progress",
            "board": 1,
            "cards": [
                {
                    "id": 42,
                    "title": "Fix login bug",
                    "description": "...",
                    "list": 5,
                    "position": 0,
                    "assigned_to": {"id": 3, "username": "alice"},
                    "created_at": "2026-05-15T10:00:00Z"
                },
                {
                    "id": 43,
                    "title": "Design homepage",
                    ...
                }
            ]
        }
    
    Note: Cards are read-only because:
    - Create/update cards through dedicated /api/cards/ endpoints
    - Prevents accidental data inconsistency
    - Each card has its own validation and business logic
    """
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = '__all__'


class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ActivityLog model with user information.
    
    Activity logs provide audit trail and activity feeds. Each log entry
    includes who performed the action and what was changed. These are
    typically displayed in chronological order (newest first).
    
    Nested Relationships:
        user: UserSerializer for who performed the action
            Shows username and ID of the person who acted
            Can be null if action was system-triggered
    
    Use Cases:
        1. Activity Feed: "Recent activity on this board"
            Display last 20 logs with usernames and timestamps
        
        2. Card History: "What happened to this task?"
            Filter logs by card_id to show full change history
        
        3. WebSocket Broadcasts: Real-time updates for connected clients
            Send logs to update other users' views
        
        4. Audit Reports: "What changed and when?"
            Generate compliance reports from logs
    
    Included Fields:
        - id: Log ID (read-only)
        - board: Board ID (which board this action affected)
        - user: Nested UserSerializer (who performed action)
        - action: Description of what happened (max 200 chars)
        - card: Card ID if action was card-related (optional)
        - created_at: When action occurred (read-only, auto-set)
    
    Response Format (GET):
        {
            "id": 101,
            "board": 5,
            "user": {"id": 3, "username": "alice"},
            "action": "moved 'Fix login bug' to list 'Done'",
            "card": 42,
            "created_at": "2026-05-15T14:30:00Z"
        }
    
    Activity Feed Format (paginated):
        [
            {
                "id": 103,
                "action": "assigned 'Design homepage'",
                "user": {"username": "bob"},
                "created_at": "2026-05-15T15:20:00Z"
            },
            {
                "id": 102,
                "action": "moved 'Fix login bug' to list 'Done'",
                "user": {"username": "alice"},
                "created_at": "2026-05-15T14:30:00Z"
            }
        ]
    """
    # Nested read-only serializer for user information
    user = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = '__all__'


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer for Board model with complete nested hierarchy.
    
    This is the main serializer returned by the API for board data. It
    includes all nested lists and cards, providing a complete view of the
    board's structure in a single API response.
    
    Nested Relationships:
        lists: Array of ListSerializer objects (read-only, nested)
            Each list includes its nested cards
            Maintains board structure hierarchy
        
        activities: Array of ActivityLogSerializer objects (read-only)
            Shows all actions performed on this board
            Useful for activity feed/audit trail
    
    API Response Benefits:
        - Single API call gets entire board + lists + cards
        - Frontend receives data in expected hierarchy
        - Includes recent activity for real-time awareness
        - Reduces number of HTTP requests from N to 1
    
    Included Fields:
        - id: Board ID (read-only)
        - name: Board name/title (max 200 chars)
        - owner: User ID who created/owns board
        - lists: Array of ListSerializer objects (read-only, nested)
        - activities: Array of ActivityLogSerializer objects (read-only)
    
    Response Format (GET /api/boards/1/):
        {
            "id": 1,
            "name": "Website Redesign",
            "owner": 2,
            "lists": [
                {
                    "id": 5,
                    "name": "To Do",
                    "board": 1,
                    "cards": [
                        {
                            "id": 42,
                            "title": "Design homepage",
                            "list": 5,
                            "assigned_to": {"id": 3, "username": "alice"},
                            ...
                        }
                    ]
                },
                {
                    "id": 6,
                    "name": "In Progress",
                    "board": 1,
                    "cards": [...]
                }
            ],
            "activities": [
                {
                    "id": 103,
                    "action": "moved 'Design homepage' to list 'In Progress'",
                    "user": {"id": 3, "username": "alice"},
                    "created_at": "2026-05-15T15:20:00Z"
                }
            ]
        }
    
    Performance Note:
        - Uses prefetch_related() in views to optimize queries
        - Prevents N+1 query problem despite deep nesting
        - Efficiently fetches all related data in ~3 total DB queries
    
    Note: Nested fields are read-only because:
    - Create/update through dedicated endpoints (/api/lists/, /api/cards/)
    - Prevents accidental data inconsistency
    - Each entity has own validation logic
    """
    # Nested read-only serializers for hierarchical response
    lists = ListSerializer(many=True, read_only=True)
    activities = ActivityLogSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = '__all__'
