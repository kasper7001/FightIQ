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
        label="Selection",
        help_text="Select a fight first.",
    )

    class Meta:
        model = BetSelection
        fields = ["fight", "fighter", "odds"]

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
        fighter = cleaned_data.get("fighter")

        if fight and fighter:
            valid_ids = [
                fight.fighter_a_id,
                fight.fighter_b_id,
            ]

            if fighter.id not in valid_ids:
                self.add_error(
                    "fighter",
                    "The selected fighter is not part of this fight.",
                )

        return cleaned_data
