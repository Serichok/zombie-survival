from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PlayerStats, User


@admin.register(User)
class ZombieUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Zombie Survival", {"fields": ("nickname", "avatar")}),)
    list_display = ("email", "nickname", "is_staff", "is_active")
    ordering = ("email",)


admin.site.register(PlayerStats)
