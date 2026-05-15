from django.contrib import admin
from boards.models import Board, List, Card, ActivityLog

# Register your models here.
# display card, list, board and its id and title
# admin.site.register(Board)
# admin.site.register(List)
# admin.site.register(Card)   

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner')

@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'board')

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'list', 'position', 'assigned_to', 'created_at')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('board', 'user', 'action', 'card', 'created_at')
