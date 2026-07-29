from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Court(models.Model):

    COURT_TYPES = [
        ('tennis', 'Tennis'),
        ('padel', 'Padel'),
    ]

    LOCATIONS = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
    ]

    SURFACES = [
        ('hard', 'Hard'),
        ('clay', 'Clay'),
        ('grass', 'Grass'),
    ]

    court_type = models.CharField(
        max_length=20,
        choices=COURT_TYPES
    )

    location = models.CharField(
        max_length=20,
        choices=LOCATIONS
    )

    surface = models.CharField(
        max_length=20,
        choices=SURFACES
    )

    number = models.PositiveIntegerField()

    is_active = models.BooleanField(
        default=True
    )

    def clean(self):

        super().clean()

        if (
            self.court_type == 'padel'
            and self.surface != 'hard'
        ):
            raise ValidationError(
                'Padel courts can only have hard surfaces.'
            )

    def __str__(self):

        return (
            f'{self.get_location_display()} '
            f'{self.get_court_type_display()} '
            f'{self.get_surface_display()} '
            f'Court {self.number}'
        )


class Reservation(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    def clean(self):

        super().clean()

        if (
            not self.date
            or not self.start_time
            or not self.end_time
        ):
            return

        if self.end_time <= self.start_time:
            raise ValidationError(
                'End time must be later than start time.'
            )

        if not self.court_id:
            return

        overlapping_reservations = Reservation.objects.filter(
            court=self.court,
            date=self.date,
            status='active',
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )

        if self.pk:
            overlapping_reservations = (
                overlapping_reservations.exclude(
                    pk=self.pk
                )
            )

        if overlapping_reservations.exists():
            raise ValidationError(
                'This court is already reserved during '
                'the selected time.'
            )

    def __str__(self):

        return (
            f'{self.user.username} reserved '
            f'{self.court} '
            f'on {self.date}'
        )