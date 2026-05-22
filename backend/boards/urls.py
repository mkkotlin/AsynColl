"""
REST API URL routing configuration.

Defines URL patterns for board, list, card, and user endpoints using
Django REST Framework's DefaultRouter for automatic CRUD endpoint generation.
"""

from rest_framework.routers import DefaultRouter
from boards.views import BoardViewSet, CardViewSet, ListViewSet, UserViewSet, register_user
from django.urls import path

router = DefaultRouter()
router.register(r'boards', BoardViewSet)
router.register(r'lists', ListViewSet)
router.register(r'cards', CardViewSet)
router.register(r'users', UserViewSet)

urlpatterns = router.urls + [
    path('register/', register_user)
]