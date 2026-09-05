from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .models import Event, Fight, HistoricalPick, Prediction


@login_required
def event_list(request):
    events = (
        Event.objects
        .prefetch_related("fights")
        .order_by("-date")
    )

    return render(
        request,
        "predictions/event_list.html",
        {"events": events},
    )


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(
        Event.objects.prefetch_related(
            "fights",
            "fights__fighter_a",
            "fights__fighter_b",
        ),
        id=event_id,
    )

    user_predictions = {
        prediction.fight_id: prediction
        for prediction in (
            Prediction.objects
            .filter(
                user=request.user,
                fight__event=event,
            )
            .select_related("predicted_winner")
        )
    }

    fight_rows = []

    for fight in event.fights.all():
        fight_rows.append({
            "fight": fight,
            "prediction": user_predictions.get(fight.id),
        })

    return render(
        request,
        "predictions/event_detail.html",
        {
            "event": event,
            "fight_rows": fight_rows,
        },
    )


@login_required
def analytics_dashboard(request):
    selected_promotion = request.GET.get("promotion", "").strip().upper()

    historical_rows = build_historical_pick_rows(
        request.user,
        selected_promotion,
    )

    current_rows = build_current_prediction_rows(
        request.user,
        selected_promotion,
    )

    all_rows = historical_rows + current_rows

    available_promotions = get_available_promotions(request.user)

    context = build_analytics_context(all_rows, current_rows)
    context["selected_promotion"] = selected_promotion
    context["available_promotions"] = available_promotions
    context["historical_count"] = len(historical_rows)
    context["current_count"] = len(current_rows)
    context["current_prediction_rows"] = current_rows[:25]

    return render(request, "predictions/analytics.html", context)


def build_historical_pick_rows(user, selected_promotion=""):
    rows = []

    historical_picks = (
        HistoricalPick.objects
        .filter(user=user)
        .order_by("-date", "-id")
    )

    if selected_promotion:
        historical_picks = historical_picks.filter(promotion__iexact=selected_promotion)

    for pick in historical_picks:
        rows.append({
            "source": "Historical",
            "promotion": pick.promotion,
            "date": pick.date,
            "event_name": pick.event_name or "Unknown Event",
            "fight_name": pick.fight_name or "",
            "pick_name": pick.pick_name or "",
            "bet_type": pick.bet_type or "Unknown",
            "stake": pick.stake,
            "odds": pick.odds,
            "outcome": pick.outcome,
            "profit_loss": pick.profit_loss,
            "predicted_method": "",
            "actual_method": "",
            "method_correct": None,
            "is_current": False,
        })

    return rows


def build_current_prediction_rows(user, selected_promotion=""):
    rows = []

    predictions = (
        Prediction.objects
        .filter(user=user)
        .select_related(
            "fight",
            "fight__event",
            "fight__fighter_a",
            "fight__fighter_b",
            "fight__result",
            "predicted_winner",
        )
        .order_by("-fight__event__date", "-id")
    )

    if selected_promotion:
        predictions = predictions.filter(fight__event__promotion__iexact=selected_promotion)

    for prediction in predictions:
        result = getattr(prediction.fight, "result", None)

        rows.append({
            "source": "FightIQ",
            "promotion": prediction.fight.event.promotion,
            "date": prediction.fight.event.date,
            "event_name": f"{prediction.fight.event.promotion}: {prediction.fight.event.name}",
            "fight_name": str(prediction.fight),
            "pick_name": str(prediction.predicted_winner),
            "bet_type": "Winner Pick",
            "stake": prediction.stake_amount(),
            "odds": prediction.predicted_odds(),
            "outcome": prediction.result_status(),
            "profit_loss": prediction.profit_loss(),
            "predicted_method": prediction.get_method_display(),
            "actual_method": result.get_method_display() if result else "",
            "method_correct": prediction.is_method_correct() if result else None,
            "is_current": True,
        })

    return rows

def get_available_promotions(user):
    historical_promotions = set(
        HistoricalPick.objects
        .exclude(promotion="")
        .values_list("promotion", flat=True)
    )

    current_promotions = set(
        Prediction.objects
        .filter(user=user)
        .exclude(fight__event__promotion="")
        .values_list("fight__event__promotion", flat=True)
    )

    return sorted(historical_promotions | current_promotions)

