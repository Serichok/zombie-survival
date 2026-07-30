from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rooms.models import RoomPlayer
from .models import Game
from .services import add_event, finish_game, game_snapshot, publish


def player_game(request, code):
    return get_object_or_404(Game.objects.select_related("room"), room__code=code.upper(), room__memberships__user=request.user)


def organizer_game(request, code):
    game = player_game(request, code)
    if game.room.organizer_id != request.user.id: raise PermissionError("Только организатор.")
    return game


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current(request, code): return Response(game_snapshot(player_game(request, code), request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_timer(request, code):
    try: game = organizer_game(request, code)
    except PermissionError as e: return Response({"detail": str(e)}, status=403)
    seconds = int(request.data.get("seconds", 0))
    if seconds < 0 or seconds > 86400: return Response({"detail": "Некорректное время."}, status=400)
    game.ends_at = timezone.now() + timedelta(seconds=seconds); game.save(update_fields=["ends_at"]); publish(game.room, "game.updated", game_snapshot(game)); return Response(game_snapshot(game, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_map(request, code):
    try: game = organizer_game(request, code)
    except PermissionError as e: return Response({"detail": str(e)}, status=403)
    payload = request.data.get("map_data", {})
    if not isinstance(payload, dict): return Response({"detail": "map_data должен быть объектом."}, status=400)
    game.map_data = {key: payload.get(key) for key in ("zombie_base", "safe_zone", "boundary")}; game.save(update_fields=["map_data"]); publish(game.room, "game.updated", game_snapshot(game)); return Response(game_snapshot(game, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assign_role(request, code, user_id):
    try: game = organizer_game(request, code)
    except PermissionError as e: return Response({"detail": str(e)}, status=403)
    role = request.data.get("role")
    if role not in RoomPlayer.Role.values: return Response({"detail": "Неизвестная роль."}, status=400)
    member = get_object_or_404(RoomPlayer, room=game.room, user_id=user_id); member.current_role = role; member.save(update_fields=["current_role"])
    publish(game.room, "game.updated", game_snapshot(game)); return Response({"user_id": user_id, "role": role})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def event(request, code):
    try: game = organizer_game(request, code); obj = add_event(game, request.user, request.data.get("type", "notice"), request.data.get("message", ""))
    except PermissionError as e: return Response({"detail": str(e)}, status=403)
    if not obj.message: return Response({"detail": "Текст события обязателен."}, status=400)
    return Response({"id": obj.id, "message": obj.message})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finish(request, code):
    try: game = organizer_game(request, code); game = finish_game(game, request.user, request.data.get("winner", "none"))
    except PermissionError as e: return Response({"detail": str(e)}, status=403)
    return Response(game_snapshot(game, request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stop(request, code):
    try: game = organizer_game(request, code)
    except PermissionError as e: return Response({"detail": str(e)}, status=403)
    game.status = Game.Status.STOPPED; game.save(update_fields=["status"]); publish(game.room, "game.updated", game_snapshot(game)); return Response(game_snapshot(game, request.user))
