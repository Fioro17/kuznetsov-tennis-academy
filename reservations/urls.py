from django.urls import path

from . import views


urlpatterns = [
    path(
        '',
        views.my_reservations,
        name='my_reservations'
    ),

    path(
        'create/',
        views.create_reservation,
        name='create_reservation'
    ),

    path(
        '<int:reservation_id>/cancel/',
        views.cancel_reservation,
        name='cancel_reservation'
        ),
]