from django.urls import path
from . import views

urlpatterns = [path("", views.RoomListCreateView.as_view()), path("join/", views.join_room), path("<str:code>/", views.room_detail), path("<str:code>/ready/", views.set_ready), path("<str:code>/leave/", views.leave_room), path("<str:code>/start/", views.start), path("<str:code>/delete/", views.delete_room), path("<str:code>/members/<int:user_id>/kick/", views.kick), path("<str:code>/members/<int:user_id>/organizer/", views.transfer)]
