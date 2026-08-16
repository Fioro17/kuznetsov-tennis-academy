from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Court, Reservation


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = "__all__"


class ReservationSerializer(serializers.ModelSerializer):

    court = serializers.PrimaryKeyRelatedField(
        queryset=Court.objects.filter(is_active=True)
    )

    class Meta:
        model = Reservation
        fields = [
            "id",
            "court",
            "date",
            "start_time",
            "end_time",
            "status",
        ]
        read_only_fields = ["status"]

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        # Use existing values when PATCH only changes one field
        date = data.get(
            "date",
            getattr(self.instance, "date", None)
        )

        start_time = data.get(
            "start_time",
            getattr(self.instance, "start_time", None)
        )

        end_time = data.get(
            "end_time",
            getattr(self.instance, "end_time", None)
        )

        court = data.get(
            "court",
            getattr(self.instance, "court", None)
        )

        today = timezone.localdate()
        current_time = timezone.localtime().time()
        latest_booking_date = today + timedelta(days=14)

        # 1. End must be after start
        if end_time <= start_time:
            raise serializers.ValidationError(
                {
                    "end_time":
                    "End time must be after start time."
                }
            )

        # 2. Cannot book a past date
        if date < today:
            raise serializers.ValidationError(
                {
                    "date":
                    "Reservation must be in the future."
                }
            )

        # 3. Cannot book an earlier time today
        if date == today and start_time <= current_time:
            raise serializers.ValidationError(
                {
                    "start_time":
                    "Reservation must be in the future."
                }
            )

        # 4. Maximum 14 days ahead
        if date > latest_booking_date:
            raise serializers.ValidationError(
                {
                    "date":
                    "Reservations can only be made up to 14 days ahead."
                }
            )

        # Existing active reservations
        reservations = Reservation.objects.filter(
            date=date,
            status="active"
        )

        # Important for PATCH:
        # don't compare a reservation against itself
        if self.instance:
            reservations = reservations.exclude(
                pk=self.instance.pk
            )

        # 5. User cannot have overlapping reservation
        player_overlap = reservations.filter(
            user=user,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if player_overlap:
            raise serializers.ValidationError(
                {
                    "start_time":
                    "You already have a court reservation or lesson during this time."
                }
            )

        # 6. Court cannot be double-booked
        court_overlap = reservations.filter(
            court=court,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if court_overlap:
            raise serializers.ValidationError(
                {
                    "start_time":
                    "This court is already reserved during that time."
                }
            )

        return data
