from django.contrib.auth.models import User
from django.db import models
from reservations.models import Court, Reservation


class Coach(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='coach_profile'
    )

    profile_picture = models.ImageField(
        upload_to='coach_pictures/',
        default='coach_pictures/default.png',
        blank=True
    )

    title = models.CharField(
        max_length=100,
        default='Academy Coach'
    )

    specialty = models.CharField(
        max_length=100,
    )

    biography = models.TextField()

    years_of_experience = models.PositiveIntegerField(
        default=0
    )

    hourly_rate = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=75
    )

    nationality = models.CharField(
        max_length=50,
        blank=True
    )

    utr_rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True
    )

    certifications = models.CharField(
        max_length=255,
        blank=True
    )

    programs = models.ManyToManyField(
        'LessonProgram',
        related_name='coaches',
        blank=True
    )

    is_available = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
class LessonProgram(models.Model):

    LESSON_TYPES = [
        ('private', 'Private Lesson'),
        ('semi_private', 'Semi-Private Lesson'),
        ('group', 'Group Lesson'),
        ('fitness', 'Fitness Session'),
        ('padel', 'Padel Lesson'),
    ]

    name = models.CharField(
        max_length=120
    )

    lesson_type = models.CharField(
        max_length=30,
        choices=LESSON_TYPES
    )

    description = models.TextField()

    duration_minutes = models.PositiveIntegerField(
        default=60
    )

    maximum_players = models.PositiveIntegerField(
        default=1
    )

    court_type = models.CharField(
        max_length=20,
        choices=Court.COURT_TYPES,
        default='tennis'
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.name
    
class LessonBooking(models.Model):

    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_bookings'
    )

    coach = models.ForeignKey(
        Coach,
        on_delete=models.CASCADE,
        related_name='lesson_bookings'
    )

    program = models.ForeignKey(
        LessonProgram,
        on_delete=models.PROTECT,
        related_name='bookings'
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    preferred_location = models.CharField(
        max_length=20,
        choices=Court.LOCATIONS
    )

    preferred_surface = models.CharField(
        max_length=20,
        choices=Court.SURFACES
    )

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='lesson_booking',
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f'{self.player.username} with '
            f'{self.coach} on {self.date}'
        )
