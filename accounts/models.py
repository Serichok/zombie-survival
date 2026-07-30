from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=32, unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "nickname"]

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class PlayerStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="stats")
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    games_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    survivor_count = models.PositiveIntegerField(default=0)
    soldier_count = models.PositiveIntegerField(default=0)
    doctor_count = models.PositiveIntegerField(default=0)
    zombie_count = models.PositiveIntegerField(default=0)

    @property
    def win_rate(self):
        return round((self.wins / self.games_played) * 100, 1) if self.games_played else 0
