from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BetSelection, Result


def get_moneyline_outcome(selection, result):
    if result.method == "NC" or not result.winner_id:
        return "VOID"

    if selection.selected_fighter_id == result.winner_id:
        return "WON"

    return "LOST"


@receiver(post_save, sender=Result)
def settle_moneyline_bets_from_result(sender, instance, **kwargs):
    selections = BetSelection.objects.filter(
        fight=instance.fight,
        market="MONEYLINE",
    )

    for selection in selections:
        new_outcome = get_moneyline_outcome(
            selection,
            instance,
        )

        if selection.outcome != new_outcome:
            BetSelection.objects.filter(
                pk=selection.pk
            ).update(
                outcome=new_outcome
            )


@receiver(post_save, sender=BetSelection)
def settle_new_moneyline_bet(sender, instance, created, **kwargs):
    if instance.market != "MONEYLINE":
        return

    if not instance.selected_fighter_id:
        return

    try:
        result = instance.fight.result
    except Result.DoesNotExist:
        return

    new_outcome = get_moneyline_outcome(
        instance,
        result,
    )

    if instance.outcome != new_outcome:
        BetSelection.objects.filter(
            pk=instance.pk
        ).update(
            outcome=new_outcome
        )