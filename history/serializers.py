from rest_framework import serializers
from .models import GameHistory


class GameHistorySerializer(serializers.ModelSerializer):
    class Meta: model = GameHistory; fields = ("id", "room_name", "participants", "winner", "duration_seconds", "played_at")
