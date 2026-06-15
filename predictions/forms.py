from django import forms

from .models import Fighter, Fight, Prediction, Result


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
