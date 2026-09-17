from django import forms
from decimal import Decimal

from .models import Fighter, Fight, Prediction, Result, Bet, BetSelection


class PredictionAdminForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fight_id = None

        if self.data.get("fight"):
            fight_id = self.data.get("fight")
        elif self.instance and self.instance.pk:
            fight_id = self.instance.fight_id

        if fight_id:
            try:
                fight = Fight.objects.get(pk=fight_id)
                self.fields["predicted_winner"].queryset = Fighter.objects.filter(
                    id__in=[
                        fight.fighter_a_id,
                        fight.fighter_b_id,
                    ]
                )
            except Fight.DoesNotExist:
                self.fields["predicted_winner"].queryset = Fighter.objects.none()
        else:
            self.fields["predicted_winner"].queryset = Fighter.objects.none()
            self.fields["predicted_winner"].help_text = "Select a fight first."

class ResultAdminForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fight_id = None

        if self.data.get("fight"):
            fight_id = self.data.get("fight")
        elif self.instance and self.instance.pk:
            fight_id = self.instance.fight_id

        if fight_id:
            try:
                fight = Fight.objects.get(pk=fight_id)
                self.fields["winner"].queryset = Fighter.objects.filter(
                    id__in=[
                        fight.fighter_a_id,
                        fight.fighter_b_id,
                    ]
                )
            except Fight.DoesNotExist:
                self.fields["winner"].queryset = Fighter.objects.none()
        else:
            self.fields["winner"].queryset = Fighter.objects.none()
            self.fields["winner"].help_text = "Select a fight first."

class BetForm(forms.ModelForm):
    class Meta:
        model = Bet
        fields = ["stake_units", "notes"]

        widgets = {
            "stake_units": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional notes about this bet...",
                }
            ),
        }

    def clean_stake_units(self):
        stake = self.cleaned_data["stake_units"]

        if stake <= Decimal("0"):
            raise forms.ValidationError(
                "Stake must be greater than 0 units."
            )

        return stake


class SingleBetSelectionForm(forms.ModelForm):
    fighter = forms.ModelChoiceField(
        queryset=Fighter.objects.none(),
        required=False,
        label="Fighter",
    )

    method_pick = forms.ChoiceField(
        choices=[
            ("", "---------"),
            ("KO_TKO", "KO/TKO"),
            ("SUB", "Submission"),
            ("DEC", "Decision"),
        ],
        required=False,
        label="Method",
    )

    distance_pick = forms.ChoiceField(
        choices=[
            ("", "---------"),
            ("YES", "Goes the Distance"),
            ("NO", "Does Not Go the Distance"),
        ],
        required=False,
        label="Distance",
    )

    class Meta:
        model = BetSelection

        fields = [
            "fight",
            "market",
            "fighter",
            "method_pick",
            "distance_pick",
            "odds",
        ]

        widgets = {
            "odds": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "1.01",
                    "placeholder": "e.g. 1.80",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fight_id = None

        if self.data.get("fight"):
            fight_id = self.data.get("fight")

        elif self.instance and self.instance.pk:
            fight_id = self.instance.fight_id

        if fight_id:
            try:
                fight = Fight.objects.get(pk=fight_id)

                self.fields["fighter"].queryset = Fighter.objects.filter(
                    id__in=[
                        fight.fighter_a_id,
                        fight.fighter_b_id,
                    ]
                )

            except (Fight.DoesNotExist, ValueError):
                self.fields["fighter"].queryset = Fighter.objects.none()

        else:
            self.fields["fighter"].queryset = Fighter.objects.none()

        # Populate our custom fields when editing an existing bet.
        if self.instance and self.instance.pk:
            if self.instance.selected_fighter_id:
                self.fields["fighter"].initial = self.instance.selected_fighter_id

            self.fields["method_pick"].initial = self.instance.method_selection
            self.fields["distance_pick"].initial = self.instance.distance_selection

    def clean_odds(self):
        odds = self.cleaned_data["odds"]

        if odds <= Decimal("1.00"):
            raise forms.ValidationError(
                "Decimal odds must be greater than 1.00."
            )

        return odds

    def clean(self):
        cleaned_data = super().clean()

        fight = cleaned_data.get("fight")
        market = cleaned_data.get("market")
        fighter = cleaned_data.get("fighter")
        method_pick = cleaned_data.get("method_pick")
        distance_pick = cleaned_data.get("distance_pick")

        if not fight:
            return cleaned_data

        if market == "MONEYLINE":
            if not fighter:
                self.add_error(
                    "fighter",
                    "Select the fighter you are backing."
                )

        elif market == "METHOD":
            if not fighter:
                self.add_error(
                    "fighter",
                    "Select the fighter you are backing."
                )

            if not method_pick:
                self.add_error(
                    "method_pick",
                    "Select a method of victory."
                )

        elif market == "DISTANCE":
            if not distance_pick:
                self.add_error(
                    "distance_pick",
                    "Select whether the fight goes the distance."
                )

        if fighter:
            valid_ids = [
                fight.fighter_a_id,
                fight.fighter_b_id,
            ]

            if fighter.id not in valid_ids:
                self.add_error(
                    "fighter",
                    "The selected fighter is not part of this fight."
                )

        return cleaned_data

class UserPredictionForm(forms.ModelForm):
    class Meta:
        model = Prediction

        fields = [
            "predicted_winner",
            "method",
            "confidence",
            "striking_notes",
            "grappling_notes",
            "cardio_notes",
            "durability_notes",
            "betting_notes",
            "final_reasoning",
        ]

        widgets = {
            "striking_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Striking matchup, range, power, defence...",
                }
            ),
            "grappling_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Wrestling, takedowns, submissions...",
                }
            ),
            "cardio_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Cardio and pace considerations...",
                }
            ),
            "durability_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Chin, damage history, toughness...",
                }
            ),
            "betting_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Odds, value, betting angles...",
                }
            ),
            "final_reasoning": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Summarise why you are making this prediction...",
                }
            ),
        }

    def __init__(self, *args, fight=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fight = fight

        if fight:
            self.fields["predicted_winner"].queryset = Fighter.objects.filter(
                id__in=[
                    fight.fighter_a_id,
                    fight.fighter_b_id,
                ]
            )
        else:
            self.fields["predicted_winner"].queryset = Fighter.objects.none()

    def clean_predicted_winner(self):
        predicted_winner = self.cleaned_data["predicted_winner"]

        if not self.fight:
            raise forms.ValidationError(
                "No fight has been selected."
            )

        valid_fighter_ids = [
            self.fight.fighter_a_id,
            self.fight.fighter_b_id,
        ]

        if predicted_winner.id not in valid_fighter_ids:
            raise forms.ValidationError(
                "You can only select a fighter taking part in this fight."
            )

        return predicted_winner
