from rest_framework import serializers
from .models import Room


class RoomCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=64)
    code = serializers.CharField(read_only=True)
    class Meta: model = Room; fields = ("name", "code", "password", "max_players", "starting_zombies", "duration_minutes")
    def validate(self, data):
        if data.get("starting_zombies", 1) >= data.get("max_players", 10): raise serializers.ValidationError("Зомби должны быть меньше максимума игроков.")
        return data
    def create(self, data):
        password = data.pop("password", ""); room = Room(organizer=self.context["request"].user, **data); room.set_password(password); room.save(); return room


class JoinSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(required=False, allow_blank=True, max_length=64)
