"""
Django Admin Interface Configuration
=====================================

This module registers models with Django's admin interface and customizes
how they appear. The admin interface provides a simple way for administrators
and staff to manage data without writing custom CRUD views.

Features:
- Display relevant fields in list view for quick scanning
- Searchable and filterable data
- Inline editing capabilities
- Export capabilities (built-in)

Access:
- URL: /admin/
- Login: Django superuser credentials
- Permissions: Django User/Group system controls access
"""

from django.contrib import admin
from boards.models import Board, List, Card, ActivityLog


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Board model.
    
    Displays:
    - id: Unique board identifier (auto-generated)
    - name: Board name/title for quick identification
    - owner: User who created/owns the board
    
    Usage in Admin:
    1. View all boards with their owners in list view
    2. Click board to edit metadata (name, owner)
    3. See related lists and cards in related objects section
    4. Delete boards (cascades to all lists and cards)
    
    List View Display:
    ID  | Name                    | Owner
    ----|-------------------------|----------
    1   | Website Redesign        | admin
    2   | Q1 Goals                | john
    3   | Customer Feedback       | alice
    
    Potential Enhancements:
    - Add search_fields = ['name', 'owner__username']
    - Add list_filter = ['owner', 'created_at'] (need to add created_at field)
    - Add readonly_fields = ['id']
    - Add inlines = [ListInline] to edit lists in board view
    - Add actions for bulk operations
    """
    list_display = ('id', 'name', 'owner')


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for List model.
    
    Displays:
    - id: Unique list identifier (auto-generated)
    - name: List name (e.g., "To Do", "In Progress")
    - board: Which board contains this list
    
    Usage in Admin:
    1. View all lists across all boards
    2. Click to edit list metadata (name, board)
    3. See related cards in related objects section
    4. Reorganize lists (move to different board if needed)
    
    List View Display:
    ID  | Name            | Board
    ----|-----------------|--------------------
    1   | To Do           | Website Redesign
    2   | In Progress     | Website Redesign
    3   | Done            | Website Redesign
    4   | Backlog         | Q1 Goals
    
    Potential Enhancements:
    - Add search_fields = ['name', 'board__name']
    - Add list_filter = ['board']
    - Add inlines = [CardInline] for mass card editing
    - Add ordering = ['board', 'id']
    - Add custom actions: "Move all cards to another list"
    """
    list_display = ('id', 'name', 'board')


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Card model.
    
    Displays:
    - id: Unique card identifier (auto-generated)
    - title: Card name/title
    - list: Which list contains this card
    - position: Sort order within list (for drag-and-drop)
    - assigned_to: User assigned to card (if any)
    - created_at: When card was created
    
    Usage in Admin:
    1. View all cards with their status and assignments
    2. Bulk edit assignments or status
    3. Monitor created_at to see velocity
    4. Filter by assigned user or list
    
    List View Display:
    ID  | Title               | List        | Pos | Assigned To | Created
    ----|---------------------|-------------|-----|-------------|------------------
    1   | Design homepage     | To Do       | 0   | alice       | 2026-05-15 10:00
    2   | Fix login bug       | In Progress | 0   | bob         | 2026-05-14 14:30
    3   | Deploy API          | Done        | 1   | charlie     | 2026-05-10 09:15
    
    Potential Enhancements:
    - Add search_fields = ['title', 'description', 'assigned_to__username']
    - Add list_filter = ['list', 'assigned_to', 'created_at']
    - Add readonly_fields = ['id', 'created_at', 'position']
    - Add date_hierarchy = 'created_at'
    - Add fieldsets for better organization
    - Add custom actions: "Bulk assign to user", "Bulk move to list"
    - Add autocomplete_fields = ['assigned_to', 'list']
    """
    list_display = ('id', 'title', 'list', 'position', 'assigned_to', 'created_at')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for ActivityLog model.
    
    Displays:
    - board: Which board the action happened on
    - user: Who performed the action
    - action: What happened (free-form description)
    - card: Which card was affected (if applicable)
    - created_at: When action occurred
    
    Usage in Admin:
    1. View audit trail of all board changes
    2. Monitor user activity
    3. Find who moved a card when
    4. Generate compliance/audit reports
    
    List View Display:
    Board           | User   | Action                           | Card  | Time
    --------|--------|------------|------|-----|-------|--------|-------------|
    Website Redesign | alice  | moved 'Design' to 'In Progress'  | 1     | 2026-05-15 15:20
    Website Redesign | bob    | assigned 'Fix login bug'         | 2     | 2026-05-15 14:30
    Q1 Goals         | charlie| moved 'Q4 Review' to 'Done'     | 5     | 2026-05-15 13:00
    
    Activity Log Uses:
    - Audit Trail: Track all changes for compliance
    - Real-time Activity Feed: Show on dashboard
    - Change History: "What happened to this card?"
    - User Analytics: "Who is most active?"
    - Debugging: "What went wrong and when?"
    
    Potential Enhancements:
    - Add search_fields = ['action', 'user__username', 'card__title']
    - Add list_filter = ['board', 'user', 'created_at']
    - Add readonly_fields = ['id', 'created_at'] (logs shouldn't be edited)
    - Add date_hierarchy = 'created_at'
    - Add ordering = ['-created_at'] (newest first)
    - Add custom actions: "Export activity report as CSV"
    - Add permissions: readonly for staff, full access for superusers
    - Add change_list_template for custom filtering UI
    
    Security Note:
    - Activity logs should be immutable (no editing)
    - Only admins should have access
    - Consider archiving old logs to maintain performance
    - Sensitive actions (like password resets) shouldn't be logged
    """
    list_display = ('board', 'user', 'action', 'card', 'created_at')
