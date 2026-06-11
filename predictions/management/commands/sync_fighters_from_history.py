import re

from django.core.management.base import BaseCommand

from predictions.models import Fighter, HistoricalPick


AUTO_CREATED_NOTE = "Created from historical picks import."


NON_FIGHTER_KEYWORDS = [
    "over",
    "under",
    "round",
    "rounds",
    "decision",
    "submission",
    "ko",
    "tko",
    "points",
    "double chance",
    "parlay",
    "acca",
    "method",
    "distance",
    "fight to go",
    "fight not to go",
]


def clean_name(name):
    if not name:
        return ""

    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)

    removable_bits = [
        "(C)",
        "TKO",
        "KO",
        "SUB",
        "DEC",
        "Decision",
        "Submission",
    ]

    for bit in removable_bits:
        name = name.replace(bit, "").strip()

    return name


def looks_like_fighter_name(value):
    value = clean_name(value)

    if not value:
        return False

    lower_value = value.lower()

    for keyword in NON_FIGHTER_KEYWORDS:
        if keyword in lower_value:
            return False

    # Require at least first name and surname.
    parts = value.split(" ")

    if len(parts) < 2:
        return False

    # Avoid importing things that are clearly not names.
    if any(char.isdigit() for char in value):
        return False

    return True


def split_person_name(full_name):
    full_name = clean_name(full_name)
    parts = full_name.split(" ")

    first_name = " ".join(parts[:-1])
    last_name = parts[-1]

    return first_name, last_name


def fighter_exists(full_name):
    full_name = clean_name(full_name).lower()

    for fighter in Fighter.objects.all():
        existing_name = f"{fighter.first_name} {fighter.last_name}".strip().lower()

        if existing_name == full_name:
            return True

    return False


def create_fighter(full_name):
    first_name, last_name = split_person_name(full_name)

    return Fighter.objects.create(
        first_name=first_name,
        last_name=last_name,
        stance="UNKNOWN",
        notes=AUTO_CREATED_NOTE,
    )


class Command(BaseCommand):
    help = "Create Fighter records from picked fighter names in historical picks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-auto-created",
            action="store_true",
            help="Delete fighters previously created by this import command before syncing again.",
        )

    def handle(self, *args, **options):
        if options["clear_auto_created"]:
            deleted_count, _ = Fighter.objects.filter(notes=AUTO_CREATED_NOTE).delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {deleted_count} previously auto-created fighters."
                )
            )

        picked_names = (
            HistoricalPick.objects
            .exclude(pick_name="")
            .values_list("pick_name", flat=True)
            .distinct()
        )

        created_count = 0
        skipped_count = 0
        ignored_count = 0

        for pick_name in picked_names:
            cleaned_pick_name = clean_name(pick_name)

            if not looks_like_fighter_name(cleaned_pick_name):
                ignored_count += 1
                continue

            if fighter_exists(cleaned_pick_name):
                skipped_count += 1
                continue

            create_fighter(cleaned_pick_name)
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Fighter sync complete. Created {created_count}. "
                f"Skipped {skipped_count}. Ignored {ignored_count} non-fighter picks."
            )
        )
