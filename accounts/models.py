from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    PLAYER_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('competitive', 'Competitive'),
    ]

    ROLE_CHOICES = [
        ('player', 'Player'),
        ('coach', 'Coach'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        default='profile_pictures/default.png',
        blank=True
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    player_level = models.CharField(
        max_length=20,
        choices=PLAYER_LEVELS,
        default='beginner'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default = 'player'
    )

    bio = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
