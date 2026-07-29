from datetime import datetime, time, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Court, Reservation


class ReservationForm(forms.ModelForm):

    class Meta:
        model = Reservation

        fields = [
            'court',
            'date',
            'start_time',
            'end_time',
        ]

        widgets = {
            'court': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),

            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),

            'start_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                    'step': '1800',
                    'min': '08:00',
                    'max': '21:30',
                }
            ),

            'end_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                    'step': '1800',
                    'min': '08:30',
                    'max': '22:00',
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        today = timezone.localdate()
        latest_booking_date = today + timedelta(days=14)

        self.fields['date'].widget.attrs.update({
            'min': today.isoformat(),
            'max': latest_booking_date.isoformat(),
        })

        active_courts = Court.objects.filter(
            is_active=True
        ).order_by(
            'court_type',
            'location',
            'surface',
            'number'
        )

        self.fields['court'].queryset = active_courts

        indoor_hard = []
        outdoor_hard = []
        outdoor_clay = []
        outdoor_grass = []
        outdoor_padel = []

        for court in active_courts:

            court_option = (
                court.id,
                f'Court {court.number}'
            )

            if court.court_type == 'padel':
                outdoor_padel.append(court_option)

            elif (
                court.location == 'indoor'
                and court.surface == 'hard'
            ):
                indoor_hard.append(court_option)

            elif (
                court.location == 'outdoor'
                and court.surface == 'hard'
            ):
                outdoor_hard.append(court_option)

            elif court.surface == 'clay':
                outdoor_clay.append(court_option)

            elif court.surface == 'grass':
                outdoor_grass.append(court_option)

        grouped_choices = [
            ('', 'Select a court'),
        ]

        if indoor_hard:
            grouped_choices.append(
                ('Indoor Hard Courts', indoor_hard)
            )

        if outdoor_hard:
            grouped_choices.append(
                ('Outdoor Hard Courts', outdoor_hard)
            )

        if outdoor_clay:
            grouped_choices.append(
                ('Outdoor Clay Courts', outdoor_clay)
            )

        if outdoor_grass:
            grouped_choices.append(
                ('Outdoor Grass Courts', outdoor_grass)
            )

        if outdoor_padel:
            grouped_choices.append(
                ('Outdoor Padel Courts', outdoor_padel)
            )

        self.fields['court'].choices = grouped_choices

    def clean_start_time(self):

        start_time = self.cleaned_data.get('start_time')

        if not start_time:
            return start_time

        if start_time.minute not in (0, 30):

            raise ValidationError(
                'Start time must be on the hour or half hour.'
            )

        if start_time.second != 0:

            raise ValidationError(
                'Please select a valid 30-minute time slot.'
            )

        return start_time

    def clean_end_time(self):

        end_time = self.cleaned_data.get('end_time')

        if not end_time:
            return end_time

        if end_time.minute not in (0, 30):

            raise ValidationError(
                'End time must be on the hour or half hour.'
            )

        if end_time.second != 0:

            raise ValidationError(
                'Please select a valid 30-minute time slot.'
            )

        return end_time

    def clean(self):

        cleaned_data = super().clean()

        reservation_date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if reservation_date:

            today = timezone.localdate()
            latest_booking_date = today + timedelta(days=14)

            if reservation_date < today:

                self.add_error(
                    'date',
                    'You cannot make a reservation in the past.'
                )

            elif reservation_date > latest_booking_date:

                self.add_error(
                    'date',
                    'Reservations can only be made up to 14 days in advance.'
                )

        if not reservation_date or not start_time or not end_time:
            return cleaned_data

        opening_time = time(8, 0)
        closing_time = time(22, 0)

        if start_time < opening_time:

            self.add_error(
                'start_time',
                'Reservations cannot begin before 8:00 AM.'
            )

        if end_time > closing_time:

            self.add_error(
                'end_time',
                'Reservations must end by 10:00 PM.'
            )

        if end_time <= start_time:

            self.add_error(
                'end_time',
                'The end time must be later than the start time.'
            )

            return cleaned_data

        reservation_datetime = timezone.make_aware(
            datetime.combine(
                reservation_date,
                start_time
            )
        )

        if reservation_datetime <= timezone.now():

            self.add_error(
                'start_time',
                'Reservations must be made for a future date and time.'
            )

        start_minutes = (
            start_time.hour * 60
            + start_time.minute
        )

        end_minutes = (
            end_time.hour * 60
            + end_time.minute
        )

        duration = end_minutes - start_minutes

        if duration < 30:

            self.add_error(
                'end_time',
                'A reservation must be at least 30 minutes.'
            )

        elif duration > 120:

            self.add_error(
                'end_time',
                'A reservation cannot be longer than 2 hours.'
            )

        return cleaned_data