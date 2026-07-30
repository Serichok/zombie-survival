from rest_framework.permissions import BasePermission


class IsOrganizer(BasePermission):
    def has_object_permission(self, request, view, obj): return obj.organizer_id == request.user.id
