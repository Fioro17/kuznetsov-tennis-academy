from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404

from .forms import ReservationForm
from .models import Reservation



@login_required
def create_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)

        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user

            reservation_datetime = datetime.combine(
                reservation.date,
                reservation.start_time
            )

            if reservation_datetime <= datetime.now():
                form.add_error(
                    None,
                    'Reservation must be in the future.'
                )

            elif reservation.end_time <= reservation.start_time:
                form.add_error(
                    'end_time',
                    'End time must be later than start time.'
                )

            else:
                overlapping_reservations = Reservation.objects.filter(
                    court=reservation.court,
                    date=reservation.date,
                    status='active',
                    start_time__lt=reservation.end_time,
                    end_time__gt=reservation.start_time,
                )

                if overlapping_reservations.exists():
                    form.add_error(
                        None,
                        'This court is already reserved during that time.'
                    )

                else:
                    reservation.save()
                    return redirect('my_reservations')

    else:
        form = ReservationForm()

    return render(
        request,
        'reservations/create_reservation.html',
        {'form': form}
    )

from datetime import date

@login_required
def my_reservations(request):
    upcoming_reservations = Reservation.objects.filter(
        user=request.user,
        status='active',
        date__gte=date.today()
    ).order_by(
        'date',
        'start_time'
    )

    reservation_history = Reservation.objects.filter(
        user=request.user
    ).exclude(
        status='active',
        date__gte=date.today()
    ).order_by(
        '-date',
        '-start_time'
    )

    context = {
        'upcoming_reservations': upcoming_reservations,
        'reservation_history': reservation_history,
    }

    return render(
        request,
        'reservations/my_reservations.html',
        context
    )

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user
    )

    if request.method == 'POST':
        reservation.status = 'cancelled'
        reservation.save()

    return redirect('my_reservations')