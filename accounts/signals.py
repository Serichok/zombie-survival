from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PlayerStats, User


@receiver(post_save, sender=User)
def create_player_stats(sender, instance, created, **kwargs):
    if created:
        PlayerStats.objects.create(user=instance)
