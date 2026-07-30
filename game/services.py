"""Game domain services: one authoritative place for state transitions."""
import random
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from accounts.models import PlayerStats
from history.models import GameHistory
from rooms.models import Room, RoomPlayer
from .models import Game, GameEvent


def room_snapshot(room, viewer=None):
    memberships = room.memberships.select_related("user").all()
    return {"id": room.id, "name": room.name, "code": room.code, "status": room.status, "max_players": room.max_players,
            "starting_zombies": room.starting_zombies, "duration_minutes": room.duration_minutes, "organizer_id": room.organizer_id,
            "members": [{"id": m.user_id, "nickname": m.user.nickname, "avatar": m.user.avatar.url if m.user.avatar else None,
                         "ready": m.ready, "is_organizer": m.user_id == room.organizer_id,
                         "role": m.current_role if viewer and viewer.id == m.user_id else None} for m in memberships]}


def publish(room, event_type, payload):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"room_{room.code}", {"type": "broadcast", "event_type": event_type, "payload": payload})


def publish_lobby(room):
    publish(room, "lobby.updated", room_snapshot(room))


@transaction.atomic
def start_game(room, actor):
    room = Room.objects.select_for_update().get(pk=room.pk)
    if room.organizer_id != actor.id: raise PermissionError("Только организатор может начать игру.")
    players = list(room.memberships.select_for_update().all())
    if len(players) < 2: raise ValueError("Для старта нужны минимум два игрока.")
    if room.status != Room.Status.LOBBY: raise ValueError("Игра уже запущена.")
    if room.starting_zombies >= len(players): raise ValueError("Стартовых зомби должно быть меньше числа игроков.")
    random.shuffle(players)
    zombie_ids = {m.id for m in players[:room.starting_zombies]}
    non_zombies = [m for m in players if m.id not in zombie_ids]
    for index, member in enumerate(players):
        if member.id in zombie_ids: member.current_role = RoomPlayer.Role.ZOMBIE
        elif index == room.starting_zombies: member.current_role = RoomPlayer.Role.DOCTOR
        elif index == room.starting_zombies + 1: member.current_role = RoomPlayer.Role.SOLDIER
        else: member.current_role = RoomPlayer.Role.SURVIVOR
        member.ready = False
    RoomPlayer.objects.bulk_update(players, ["current_role", "ready"])
    room.status = Room.Status.PLAYING; room.save(update_fields=["status"])
    game = Game.objects.create(room=room, ends_at=timezone.now() + timedelta(minutes=room.duration_minutes))
    GameEvent.objects.create(game=game, type="started", message="Игра началась")
    publish(room, "game.started", game_snapshot(game))
    return game


def game_snapshot(game, user=None):
    members = game.room.memberships.all()
    roles = list(members.values_list("current_role", flat=True))
    data = {"id": game.id, "status": game.status, "winner": game.winner, "map_name": game.map_name, "map_data": game.map_data,
            "ends_at": game.ends_at.isoformat(), "players": len(roles), "zombies": roles.count("zombie"),
            "survivors": len(roles) - roles.count("zombie")}
    if user:
        member = members.filter(user=user).first(); data["my_role"] = member.current_role if member else None
    return data


@transaction.atomic
def finish_game(game, actor, winner):
    game = Game.objects.select_for_update().select_related("room").get(pk=game.pk)
    if game.room.organizer_id != actor.id: raise PermissionError("Только организатор может завершить игру.")
    if game.status == Game.Status.FINISHED: return game
    game.status = Game.Status.FINISHED; game.winner = winner; game.ended_at = timezone.now(); game.save(update_fields=["status", "winner", "ended_at"])
    game.room.status = Room.Status.FINISHED; game.room.save(update_fields=["status"])
    members = list(game.room.memberships.select_related("user", "user__stats"))
    participant_names = [m.user.nickname for m in members]
    elapsed = max(1, int((game.ended_at - game.started_at).total_seconds()))
    for member in members:
        stats = member.user.stats; stats.games_played += 1
        field = f"{member.current_role}_count"; setattr(stats, field, getattr(stats, field) + 1)
        is_win = (winner == Game.Winner.ZOMBIES and member.current_role == "zombie") or (winner == Game.Winner.SURVIVORS and member.current_role != "zombie")
        gained = 20 + (50 if is_win else 0) + (20 if member.current_role != "zombie" and winner == Game.Winner.SURVIVORS else 0)
        if is_win: stats.wins += 1
        stats.xp += gained; stats.level = max(1, stats.xp // 100 + 1); stats.save()
        GameHistory.objects.create(game=game, participant=member.user, room_name=game.room.name, participants=participant_names, winner=winner, duration_seconds=elapsed, played_at=game.ended_at)
    GameEvent.objects.create(game=game, type="finished", message="Игра окончена", payload={"winner": winner})
    publish(game.room, "game.finished", game_snapshot(game))
    return game


def add_event(game, actor, event_type, message):
    if game.room.organizer_id != actor.id: raise PermissionError("Только организатор может отправлять события.")
    event = GameEvent.objects.create(game=game, type=event_type, message=message)
    publish(game.room, "game.event", {"id": event.id, "type": event.type, "message": event.message, "created_at": event.created_at.isoformat()})
    return event
