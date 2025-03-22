"""
ASGI config for campus_picks project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api_gateway import urls as api_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_picks.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": django.core.asgi.get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(api_routing.websocket_urlpatterns)
    ),
})


