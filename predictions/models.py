from django.db import models
from django.conf import settings
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

    def __str__(self):
        return f"{self.fighter_a} vs {self.fighter_b}"


class Prediction(models.Model):
    METHOD_CHOICES = [
        ("KO_TKO", "KO/TKO"),
        ("SUB", "Submission"),
        ("DEC", "Decision"),
    ]

    CONFIDENCE_CHOICES = [
        (0, "£0 - Wouldn't bet"),
        (250, "£2.50 - Fun/value bet"),
        (500, "£5 - Solid bet"),
        (1000, "£10 - Very confident"),
    ]

    fight = models.OneToOneField(Fight, on_delete=models.CASCADE, related_name="prediction")
    predicted_winner = models.ForeignKey(Fighter, on_delete=models.CASCADE, related_name="predictions")

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    confidence = models.PositiveIntegerField(choices=CONFIDENCE_CHOICES, default=0)

    striking_notes = models.TextField(blank=True)
    grappling_notes = models.TextField(blank=True)
    cardio_notes = models.TextField(blank=True)
    durability_notes = models.TextField(blank=True)
    betting_notes = models.TextField(blank=True)
    final_reasoning = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def confidence_display(self):
        return dict(self.CONFIDENCE_CHOICES).get(self.confidence, "Unknown")

    def __str__(self):
        return f"{self.predicted_winner} by {self.get_method_display()}"


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

    def prediction_correct(self):
        if not hasattr(self.fight, "prediction"):
            return False
        return self.fight.prediction.predicted_winner == self.winner

    def method_correct(self):
        if not hasattr(self.fight, "prediction"):
            return False
        return self.fight.prediction.method == self.method

    def __str__(self):
        return f"{self.fight} result"
