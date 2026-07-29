from datetime import datetime, timedelta
from django.db import models
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from reservations.models import Court, Reservation
from .forms import LessonBookingForm
from .models import Coach, LessonBooking, LessonProgram
from django.db.models import Q

def coach_list(request):

    coaches = Coach.objects.filter(
        is_available=True
    ).select_related(
        'user'
    ).prefetch_related(
        Prefetch(
            'programs',
            queryset=LessonProgram.objects.filter(
                is_active=True
            )
        )
    )

    context = {
        'coaches': coaches,
    }

    return render(
        request,
        'coaches/coach_list.html',
        context
    )


def coach_detail(request, coach_id):

    coach = get_object_or_404(
        Coach.objects.select_related(
            'user'
        ).prefetch_related(
            Prefetch(
                'programs',
                queryset=LessonProgram.objects.filter(
                    is_active=True
                )
            )
        ),
        id=coach_id,
        is_available=True
    )

    context = {
        'coach': coach,
    }

    return render(
        request,
        'coaches/coach_detail.html',
        context
    )


@login_required
def book_lesson(request, coach_id):

    coach = get_object_or_404(
        Coach.objects.select_related(
            'user'
        ).prefetch_related(
            'programs'
        ),
        id=coach_id,
        is_available=True
    )

    if request.method == 'POST':

        form = LessonBookingForm(
            request.POST,
            coach=coach
        )

        if form.is_valid():

            program = form.cleaned_data['program']
            lesson_date = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            preferred_location = form.cleaned_data[
                'preferred_location'
            ]
            preferred_surface = form.cleaned_data[
                'preferred_surface'
            ]

            start_datetime = timezone.make_aware(
                datetime.combine(
                    lesson_date,
                    start_time
                )
            )

            end_datetime = start_datetime + timedelta(
                minutes=program.duration_minutes
            )

            end_time = end_datetime.time()

            if start_datetime <= timezone.now():

                form.add_error(
                    'start_time',
                    'Lessons must be booked in the future.'
                )

            elif not coach.programs.filter(
                id=program.id,
                is_active=True
            ).exists():

                form.add_error(
                    'program',
                    'This program is not offered by this coach.'
                )

            else:

                coach_has_conflict = LessonBooking.objects.filter(
                    coach=coach,
                    date=lesson_date,
                    status='confirmed',
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exists()

                if coach_has_conflict:

                    form.add_error(
                        'start_time',
                        'This coach already has a lesson at this time.'
                    )

                else:

                    matching_courts = Court.objects.filter(
                        court_type=program.court_type,
                        location=preferred_location,
                        surface=preferred_surface,
                        is_active=True
                    ).order_by(
                        'number'
                    )

                    available_court = None

                    for court in matching_courts:

                        court_has_conflict = Reservation.objects.filter(
                            court=court,
                            date=lesson_date,
                            status='active',
                            start_time__lt=end_time,
                            end_time__gt=start_time
                        ).exists()

                        if not court_has_conflict:
                            available_court = court
                            break

                    if available_court is None:

                        form.add_error(
                            None,
                            'No matching courts are available at this time.'
                        )

                    else:

                        with transaction.atomic():

                            reservation = Reservation.objects.create(
                                user=request.user,
                                court=available_court,
                                date=lesson_date,
                                start_time=start_time,
                                end_time=end_time,
                                status='active'
                            )

                            lesson_booking = form.save(
                                commit=False
                            )

                            lesson_booking.player = request.user
                            lesson_booking.coach = coach
                            lesson_booking.end_time = end_time
                            lesson_booking.reservation = reservation
                            lesson_booking.status = 'confirmed'

                            lesson_booking.save()

                        messages.success(
                            request,
                            (
                                f'Your lesson with {coach} was booked. '
                                f'Court {available_court.number} was assigned.'
                            )
                        )

                        return redirect(
                            'coaches:coach_detail',
                            coach_id=coach.id
                        )

    else:

        form = LessonBookingForm(
            coach=coach
        )

    context = {
        'coach': coach,
        'form': form,
    }

    return render(
        request,
        'coaches/book_lesson.html',
        context
    )

@login_required
def my_lessons(request):

    lessons = LessonBooking.objects.filter(
        player=request.user
    ).select_related(
        'coach__user',
        'program',
        'reservation__court'
    ).order_by(
        'date',
        'start_time'
    )

    context = {
        'lessons': lessons,
    }

    return render(
        request,
        'coaches/my_lessons.html',
        context
    )


@login_required
@require_POST
def cancel_lesson(request, lesson_id):

    lesson = get_object_or_404(
        LessonBooking.objects.select_related(
            'reservation'
        ),
        id=lesson_id,
        player=request.user
    )

    if lesson.status == 'cancelled':

        messages.info(
            request,
            'This lesson has already been cancelled.'
        )

        return redirect(
            'coaches:my_lessons'
        )

    if lesson.status == 'completed':

        messages.error(
            request,
            'A completed lesson cannot be cancelled.'
        )

        return redirect(
            'coaches:my_lessons'
        )

    lesson_start = timezone.make_aware(
        datetime.combine(
            lesson.date,
            lesson.start_time
        )
    )

    if lesson_start <= timezone.now():

        messages.error(
            request,
            'A past lesson cannot be cancelled.'
        )

        return redirect(
            'coaches:my_lessons'
        )

    with transaction.atomic():

        lesson.status = 'cancelled'

        lesson.save(
            update_fields=['status']
        )

        if lesson.reservation:

            lesson.reservation.status = 'cancelled'

            lesson.reservation.save(
                update_fields=['status']
            )

    messages.success(
        request,
        'Your lesson has been cancelled and the court is now available.'
    )

    return redirect(
        'coaches:my_lessons'
    )

@login_required
def coach_schedule(request):

    coach = get_object_or_404(
        Coach.objects.select_related('user'),
        user=request.user
    )

    today = timezone.localdate()
    current_time = timezone.localtime().time()

    upcoming_lessons = LessonBooking.objects.filter(
        coach=coach,
        status='confirmed'
    ).filter(
        models.Q(date__gt=today)
        |
        models.Q(
            date=today,
            start_time__gte=current_time
        )
    ).select_related(
        'player',
        'program',
        'reservation__court'
    ).order_by(
        'date',
        'start_time'
    )

    context = {
        'coach': coach,
        'upcoming_lessons': upcoming_lessons,
    }

    return render(
        request,
        'coaches/coach_schedule.html',
        context
    )

