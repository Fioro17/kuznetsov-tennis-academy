from django.contrib import admin
from .models import Coach, LessonProgram, LessonBooking


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'title',
        'specialty',
        'years_of_experience',
        'hourly_rate',
        'is_available',
        'is_featured',
    )

    list_filter = (
        'specialty',
        'is_available',
        'is_featured',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'title',
        'nationality',
    )

    filter_horizontal = (
        'programs',
    )


@admin.register(LessonProgram)
class LessonProgramAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'lesson_type',
        'duration_minutes',
        'maximum_players',
        'court_type',
        'is_active',
    )

    list_filter = (
        'lesson_type',
        'court_type',
        'is_active',
    )

    search_fields = (
        'name',
        'description',
    )


@admin.register(LessonBooking)
class LessonBookingAdmin(admin.ModelAdmin):
    list_display = (
        'player',
        'coach',
        'program',
        'date',
        'start_time',
        'end_time',
        'status',
    )

    list_filter = (
        'status',
        'date',
        'preferred_location',
        'preferred_surface',
    )

    search_fields = (
        'player__username',
        'player__first_name',
        'player__last_name',
        'coach__user__username',
        'coach__user__first_name',
        'coach__user__last_name',
        'program__name',
    )

    readonly_fields = (
        'created_at',
    )