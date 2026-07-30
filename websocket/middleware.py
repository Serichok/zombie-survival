from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from accounts.models import User


@database_sync_to_async
def user_for_id(user_id):
    try: return User.objects.get(id=user_id)
    except User.DoesNotExist: return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, inner): self.inner = inner
    async def __call__(self, scope, receive, send):
        token = parse_qs(scope["query_string"].decode()).get("token", [None])[0]
        try: scope["user"] = await user_for_id(AccessToken(token)["user_id"])
        except (TokenError, KeyError, TypeError): scope["user"] = AnonymousUser()
        return await self.inner(scope, receive, send)
