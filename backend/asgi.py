import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from websocket.middleware import JWTAuthMiddleware
from websocket.routing import websocket_urlpatterns

application = ProtocolTypeRouter({"http": get_asgi_application(), "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns))})
