from collections import defaultdict
from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ReservationForm
from .models import Court, Reservation


ACADEMY_OPENING_TIME = time(8, 0)
ACADEMY_CLOSING_TIME = time(22, 0)
SLOT_LENGTH_MINUTES = 30


def parse_selected_date(date_string):

    if not date_string:
        return None

    try:
        return datetime.strptime(
            date_string,
            '%Y-%m-%d'
        ).date()

    except ValueError:
        return None


def build_court_availability(courts, selected_date):

    if not selected_date:
        return []

    reservations = Reservation.objects.filter(
        date=selected_date,
        status='active',
        court__in=courts
    ).select_related(
        'court'
    ).order_by(
        'court_id',
        'start_time'
    )

    reservations_by_court = defaultdict(list)

    for reservation in reservations:
        reservations_by_court[
            reservation.court_id
        ].append(reservation)

    total_open_minutes = (
        ACADEMY_CLOSING_TIME.hour * 60
        - ACADEMY_OPENING_TIME.hour * 60
    )

    total_slots = (
        total_open_minutes
        // SLOT_LENGTH_MINUTES
    )

    today = timezone.localdate()
    current_time = timezone.localtime().time()

    court_availability = []

    for court in courts:

        court_reservations = reservations_by_court[
            court.id
        ]

        reserved_periods = []
        reserved_slots_count = 0

        for reservation in court_reservations:

            reserved_periods.append({
                'start': reservation.start_time.strftime(
                    '%I:%M %p'
                ).lstrip('0'),

                'end': reservation.end_time.strftime(
                    '%I:%M %p'
                ).lstrip('0'),
            })

            start_minutes = (
                reservation.start_time.hour * 60
                + reservation.start_time.minute
            )

            end_minutes = (
                reservation.end_time.hour * 60
                + reservation.end_time.minute
            )

            reserved_minutes = (
                end_minutes - start_minutes
            )

            reserved_slots_count += (
                reserved_minutes
                // SLOT_LENGTH_MINUTES
            )

        past_slots_count = 0

        if selected_date < today:

            past_slots_count = total_slots

        elif selected_date == today:

            opening_minutes = (
                ACADEMY_OPENING_TIME.hour * 60
                + ACADEMY_OPENING_TIME.minute
            )

            current_minutes = (
                current_time.hour * 60
                + current_time.minute
            )

            minutes_since_opening = max(
                current_minutes - opening_minutes,
                0
            )

            past_slots_count = min(
                (
                    minutes_since_opening
                    + SLOT_LENGTH_MINUTES - 1
                )
                // SLOT_LENGTH_MINUTES,
                total_slots
            )

        unavailable_slots_count = min(
            reserved_slots_count
            + past_slots_count,
            total_slots
        )

        available_slots_count = max(
            total_slots
            - unavailable_slots_count,
            0
        )

        court_availability.append({
            'court': court,
            'reserved_periods': reserved_periods,
            'available_slots_count': available_slots_count,
        })

    return court_availability


@login_required
def create_reservation(request):

    selected_date_string = request.GET.get(
        'date',
        ''
    )

    selected_court_id = request.GET.get(
        'court',
        ''
    )

    if request.method == 'POST':

        form = ReservationForm(
            request.POST
        )

        selected_date_string = request.POST.get(
            'date',
            ''
        )

        selected_court_id = request.POST.get(
            'court',
            ''
        )

        if form.is_valid():

            reservation = form.save(
                commit=False
            )

            reservation.user = request.user

            today = timezone.localdate()
            current_time = timezone.localtime().time()

            reservation_is_past = (
                reservation.date < today
                or (
                    reservation.date == today
                    and reservation.start_time <= current_time
                )
            )

            player_overlap_exists = Reservation.objects.filter(
                user=request.user,
                date=reservation.date,
                status='active',
                start_time__lt=reservation.end_time,
                end_time__gt=reservation.start_time
            ).exists()

            court_overlap_exists = Reservation.objects.filter(
                court=reservation.court,
                date=reservation.date,
                status='active',
                start_time__lt=reservation.end_time,
                end_time__gt=reservation.start_time
            ).exists()

            if reservation_is_past:

                form.add_error(
                    'start_time',
                    'Reservation must be in the future.'
                )

            elif player_overlap_exists:

                form.add_error(
                    'start_time',
                    (
                        'You already have a court reservation '
                        'or lesson during this time.'
                    )
                )

            elif court_overlap_exists:

                form.add_error(
                    'start_time',
                    (
                        'This court is already reserved '
                        'during that time.'
                    )
                )

            else:

                reservation.save()

                messages.success(
                    request,
                    (
                        'Your reservation was created '
                        'successfully.'
                    )
                )

                return redirect(
                    'my_reservations'
                )

    else:

        initial_data = {}

        if selected_date_string:
            initial_data['date'] = (
                selected_date_string
            )

        if selected_court_id:
            initial_data['court'] = (
                selected_court_id
            )

        form = ReservationForm(
            initial=initial_data
        )

    courts = Court.objects.filter(
        is_active=True
    ).order_by(
        'court_type',
        'location',
        'surface',
        'number'
    )

    selected_date = parse_selected_date(
        selected_date_string
    )

    if selected_date_string and not selected_date:

        messages.error(
            request,
            'Please select a valid date.'
        )

        selected_date_string = ''

    selected_court = None

    if selected_court_id:

        selected_court = courts.filter(
            id=selected_court_id
        ).first()

    court_availability = build_court_availability(
        courts,
        selected_date
    )

    context = {
        'form': form,
        'selected_date': selected_date_string,
        'selected_court': selected_court,
        'court_availability': court_availability,
        'today': timezone.localdate().isoformat(),
        'academy_opening_time': ACADEMY_OPENING_TIME,
        'academy_closing_time': ACADEMY_CLOSING_TIME,
    }

    return render(
        request,
        'reservations/create_reservation.html',
        context
    )


@login_required
def my_reservations(request):

    today = timezone.localdate()
    current_time = timezone.localtime().time()

    upcoming_reservations = (
        Reservation.objects.filter(
            user=request.user,
            status='active',
            lesson_booking__isnull=True
        )
        .filter(
            Q(date__gt=today)
            | Q(
                date=today,
                end_time__gt=current_time
            )
        )
        .select_related(
            'court'
        )
        .order_by(
            'date',
            'start_time'
        )
    )

    reservation_history = (
        Reservation.objects.filter(
            user=request.user,
            lesson_booking__isnull=True
        )
        .exclude(
            id__in=upcoming_reservations.values(
                'id'
            )
        )
        .select_related(
            'court'
        )
        .order_by(
            '-date',
            '-start_time'
        )
    )

    context = {
        'upcoming_reservations': (
            upcoming_reservations
        ),
        'reservation_history': (
            reservation_history
        ),
        'active_reservations_count': (
            upcoming_reservations.count()
        ),
        'reservation_history_count': (
            reservation_history.count()
        ),
    }

    return render(
        request,
        'reservations/my_reservations.html',
        context
    )


@login_required
def cancel_reservation(
    request,
    reservation_id
):

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user,
        lesson_booking__isnull=True
    )

    if request.method != 'POST':

        return redirect(
            'my_reservations'
        )

    if reservation.status == 'cancelled':

        messages.info(
            request,
            (
                'This reservation has already '
                'been cancelled.'
            )
        )

        return redirect(
            'my_reservations'
        )

    reservation.status = 'cancelled'

    reservation.save(
        update_fields=['status']
    )

    messages.success(
        request,
        (
            'Your reservation was cancelled '
            'successfully.'
        )
    )

    return redirect(
        'my_reservations'
    )