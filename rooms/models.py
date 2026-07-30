import secrets
import string

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models


def room_code():
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


class Room(models.Model):
    class Status(models.TextChoices): LOBBY = "lobby", "Лобби"; PLAYING = "playing", "Игра"; FINISHED = "finished", "Завершена"
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=6, unique=True, default=room_code, editable=False)
    password_hash = models.CharField(max_length=128, blank=True)
    max_players = models.PositiveSmallIntegerField(default=10)
    starting_zombies = models.PositiveSmallIntegerField(default=1)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organized_rooms")
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, through="RoomPlayer", related_name="rooms")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.LOBBY)
    created_at = models.DateTimeField(auto_now_add=True)
    def set_password(self, value): self.password_hash = make_password(value) if value else ""
    def check_password(self, value): return not self.password_hash or check_password(value or "", self.password_hash)


class RoomPlayer(models.Model):
    class Role(models.TextChoices): SURVIVOR = "survivor", "Выживший"; SOLDIER = "soldier", "Солдат"; DOCTOR = "doctor", "Доктор"; ZOMBIE = "zombie", "Зомби"
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="room_memberships")
    ready = models.BooleanField(default=False)
    current_role = models.CharField(max_length=12, choices=Role.choices, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["room", "user"], name="unique_room_member")]
