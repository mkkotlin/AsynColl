"""
ASGI config for collab_board project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import boards.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collab_board.settings')

# application = get_asgi_application()
application = ProtocolTypeRouter({
    "http":get_asgi_application(),
    "websocket":URLRouter( boards.routing.websocket_urlpatterns)
})
