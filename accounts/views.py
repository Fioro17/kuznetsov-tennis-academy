from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from coaches.models import LessonBooking
from reservations.models import Reservation

from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile


def register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = UserCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            Profile.objects.get_or_create(
                user=user
            )

            login(
                request,
                user
            )

            return redirect(
                'home'
            )

    else:

        form = UserCreationForm()

    context = {
        'form': form,
    }

    return render(
        request,
        'accounts/register.html',
        context
    )


@login_required
def profile(request):

    Profile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        'accounts/profile.html'
    )


@login_required
def edit_profile(request):

    user_profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        user_form = UserUpdateForm(
            request.POST,
            instance=request.user
        )

        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=user_profile
        )

        if (
            user_form.is_valid()
            and profile_form.is_valid()
        ):

            user_form.save()
            profile_form.save()

            return redirect(
                'profile'
            )

    else:

        user_form = UserUpdateForm(
            instance=request.user
        )

        profile_form = ProfileUpdateForm(
            instance=user_profile
        )

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }

    return render(
        request,
        'accounts/edit_profile.html',
        context
    )


@login_required
def dashboard(request):

    user_profile, created = Profile.objects.get_or_create(
        user=request.user
    )

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
            |
            Q(
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

    next_reservation = upcoming_reservations.first()

    upcoming_lessons = (
        LessonBooking.objects.filter(
            player=request.user,
            status='confirmed'
        )
        .filter(
            Q(date__gt=today)
            |
            Q(
                date=today,
                end_time__gt=current_time
            )
        )
        .select_related(
            'coach__user',
            'program',
            'reservation__court'
        )
        .order_by(
            'date',
            'start_time'
        )
    )

    next_lesson = upcoming_lessons.first()

    is_coach = hasattr(
        request.user,
        'coach_profile'
    )

    context = {
        'user_profile': user_profile,
        'next_reservation': next_reservation,
        'next_lesson': next_lesson,
        'upcoming_reservations_count': (
            upcoming_reservations.count()
        ),
        'upcoming_lessons_count': (
            upcoming_lessons.count()
        ),
        'is_coach': is_coach,
    }

    return render(
        request,
        'accounts/dashboard.html',
        context
    )

