from django.contrib import admin

from .models import Court, Reservation


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):

    list_display = [
        'number',
        'court_type',
        'surface',
        'location',
        'is_active',
    ]

    list_filter = [
        'court_type',
        'surface',
        'location',
        'is_active',
    ]

    search_fields = [
        'number',
    ]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = [
        'user',
        'court',
        'date',
        'start_time',
        'end_time',
        'status',
        'created_at',
    ]

    list_filter = [
        'status',
        'date',
        'court',
    ]

    search_fields = [
        'user__username',
    ]

    ordering = [
        '-date',
        '-start_time',
    ]