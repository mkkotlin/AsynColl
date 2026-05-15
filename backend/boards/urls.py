"""
REST API URL Router Configuration
==================================

This module configures REST API endpoints using Django REST Framework's
DefaultRouter, which automatically generates URLs for all ViewSet actions
(list, create, retrieve, update, partial_update, destroy).

Router Benefits:
- Automatic CRUD endpoint generation
- Standard naming conventions
- Automatic OPTIONS for CORS preflight
- Consistent URL structure

Registered ViewSets and Generated Endpoints:
1. BoardViewSet ('boards') -> /api/boards/
   - GET /api/boards/              -> List all boards
   - POST /api/boards/             -> Create board
   - GET /api/boards/<id>/         -> Retrieve board
   - PATCH /api/boards/<id>/       -> Partial update
   - PUT /api/boards/<id>/         -> Full update
   - DELETE /api/boards/<id>/      -> Delete board

2. ListViewSet ('lists') -> /api/lists/
   - GET /api/lists/               -> List all lists
   - POST /api/lists/              -> Create list
   - GET /api/lists/<id>/          -> Retrieve list
   - PATCH /api/lists/<id>/        -> Partial update
   - PUT /api/lists/<id>/          -> Full update
   - DELETE /api/lists/<id>/       -> Delete list
   - POST /api/lists/<id>/reorder/ -> Custom reorder action

3. CardViewSet ('cards') -> /api/cards/
   - GET /api/cards/               -> List all cards
   - POST /api/cards/              -> Create card
   - GET /api/cards/<id>/          -> Retrieve card
   - PATCH /api/cards/<id>/        -> Partial update (with logging)
   - PUT /api/cards/<id>/          -> Full update
   - DELETE /api/cards/<id>/       -> Delete card

4. UserViewSet ('users') -> /api/users/
   - GET /api/users/               -> List all users
   - GET /api/users/<id>/          -> Retrieve user

Additional Endpoints:
- POST /api/register/             -> User registration (custom function view)

Auto-Generated Endpoint Documentation:
- All endpoints support OPTIONS requests for CORS
- DefaultRouter generates API root at /api/ with all URLs
- Browsable API available at each endpoint in browser
"""

from rest_framework.routers import DefaultRouter
from boards.views import BoardViewSet, CardViewSet, ListViewSet, UserViewSet, register_user
from django.urls import path

# Initialize DefaultRouter
# This router will generate all REST API endpoints for registered ViewSets
router = DefaultRouter()

# Register ViewSets with router
# Format: router.register(r'<url_prefix>', <ViewSetClass>, basename='<optional>')
# URL prefix becomes part of endpoint path: /api/<url_prefix>/

# Boards API endpoints
# Prefix 'boards' -> /api/boards/
router.register(r'boards', BoardViewSet)

# Lists API endpoints
# Prefix 'lists' -> /api/lists/
router.register(r'lists', ListViewSet)

# Cards API endpoints
# Prefix 'cards' -> /api/cards/
router.register(r'cards', CardViewSet)

# Users API endpoints (read-only)
# Prefix 'users' -> /api/users/
router.register(r'users', UserViewSet)

# Combine auto-generated router URLs with custom endpoints
# Router generates: /api/boards/, /api/lists/, /api/cards/, /api/users/
# We add: /api/register/
urlpatterns = router.urls + [
    path('register/', register_user)
]