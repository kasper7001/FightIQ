from django.core.management.base import BaseCommand

from predictions.models import BetSelection, Result


class Command(BaseCommand):
    help = "Settle existing pending moneyline bets where a fight result already exists."

    def handle(self, *args, **options):
        updated = 0
        skipped = 0

        selections = BetSelection.objects.filter(
            market="MONEYLINE",
            outcome="PENDING",
        ).select_related(
            "fight",
            "fight__result",
            "selected_fighter",
        )

        for selection in selections:
            try:
                result = selection.fight.result
            except Result.DoesNotExist:
                skipped += 1
                continue

            if result.method == "NC" or not result.winner_id:
                new_outcome = "VOID"
            elif selection.selected_fighter_id == result.winner_id:
                new_outcome = "WON"
            else:
                new_outcome = "LOST"

            if selection.outcome != new_outcome:
                selection.outcome = new_outcome
                selection.save(update_fields=["outcome"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Settlement complete. Updated {updated} bets. "
                f"Skipped {skipped} bets without results."
            )
        )