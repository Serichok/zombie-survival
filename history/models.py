from django.conf import settings
from django.db import models


class GameHistory(models.Model):
    game = models.ForeignKey("game.Game", null=True, blank=True, on_delete=models.SET_NULL, related_name="history")
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_history")
    room_name = models.CharField(max_length=80)
    participants = models.JSONField(default=list)
    winner = models.CharField(max_length=12)
    duration_seconds = models.PositiveIntegerField()
    played_at = models.DateTimeField()
    class Meta: ordering = ["-played_at"]
