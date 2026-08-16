from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(
    "courts", 
    views.CourtViewSet
)

router.register(
    "reservations",
    views.ReservationViewSet,
    basename="reservation"
)

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
    path(
        "api/",
        include(router.urls)
        ),
]