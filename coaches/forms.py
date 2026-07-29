from datetime import datetime, time, timedelta

from django import forms
from django.utils import timezone

from .models import LessonBooking


class LessonBookingForm(forms.ModelForm):

    class Meta:
        model = LessonBooking

        fields = [
            'program',
            'date',
            'start_time',
            'preferred_location',
            'preferred_surface',
            'notes',
        ]

        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),

            'start_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'step': '1800',
                    'class': 'form-control',
                }
            ),

            'preferred_location': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),

            'preferred_surface': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),

            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Optional notes for your coach',
                }
            ),
        }

    def __init__(self, *args, coach=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.coach = coach

        if coach:
            self.fields['program'].queryset = coach.programs.filter(
                is_active=True
            )

        self.fields['program'].widget.attrs.update({
            'class': 'form-select'
        })

        today = timezone.localdate()
        latest_booking_date = today + timedelta(days=14)

        self.fields['date'].widget.attrs.update({
            'min': today.isoformat(),
            'max': latest_booking_date.isoformat(),
        })

    def clean_start_time(self):

        start_time = self.cleaned_data.get('start_time')

        if not start_time:
            return start_time

        if start_time.minute not in (0, 30):

            raise forms.ValidationError(
                'Please select a time ending in :00 or :30.'
            )

        if start_time.second != 0:

            raise forms.ValidationError(
                'Please select a valid 30-minute time slot.'
            )

        return start_time

    def clean(self):

        cleaned_data = super().clean()

        lesson_date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        program = cleaned_data.get('program')

        if not lesson_date or not start_time:
            return cleaned_data

        today = timezone.localdate()
        latest_booking_date = today + timedelta(days=14)

        if lesson_date < today:
            self.add_error(
                'date',
                'You cannot book a lesson in the past.'
            )

        elif lesson_date > latest_booking_date:
            self.add_error(
                'date',
                'Lessons can only be booked up to 14 days in advance.'
            )

        opening_time = time(8, 0)
        closing_time = time(22, 0)

        if start_time < opening_time:
            self.add_error(
                'start_time',
                'The academy opens at 8:00 AM.'
            )

        lesson_datetime = timezone.make_aware(
            datetime.combine(
                lesson_date,
                start_time
            )
        )

        if lesson_datetime <= timezone.now():
            self.add_error(
                'start_time',
                'Lessons must be booked for a future date and time.'
            )

        if program:
            end_datetime = lesson_datetime + timedelta(
                minutes=program.duration_minutes
            )

            if end_datetime.time() > closing_time:
                self.add_error(
                    'start_time',
                    'The lesson must finish by 10:00 PM.'
                )

        return cleaned_data