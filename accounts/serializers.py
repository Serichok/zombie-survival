from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ("email", "nickname", "password")
    def create(self, validated_data):
        return User.objects.create_user(username=validated_data["email"], **validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(source="stats.level", read_only=True)
    xp = serializers.IntegerField(source="stats.xp", read_only=True)
    games_played = serializers.IntegerField(source="stats.games_played", read_only=True)
    win_rate = serializers.FloatField(source="stats.win_rate", read_only=True)
    survivor_count = serializers.IntegerField(source="stats.survivor_count", read_only=True)
    soldier_count = serializers.IntegerField(source="stats.soldier_count", read_only=True)
    doctor_count = serializers.IntegerField(source="stats.doctor_count", read_only=True)
    zombie_count = serializers.IntegerField(source="stats.zombie_count", read_only=True)
    class Meta:
        model = User
        fields = ("id", "email", "nickname", "avatar", "level", "xp", "games_played", "win_rate", "survivor_count", "soldier_count", "doctor_count", "zombie_count")
        read_only_fields = ("email",)