def build_analytics_context(rows, current_rows):
    total_picks = len(rows)

    settled_rows = [row for row in rows if row["outcome"] in ["W", "L", "R"]]
    win_loss_rows = [row for row in rows if row["outcome"] in ["W", "L"]]

    wins = len([row for row in rows if row["outcome"] == "W"])
    losses = len([row for row in rows if row["outcome"] == "L"])
    refunds = len([row for row in rows if row["outcome"] == "R"])
    pending = len([row for row in rows if row["outcome"] == "P"])

    win_loss_total = wins + losses
    win_rate = round((wins / win_loss_total) * 100, 1) if win_loss_total else 0

    total_profit_loss = sum(
        row["profit_loss"] or Decimal("0.00")
        for row in settled_rows
    )

    odds_values = [
        row["odds"]
        for row in win_loss_rows
        if row["odds"] is not None
    ]

    average_odds = (
        (sum(odds_values) / len(odds_values)).quantize(Decimal("0.01"))
        if odds_values else None
    )

    current_win_loss_rows = [
        row for row in current_rows
        if row["outcome"] in ["W", "L"]
    ]

    current_wins = len([row for row in current_rows if row["outcome"] == "W"])
    current_losses = len([row for row in current_rows if row["outcome"] == "L"])
    method_correct = len([
        row for row in current_rows
        if row["outcome"] == "W" and row["method_correct"] is True
    ])

    current_win_loss_total = current_wins + current_losses

    current_win_rate = (
        round((current_wins / current_win_loss_total) * 100, 1)
        if current_win_loss_total else 0
    )

    method_accuracy = (
        round((method_correct / current_wins) * 100, 1)
        if current_wins else 0
    )

    return {
        "total_picks": total_picks,
        "settled_count": len(settled_rows),
        "wins": wins,
        "losses": losses,
        "refunds": refunds,
        "pending": pending,
        "win_rate": win_rate,
        "total_profit_loss": total_profit_loss,
        "average_odds": average_odds,
        "bet_type_summary": build_bet_type_summary(rows),
        "odds_ranges": build_odds_range_summary(win_loss_rows),
        "top_events": build_event_summary(rows, reverse=True)[:5],
        "worst_events": build_event_summary(rows, reverse=False)[:5],
        "monthly_summary": build_monthly_summary(rows)[:12],
        "current_wins": current_wins,
        "current_losses": current_losses,
        "current_win_rate": current_win_rate,
        "method_correct": method_correct,
        "method_accuracy": method_accuracy,
    }


def build_bet_type_summary(rows):
    grouped = {}

    for row in rows:
        bet_type = row["bet_type"] or "Unknown"

        if bet_type not in grouped:
            grouped[bet_type] = {
                "bet_type": bet_type,
                "total": 0,
                "wins": 0,
                "losses": 0,
                "refunds": 0,
                "profit": Decimal("0.00"),
            }

        grouped[bet_type]["total"] += 1

        if row["outcome"] == "W":
            grouped[bet_type]["wins"] += 1

        if row["outcome"] == "L":
            grouped[bet_type]["losses"] += 1

        if row["outcome"] == "R":
            grouped[bet_type]["refunds"] += 1

        grouped[bet_type]["profit"] += row["profit_loss"] or Decimal("0.00")

    summary = []

    for data in grouped.values():
        decisions = data["wins"] + data["losses"]
        data["win_rate"] = round((data["wins"] / decisions) * 100, 1) if decisions else 0
        summary.append(data)

    return sorted(summary, key=lambda item: item["total"], reverse=True)


def build_event_summary(rows, reverse):
    grouped = {}

    for row in rows:
        event_name = row["event_name"] or "Unknown Event"

        if event_name not in grouped:
            grouped[event_name] = {
                "event_name": event_name,
                "total": 0,
                "wins": 0,
                "losses": 0,
                "profit": Decimal("0.00"),
            }

        grouped[event_name]["total"] += 1

        if row["outcome"] == "W":
            grouped[event_name]["wins"] += 1

        if row["outcome"] == "L":
            grouped[event_name]["losses"] += 1

        grouped[event_name]["profit"] += row["profit_loss"] or Decimal("0.00")

    return sorted(
        grouped.values(),
        key=lambda item: item["profit"],
        reverse=reverse,
    )


def build_monthly_summary(rows):
    grouped = {}

    for row in rows:
        if not row["date"]:
            continue

        month = row["date"].replace(day=1)

        if month not in grouped:
            grouped[month] = {
                "month": month,
                "total": 0,
                "wins": 0,
                "losses": 0,
                "refunds": 0,
                "profit": Decimal("0.00"),
            }

        grouped[month]["total"] += 1

        if row["outcome"] == "W":
            grouped[month]["wins"] += 1

        if row["outcome"] == "L":
            grouped[month]["losses"] += 1

        if row["outcome"] == "R":
            grouped[month]["refunds"] += 1

        grouped[month]["profit"] += row["profit_loss"] or Decimal("0.00")

    return sorted(
        grouped.values(),
        key=lambda item: item["month"],
        reverse=True,
    )


def build_odds_range_summary(rows):
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

    for row in rows:
        odds = row["odds"]

        if odds is None:
            continue

        if odds < Decimal("1.50"):
            label = "Under 1.50"
        elif odds < Decimal("2.00"):
            label = "1.50 to 1.99"
        elif odds < Decimal("3.00"):
            label = "2.00 to 2.99"
        else:
            label = "3.00+"

        buckets[label]["total"] += 1

        if row["outcome"] == "W":
            buckets[label]["wins"] += 1

        if row["outcome"] == "L":
            buckets[label]["losses"] += 1

        buckets[label]["profit"] += row["profit_loss"] or Decimal("0.00")

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

def register(request):
    if request.user.is_authenticated:
        return redirect("predictions:event_list")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect("predictions:event_list")
    else:
        form = UserCreationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form},
    )
