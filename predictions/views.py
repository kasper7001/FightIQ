from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse

from .models import Event, Fight, HistoricalPick


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


@login_required
def analytics_dashboard(request):
    picks = HistoricalPick.objects.all()
    settled_picks = picks.filter(outcome__in=["W", "L", "R"])
    win_loss_picks = picks.filter(outcome__in=["W", "L"])

    total_picks = picks.count()
    settled_count = settled_picks.count()
    wins = picks.filter(outcome="W").count()
    losses = picks.filter(outcome="L").count()
    refunds = picks.filter(outcome="R").count()
    pending = picks.filter(outcome="P").count()

    win_loss_total = wins + losses
    win_rate = round((wins / win_loss_total) * 100, 1) if win_loss_total else 0

    total_profit_loss = settled_picks.aggregate(
        total=Sum("profit_loss")
    )["total"] or Decimal("0.00")

    average_odds = win_loss_picks.exclude(odds__isnull=True).aggregate(
        average=Avg("odds")
    )["average"]

    bet_type_rows = (
        picks.values("bet_type")
        .annotate(
            total=Count("id"),
            wins=Count("id", filter=Q(outcome="W")),
            losses=Count("id", filter=Q(outcome="L")),
            refunds=Count("id", filter=Q(outcome="R")),
            profit=Sum("profit_loss"),
        )
        .order_by("-total")
    )

    bet_type_summary = []
    for row in bet_type_rows:
        decisions = row["wins"] + row["losses"]
        row["win_rate"] = round((row["wins"] / decisions) * 100, 1) if decisions else 0
        row["profit"] = row["profit"] or Decimal("0.00")
        row["bet_type"] = row["bet_type"] or "Unknown"
        bet_type_summary.append(row)

    top_events = (
        picks.values("event_name")
        .annotate(
            total=Count("id"),
            wins=Count("id", filter=Q(outcome="W")),
            losses=Count("id", filter=Q(outcome="L")),
            profit=Sum("profit_loss"),
        )
        .order_by("-profit")[:5]
    )

    worst_events = (
        picks.values("event_name")
        .annotate(
            total=Count("id"),
            wins=Count("id", filter=Q(outcome="W")),
            losses=Count("id", filter=Q(outcome="L")),
            profit=Sum("profit_loss"),
        )
        .order_by("profit")[:5]
    )

    monthly_summary = (
        picks.exclude(date__isnull=True)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(
            total=Count("id"),
            wins=Count("id", filter=Q(outcome="W")),
            losses=Count("id", filter=Q(outcome="L")),
            refunds=Count("id", filter=Q(outcome="R")),
            profit=Sum("profit_loss"),
        )
        .order_by("-month")[:12]
    )

    odds_ranges = build_odds_range_summary(win_loss_picks)

    return render(request, "predictions/analytics.html", {
        "total_picks": total_picks,
        "settled_count": settled_count,
        "wins": wins,
        "losses": losses,
        "refunds": refunds,
        "pending": pending,
        "win_rate": win_rate,
        "total_profit_loss": total_profit_loss,
        "average_odds": average_odds,
        "bet_type_summary": bet_type_summary,
        "top_events": top_events,
        "worst_events": worst_events,
        "monthly_summary": monthly_summary,
        "odds_ranges": odds_ranges,
    })


def build_odds_range_summary(picks):
    buckets = {
        "Under 1.50": {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "profit": Decimal("0.00"),
        },
        "1.50 to 1.99": {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "profit": Decimal("0.00"),
        },
        "2.00 to 2.99": {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "profit": Decimal("0.00"),
        },
        "3.00+": {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "profit": Decimal("0.00"),
        },
    }

    for pick in picks.exclude(odds__isnull=True):
        odds = pick.odds

        if odds < Decimal("1.50"):
            label = "Under 1.50"
        elif odds < Decimal("2.00"):
            label = "1.50 to 1.99"
        elif odds < Decimal("3.00"):
            label = "2.00 to 2.99"
        else:
            label = "3.00+"

        buckets[label]["total"] += 1

        if pick.outcome == "W":
            buckets[label]["wins"] += 1

        if pick.outcome == "L":
            buckets[label]["losses"] += 1

        buckets[label]["profit"] += pick.profit_loss or Decimal("0.00")

    summary = []

    for label, data in buckets.items():
        decisions = data["wins"] + data["losses"]
        win_rate = round((data["wins"] / decisions) * 100, 1) if decisions else 0

        summary.append({
            "label": label,
            "total": data["total"],
            "wins": data["wins"],
            "losses": data["losses"],
            "win_rate": win_rate,
            "profit": data["profit"],
        })

    return summary

@login_required
def fight_fighters_api(request, fight_id):
    fight = get_object_or_404(
        Fight.objects.select_related("fighter_a", "fighter_b"),
        id=fight_id,
    )

    fighters = [
        {
            "id": fight.fighter_a.id,
            "name": str(fight.fighter_a),
        },
        {
            "id": fight.fighter_b.id,
            "name": str(fight.fighter_b),
        },
    ]

    return JsonResponse({"fighters": fighters})
