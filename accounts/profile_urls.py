from django.urls import path
from .views import AvatarView, ProfileView

urlpatterns = [path("me/", ProfileView.as_view()), path("avatar/", AvatarView.as_view())]
