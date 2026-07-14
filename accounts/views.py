from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile
from datetime import date
from reservations.models import Reservation


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    Profile.objects.get_or_create(user=request.user)

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

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            return redirect('profile')

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

    upcoming_reservations = Reservation.objects.filter(
        user=request.user,
        status='active',
        date__gte=date.today()
    ).order_by(
        'date',
        'start_time'
    )[:3]

    context = {
        'user_profile': user_profile,
        'upcoming_reservations': upcoming_reservations,
    }

    return render(
        request,
        'accounts/dashboard.html',
        context
    )


