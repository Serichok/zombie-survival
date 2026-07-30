from django.db import models
from rooms.models import Room


class Game(models.Model):
    class Status(models.TextChoices): RUNNING = "running", "Идёт"; STOPPED = "stopped", "Остановлена"; FINISHED = "finished", "Завершена"
    class Winner(models.TextChoices): SURVIVORS = "survivors", "Выжившие"; ZOMBIES = "zombies", "Зомби"; NONE = "none", "Нет"
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name="game")
    map_name = models.CharField(max_length=40, default="Нурсая")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    winner = models.CharField(max_length=12, choices=Winner.choices, default=Winner.NONE)
    started_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    map_data = models.JSONField(default=dict, blank=True)


class GameEvent(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="events")
    type = models.CharField(max_length=32)
    message = models.CharField(max_length=250)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
