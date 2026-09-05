from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class Fighter(models.Model):
    STANCE_CHOICES = [
        ("ORTHODOX", "Orthodox"),
        ("SOUTHPAW", "Southpaw"),
        ("SWITCH", "Switch"),
        ("UNKNOWN", "Unknown"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=100, blank=True)

    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)

    age = models.PositiveIntegerField(null=True, blank=True)
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    reach_cm = models.PositiveIntegerField(null=True, blank=True)
    stance = models.CharField(max_length=20, choices=STANCE_CHOICES, default="UNKNOWN")

    team = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    ko_wins = models.PositiveIntegerField(default=0)
    sub_wins = models.PositiveIntegerField(default=0)
    dec_wins = models.PositiveIntegerField(default=0)

    ko_losses = models.PositiveIntegerField(default=0)
    sub_losses = models.PositiveIntegerField(default=0)
    dec_losses = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Event(models.Model):
    STATUS_CHOICES = [
        ("UPCOMING", "Upcoming"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    promotion = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UPCOMING")

    def __str__(self):
        return f"{self.promotion}: {self.name}"


class Fight(models.Model):
    WEIGHT_CLASS_CHOICES = [
        ("FLW", "Flyweight"),
        ("BW", "Bantamweight"),
        ("FW", "Featherweight"),
        ("LW", "Lightweight"),
        ("WW", "Welterweight"),
        ("MW", "Middleweight"),
        ("LHW", "Light Heavyweight"),
        ("HW", "Heavyweight"),
        ("WFLW", "Women's Flyweight"),
        ("WBW", "Women's Bantamweight"),
        ("WSW", "Women's Strawweight"),
        ("OTHER", "Other"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="fights")
    fighter_a = models.ForeignKey(Fighter, on_delete=models.CASCADE, related_name="fights_as_a")
    fighter_b = models.ForeignKey(Fighter, on_delete=models.CASCADE, related_name="fights_as_b")

    weight_class = models.CharField(max_length=20, choices=WEIGHT_CLASS_CHOICES, default="OTHER")
    fight_order = models.PositiveIntegerField(default=1)

    fighter_a_odds = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fighter_b_odds = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["event", "fight_order"]

    def clean(self):
        if self.fighter_a_id and self.fighter_b_id and self.fighter_a_id == self.fighter_b_id:
            raise ValidationError("A fighter cannot fight themselves.")

    def __str__(self):
        return f"{self.fighter_a} vs {self.fighter_b}"


class Prediction(models.Model):
    METHOD_CHOICES = [
        ("KO_TKO", "KO/TKO"),
        ("SUB", "Submission"),
        ("DEC", "Decision"),
    ]

    CONFIDENCE_CHOICES = [
        (0, "No confidence / would not pick"),
        (250, "Low confidence / value angle"),
        (500, "Medium confidence"),
        (1000, "High confidence"),
    ]

    fight = models.ForeignKey(Fight, on_delete=models.CASCADE, related_name="prediction")
    predicted_winner = models.ForeignKey(Fighter, on_delete=models.CASCADE, related_name="predictions")

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    confidence = models.PositiveIntegerField(choices=CONFIDENCE_CHOICES, default=0)

    striking_notes = models.TextField(blank=True)
    grappling_notes = models.TextField(blank=True)
    cardio_notes = models.TextField(blank=True)
    durability_notes = models.TextField(blank=True)
    betting_notes = models.TextField(blank=True)
    final_reasoning = models.TextField(blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="predictions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def confidence_display(self):
        return dict(self.CONFIDENCE_CHOICES).get(self.confidence, "Unknown")

    def clean(self):
        if not self.fight_id or not self.predicted_winner_id:
            return

        valid_fighter_ids = [
            self.fight.fighter_a_id,
            self.fight.fighter_b_id,
        ]

        if self.predicted_winner_id not in valid_fighter_ids:
            raise ValidationError(
                "Predicted winner must be one of the two fighters in this fight."
            )

    def __str__(self):
        return f"{self.predicted_winner} by {self.get_method_display()}"

    def stake_amount(self):
        return Decimal("1.00")

    def predicted_odds(self):
        if not self.fight_id or not self.predicted_winner_id:
            return None

        if self.predicted_winner_id == self.fight.fighter_a_id:
            return self.fight.fighter_a_odds

        if self.predicted_winner_id == self.fight.fighter_b_id:
            return self.fight.fighter_b_odds

        return None

    def result_status(self):
        if not hasattr(self.fight, "result"):
            return "P"

        result = self.fight.result

        if result.method == "NC":
            return "R"

        if not result.winner_id:
            return "R"

        if result.winner_id == self.predicted_winner_id:
            return "W"

        return "L"

    def is_pick_correct(self):
        return self.result_status() == "W"

    def is_method_correct(self):
        if self.result_status() != "W":
            return False

        if not hasattr(self.fight, "result"):
            return False

        return self.method == self.fight.result.method

    def profit_loss(self):
        outcome = self.result_status()
        stake = self.stake_amount()
        odds = self.predicted_odds()

        if outcome == "P":
            return None

        if outcome == "R":
            return Decimal("0.00")

        if outcome == "L":
            return -stake

        if outcome == "W":
            if odds is None:
                return None

            return (stake * (odds - Decimal("1.00"))).quantize(Decimal("0.01"))

        return None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "fight"],
                name="unique_user_prediction_per_fight",
            )
        ]

class Result(models.Model):
    METHOD_CHOICES = [
        ("KO_TKO", "KO/TKO"),
        ("SUB", "Submission"),
        ("DEC", "Decision"),
        ("DQ", "Disqualification"),
        ("NC", "No Contest"),
    ]

    fight = models.OneToOneField(Fight, on_delete=models.CASCADE, related_name="result")
    winner = models.ForeignKey(Fighter, on_delete=models.SET_NULL, null=True, blank=True)

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    round_finished = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    notes = models.TextField(blank=True)

    def clean(self):
        if not self.fight_id or not self.winner_id:
            return

        valid_fighter_ids = [
            self.fight.fighter_a_id,
            self.fight.fighter_b_id,
        ]

        if self.winner_id not in valid_fighter_ids:
            raise ValidationError(
                "Result winner must be one of the two fighters in this fight."
            )

    def prediction_correct_for(self, prediction):
        return prediction.predicted_winner_id == self.winner_id

    def method_correct(self, prediction):
        return (
            prediction.predicted_winner_id == self.winner_id
            and prediction.method == self.method
        )

    def __str__(self):
        return f"{self.fight} result"

class HistoricalPick(models.Model):
    OUTCOME_CHOICES = [
        ("W", "Win"),
        ("L", "Loss"),
        ("R", "Refund/Void"),
        ("P", "Pending"),
        ("U", "Unknown"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="historical_picks",
    )

    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)

    promotion = models.CharField(max_length=100, default="UFC")
    country = models.CharField(max_length=100, blank=True)
    event_name = models.CharField(max_length=200)
    fight_name = models.CharField(max_length=200)
    pick_name = models.CharField(max_length=200)
    bet_type = models.CharField(max_length=100, blank=True)

    stake = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    odds = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    outcome = models.CharField(max_length=1, choices=OUTCOME_CHOICES, default="U")

    profit_loss = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    sheet_total_profit_loss = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)

    source_row = models.PositiveIntegerField(null=True, blank=True)
    source_hash = models.CharField(max_length=64)

    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["event_name"]),
            models.Index(fields=["pick_name"]),
            models.Index(fields=["outcome"]),
            models.Index(fields=["date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "source_hash"],
                name="unique_user_historical_source_hash",
            )
        ]

    def is_win(self):
        return self.outcome == "W"

    def is_loss(self):
        return self.outcome == "L"

    def is_refund(self):
        return self.outcome == "R"

    def is_settled(self):
        return self.outcome in ["W", "L", "R"]

    def __str__(self):
        return f"{self.event_name} - {self.pick_name} ({self.get_outcome_display()})"
