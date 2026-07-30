from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Room, RoomPlayer
from .serializers import JoinSerializer, RoomCreateSerializer
from game.services import publish_lobby, room_snapshot, start_game


class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Room.objects.exclude(status=Room.Status.FINISHED).order_by("-created_at")
    serializer_class = RoomCreateSerializer
    def list(self, request, *args, **kwargs): return Response([room_snapshot(r, request.user) for r in self.get_queryset() if r.memberships.filter(user=request.user).exists()])
    def perform_create(self, serializer):
        room = serializer.save(); RoomPlayer.objects.create(room=room, user=self.request.user, ready=True)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_room(request):
    data = JoinSerializer(data=request.data); data.is_valid(raise_exception=True)
    room = get_object_or_404(Room, code=data.validated_data["code"].upper())
    if room.status != Room.Status.LOBBY: return Response({"detail": "Комната уже запущена."}, status=400)
    if not room.check_password(data.validated_data.get("password")): return Response({"detail": "Неверный пароль."}, status=403)
    if not room.memberships.filter(user=request.user).exists():
        if room.memberships.count() >= room.max_players: return Response({"detail": "Комната заполнена."}, status=400)
        RoomPlayer.objects.create(room=room, user=request.user); publish_lobby(room)
    return Response(room_snapshot(room, request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def room_detail(request, code):
    room = get_object_or_404(Room, code=code.upper(), memberships__user=request.user)
    return Response(room_snapshot(room, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_ready(request, code):
    room = get_object_or_404(Room, code=code.upper()); member = get_object_or_404(RoomPlayer, room=room, user=request.user)
    member.ready = bool(request.data.get("ready", not member.ready)); member.save(update_fields=["ready"]); publish_lobby(room); return Response(room_snapshot(room, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def leave_room(request, code):
    room = get_object_or_404(Room, code=code.upper()); member = get_object_or_404(RoomPlayer, room=room, user=request.user)
    if room.organizer_id == request.user.id and room.memberships.count() > 1: return Response({"detail": "Сначала передайте роль организатора."}, status=400)
    member.delete(); publish_lobby(room); return Response(status=204)


def organizer_room(request, code): return get_object_or_404(Room, code=code.upper(), organizer=request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def kick(request, code, user_id):
    room = organizer_room(request, code)
    if user_id == request.user.id: return Response({"detail": "Организатора нельзя удалить."}, status=400)
    get_object_or_404(RoomPlayer, room=room, user_id=user_id).delete(); publish_lobby(room); return Response(status=204)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transfer(request, code, user_id):
    room = organizer_room(request, code); get_object_or_404(RoomPlayer, room=room, user_id=user_id)
    room.organizer_id = user_id; room.save(update_fields=["organizer"]); publish_lobby(room); return Response(room_snapshot(room, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start(request, code):
    room = get_object_or_404(Room, code=code.upper())
    try: game = start_game(room, request.user)
    except (ValueError, PermissionError) as e: return Response({"detail": str(e)}, status=400 if isinstance(e, ValueError) else 403)
    return Response({"game_id": game.id, "room": room_snapshot(room, request.user)})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_room(request, code):
    room = organizer_room(request, code)
    if room.status == Room.Status.PLAYING:
        return Response({"detail": "Сначала завершите игру."}, status=400)
    room.delete()
    return Response(status=204)
