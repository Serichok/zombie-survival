from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from frontend.views import index


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls), path("health/", health), path("api/auth/", include("accounts.urls")),
    path("api/profile/", include("accounts.profile_urls")), path("api/rooms/", include("rooms.urls")),
    path("api/game/", include("game.urls")), path("api/history/", include("history.urls")), path("", index),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
