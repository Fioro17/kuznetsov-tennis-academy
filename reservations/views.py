from collections import defaultdict
from datetime import datetime, time, timedelta 

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

def build_single_court_slots(court, selected_date):

    if not court or not selected_date:
        return []

    reservations = Reservation.objects.filter(
        court=court,
        date=selected_date,
        status='active'
    ).order_by(
        'start_time'
    )

    slots = []

    current_datetime = datetime.combine(
        selected_date,
        ACADEMY_OPENING_TIME
    )

    closing_datetime = datetime.combine(
        selected_date,
        ACADEMY_CLOSING_TIME
    )

    now = timezone.localtime()

    while current_datetime < closing_datetime:

        slot_end_datetime = current_datetime + timedelta(
            minutes=SLOT_LENGTH_MINUTES
        )

        slot_start_time = current_datetime.time()
        slot_end_time = slot_end_datetime.time()

        reservation_exists = reservations.filter(
            start_time__lt=slot_end_time,
            end_time__gt=slot_start_time
        ).exists()

        aware_slot_start = timezone.make_aware(
            current_datetime
        )

        if aware_slot_start <= now:
            status = 'past'

        elif reservation_exists:
            status = 'reserved'

        else:
            status = 'available'

        slots.append({
            'start_time': slot_start_time,
            'end_time': slot_end_time,
            'status': status,
            'start_value': slot_start_time.strftime('%H:%M'),
            'end_value': slot_end_time.strftime('%H:%M'),
            'label': slot_start_time.strftime(
                '%I:%M %p'
            ).lstrip('0'),
        })

        current_datetime = slot_end_datetime

    return slots

@login_required
def create_reservation(request):

    today = timezone.localdate()
    latest_booking_date = today + timedelta(days=14)

    courts = Court.objects.filter(
        is_active=True
    ).order_by(
        'court_type',
        'location',
        'surface',
        'number'
    )

    availability_date_string = request.GET.get(
        'availability_date',
        ''
    )

    availability_court_id = request.GET.get(
        'availability_court',
        ''
    )

    availability_date = parse_selected_date(
        availability_date_string
    )

    availability_court = None
    availability_slots = []
    availability_error = None

    if availability_court_id:

        availability_court = courts.filter(
            id=availability_court_id
        ).first()

        if not availability_court:
            availability_error = (
                'Please select a valid active court.'
            )

    if availability_date_string and not availability_date:

        availability_error = (
            'Please select a valid date.'
        )

    elif availability_date:

        if availability_date < today:

            availability_error = (
                'Availability cannot be viewed for a past date.'
            )

        elif availability_date > latest_booking_date:

            availability_error = (
                'Availability can only be viewed up to '
                '14 days ahead.'
            )

    if (
        availability_date
        and availability_court
        and not availability_error
    ):

        availability_slots = build_single_court_slots(
            availability_court,
            availability_date
        )

    if request.method == 'POST':

        form = ReservationForm(
            request.POST
        )

        if form.is_valid():

            reservation = form.save(
                commit=False
            )

            reservation.user = request.user

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
                    'Your reservation was created successfully.'
                )

                return redirect(
                    'my_reservations'
                )

    else:

        initial_data = {}

        if availability_date:
            initial_data['date'] = availability_date

        if availability_court:
            initial_data['court'] = availability_court.id

        form = ReservationForm(
            initial=initial_data
        )

    context = {
        'form': form,
        'courts': courts,
        'availability_date': availability_date_string,
        'availability_court': availability_court,
        'availability_court_id': availability_court_id,
        'availability_slots': availability_slots,
        'availability_error': availability_error,
        'today': today.isoformat(),
        'latest_booking_date': latest_booking_date.isoformat(),
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