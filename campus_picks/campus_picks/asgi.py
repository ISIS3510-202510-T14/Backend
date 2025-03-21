"""
ASGI config for campus_picks project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
import campus_picks.urls


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_picks.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter(campus_picks.urls.websocket_urlpatterns),
})
