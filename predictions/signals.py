from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BetSelection, Result


def determine_selection_outcome(selection, result):
    # No Contest voids supported markets.
    if result.method == "NC":
        return "VOID"

    # -------------------------
    # FIGHT WINNER
    # -------------------------

    if selection.market == "MONEYLINE":
        if not result.winner_id:
            return "VOID"

        if selection.selected_fighter_id == result.winner_id:
            return "WON"

        return "LOST"

    # -------------------------
    # METHOD OF VICTORY
    # -------------------------

    if selection.market == "METHOD":
        if not result.winner_id:
            return "VOID"

        winner_correct = (
            selection.selected_fighter_id == result.winner_id
        )

        method_correct = (
            selection.method_selection == result.method
        )

        if winner_correct and method_correct:
            return "WON"

        return "LOST"

    # -------------------------
    # GOES THE DISTANCE
    # -------------------------

    if selection.market == "DISTANCE":
        went_distance = result.method == "DEC"

        if selection.distance_selection == "YES":
            return "WON" if went_distance else "LOST"

        if selection.distance_selection == "NO":
            return "LOST" if went_distance else "WON"

    # Unsupported markets stay pending.
    return "PENDING"


@receiver(post_save, sender=Result)
def settle_bets_from_result(sender, instance, **kwargs):
    selections = BetSelection.objects.filter(
        fight=instance.fight,
    )

    for selection in selections:
        new_outcome = determine_selection_outcome(
            selection,
            instance,
        )

        if (
            new_outcome != "PENDING"
            and selection.outcome != new_outcome
        ):
            BetSelection.objects.filter(
                pk=selection.pk
            ).update(
                outcome=new_outcome
            )


@receiver(post_save, sender=BetSelection)
def settle_new_bet_if_result_exists(
    sender,
    instance,
    created,
    **kwargs,
):
    try:
        result = instance.fight.result
    except Result.DoesNotExist:
        return

    new_outcome = determine_selection_outcome(
        instance,
        result,
    )

    if (
        new_outcome != "PENDING"
        and instance.outcome != new_outcome
    ):
        BetSelection.objects.filter(
            pk=instance.pk
        ).update(
            outcome=new_outcome
        )