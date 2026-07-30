from django.urls import path
from . import views

urlpatterns = [path("<str:code>/", views.current), path("<str:code>/timer/", views.update_timer), path("<str:code>/map/", views.update_map), path("<str:code>/roles/<int:user_id>/", views.assign_role), path("<str:code>/events/", views.event), path("<str:code>/stop/", views.stop), path("<str:code>/finish/", views.finish)]
