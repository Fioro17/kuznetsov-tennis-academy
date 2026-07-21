from django.shortcuts import get_object_or_404, render

from .models import Coach


def coach_list(request):

    coaches = Coach.objects.filter(
        is_available=True
    ).prefetch_related(
        'programs'
    ).select_related(
        'user'
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
            'programs'
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