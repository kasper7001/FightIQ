from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Event


@login_required
def event_list(request):
    events = (
        Event.objects
        .prefetch_related("fights", "fights__prediction")
        .order_by("-date")
    )

    return render(request, "predictions/event_list.html", {
        "events": events,
    })


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(
        Event.objects.prefetch_related(
            "fights",
            "fights__fighter_a",
            "fights__fighter_b",
            "fights__prediction",
            "fights__prediction__predicted_winner",
        ),
        id=event_id,
    )

    return render(request, "predictions/event_detail.html", {
        "event": event,
    })
