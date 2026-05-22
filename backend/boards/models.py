"""
Database Models for Collaborative Board Application
=====================================================

This module defines the core data models for the collaborative board system.
The application uses a hierarchical structure: Board > List > Card

Model Hierarchy:
    Board (top-level container)
        ├── List (columns/sections)
        │   └── Card (individual tasks)
        └── ActivityLog (audit trail)

Key Design Decisions:
- CASCADE deletes maintain referential integrity (delete board -> delete all lists/cards)
- Position field enables custom ordering without relying on database constraints
- ActivityLog provides audit trail for compliance and real-time sync
- Foreign keys use related_name for efficient reverse queries in ORM
"""

from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    Represents a collaborative board container.
    
    A board is the top-level organizational unit. Each board:
    - Belongs to a single owner (User)
    - Contains multiple Lists
    - Tracks all activities (moves, assignments, etc.)
    - Serves as a workspace for team collaboration
    
    Real-world Example:
        A "Website Redesign" project would be a Board containing:
        - Lists: "To Do", "In Progress", "Review", "Done"
        - Cards: Individual tasks like "Design homepage", "Code CSS", etc.
    
    Fields:
        name (CharField): Human-readable board name (max 200 chars)
            Examples: "Q1 Goals", "Bug Fixes", "Customer Feedback"
        owner (ForeignKey): Django User who created/owns this board
            - One owner per board
            - Deleting owner cascades to delete board
    
    Relationships:
        - OneToMany with List (via related_name='lists')
        - OneToMany with ActivityLog (via related_name='activities')
    
    Cascade Behavior:
        - If board is deleted: all Lists and Cards are deleted
        - If owner (User) is deleted: board is deleted
    """
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        """String representation for admin interface and debugging."""
        return self.name


class List(models.Model):
    """
    Represents a list (column) within a board.
    
    Lists are the primary organizational containers within a board.
    They typically represent workflow stages or categories. Each list
    contains Cards that users interact with daily.
    
    Common List Types (by use case):
        Kanban Board:     "To Do" -> "In Progress" -> "Done"
        Bug Tracker:      "New" -> "Assigned" -> "Fixed" -> "Closed"
        Content Mgmt:     "Draft" -> "Review" -> "Scheduled" -> "Published"
        Sales Pipeline:   "Lead" -> "Contacted" -> "Proposal" -> "Closed"
    
    Fields:
        name (CharField): Display name for the list (max 200 chars)
            Examples: "To Do", "In Progress", "High Priority", "Backlog"
        board (ForeignKey): Parent board that contains this list
            - Each list belongs to exactly one board
            - Deleting board cascades to delete this list
    
    Relationships:
        - ManyToOne with Board
        - OneToMany with Card (via related_name='cards')
    
    Notes:
        - Lists don't have position field; order determined by ID or custom ordering
        - Consider adding 'position' field if list reordering becomes needed
        - Cards within list are ordered by their 'position' field
    
    Cascade Behavior:
        - If parent board is deleted: this list is deleted
        - If this list is deleted: all contained Cards are deleted
    """
    name = models.CharField(max_length=200)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')

    def __str__(self):
        """String representation for admin interface and debugging."""
        return self.name


class Card(models.Model):
    """
    Represents an individual card (task/item) within a list.
    
    Cards are the atomic unit of work in the system. Each card represents
    a single task that can be assigned, moved, and tracked. Cards can be
    dragged between lists and assigned to team members.
    
    Features:
        - Drag-and-drop positioning within lists
        - User assignment and tracking
        - Description for detailed task information
        - Automatic creation timestamp
        - Sortable by position for consistent ordering
    
    Fields:
        title (CharField): Card name/title (max 200 chars)
            Must be concise and descriptive
            Examples: "Implement login", "Fix database query", "Review PR"
        
        description (TextField): Detailed description (optional)
            Can contain task details, requirements, or notes
            Supports markdown or plain text
        
        list (ForeignKey): Parent list containing this card
            - Each card belongs to exactly one list
            - Cards move between lists via list_id update
            - Deleting list cascades to delete card
        
        position (PositiveIntegerField): Sort order within list
            - 0-indexed (first card has position=0)
            - Updated by ListViewSet.reorder() action
            - Used for drag-and-drop functionality
            - Default=0 for new cards (usually placed at end)
        
        assigned_to (ForeignKey): User assigned to this card (optional)
            - Can be null/blank for unassigned cards
            - SET_NULL behavior: card stays if assigned user is deleted
            - Useful for workload management and notifications
        
        created_at (DateTimeField): Automatic timestamp of creation
            - Set automatically on card creation
            - Used for sorting recent activity
            - Immutable (doesn't update on edits)
    
    Relationships:
        - ManyToOne with List (contains Cards)
        - ManyToOne with User (assigned_to)
        - OneToMany with ActivityLog (tracked changes)
    
    Ordering:
        - Default Meta.ordering = ['position']
        - Ensures consistent card order in API responses
        - Respects user's drag-and-drop reordering
    
    Cascade Behavior:
        - If parent list is deleted: this card is deleted
        - If assigned user is deleted: card stays (assigned_to becomes NULL)
        - Deleting card cascades to delete related ActivityLog entries
    
    Example Workflow:
        1. Card created: title="Fix login bug", position=0
        2. Card assigned: assigned_to=User(john), logged in ActivityLog
        3. Card moved: list_id=2, position updated, logged in ActivityLog
        4. Card completed: description updated with solution notes
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='cards')
    position = models.PositiveIntegerField(default=0)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation for admin interface and debugging."""
        return self.title

    class Meta:
        """
        Model metadata and configuration.
        
        ordering = ['position']: Ensures cards are always returned in
                                 their intended position order from the API
        """
        ordering = ['position']


class ActivityLog(models.Model):
    """
    Audit trail for all significant actions on a board.
    
    ActivityLog records track every important change (moves, assignments, etc.)
    for audit purposes, real-time sync, and activity history display. This
    enables features like:
    - "Recent Activity" feed shown to team members
    - WebSocket broadcasts for real-time updates
    - Audit trail for compliance requirements
    - Undo/rollback capabilities (future feature)
    
    Current Logged Actions:
        - Card moved: "moved 'Task Name' to list List Name"
        - Card assigned: "assigned 'Task Name'"
    
    Potential Future Actions to Log:
        - Card created: "created card 'Task Name'"
        - Card deleted: "deleted card 'Task Name'"
        - Card description updated
        - Card reassignment with previous assignee info
        - List/Board created or deleted
    
    Fields:
        board (ForeignKey): Board where action occurred
            - Links log to specific board context
            - Used to broadcast updates to board subscribers
            - Deleting board cascades to delete logs
        
        user (ForeignKey): User who performed the action
            - Can be NULL if action triggered by system/automation
            - Useful for accountability and notifications
            - SET_NULL behavior: log stays if user deleted
        
        action (CharField): Human-readable description (max 200 chars)
            Should be in past tense with clear subject/object
            Examples:
                - "moved 'Bugfix' to list 'Done'"
                - "assigned 'Feature X' to john"
                - "created 'Design mockup'"
        
        card (ForeignKey): Related card (optional, null for board-level actions)
            - Points to the card affected by this action
            - NULL for actions not tied to specific card
            - Enables filtering/searching actions by card
            - Cascade deletes card log entries if card deleted
        
        created_at (DateTimeField): Timestamp of action
            - Auto-set on creation
            - Used for chronological sorting
            - Immutable (never updated)
    
    Relationships:
        - ManyToOne with Board (board-level audit trail)
        - ManyToOne with User (who performed action)
        - ManyToOne with Card (what was affected)
    
    Use Cases:
        1. Activity Feed: Show last 10 logs for board overview
        2. Real-time Sync: Query recent logs to update connected clients
        3. Audit Report: Generate compliance reports of board changes
        4. Notifications: Alert team members of important actions
        5. Change History: Show all changes to specific card
    
    Example Log Entries:
        {
            "board_id": 5,
            "user_id": 2,
            "action": "moved 'Deploy API' to list 'In Progress'",
            "card_id": 42,
            "created_at": "2026-05-15T15:20:44Z"
        }
    
    Cascade Behavior:
        - If board is deleted: all its logs are deleted
        - If user is deleted: logs remain with user=NULL
        - If card is deleted: logs pointing to it are deleted
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """String representation for admin interface and debugging."""
        return self.action