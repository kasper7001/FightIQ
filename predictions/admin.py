from django.contrib import admin
from .models import Fighter, Event, Fight, Prediction, Result, HistoricalPick


@admin.register(Fighter)
class FighterAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "wins", "losses", "draws", "age", "stance")
    search_fields = ("first_name", "last_name", "nickname", "team")
    list_filter = ("stance",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("promotion", "name", "date", "location", "status")
    search_fields = ("promotion", "name", "location")
    list_filter = ("promotion", "status", "date")


@admin.register(Fight)
class FightAdmin(admin.ModelAdmin):
    list_display = ("event", "fight_order", "fighter_a", "fighter_b", "weight_class")
    search_fields = (
        "fighter_a__first_name",
        "fighter_a__last_name",
        "fighter_b__first_name",
        "fighter_b__last_name",
    )
    list_filter = ("event", "weight_class")
    autocomplete_fields = ("event", "fighter_a", "fighter_b")

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("fight", "predicted_winner", "method", "confidence", "updated_at")
    search_fields = (
        "fight__fighter_a__first_name",
        "fight__fighter_a__last_name",
        "fight__fighter_b__first_name",
        "fight__fighter_b__last_name",
        "predicted_winner__first_name",
        "predicted_winner__last_name",
    )
    list_filter = ("method", "confidence")
    autocomplete_fields = ("fight", "predicted_winner")

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("fight", "winner", "method", "round_finished")
    search_fields = ("fight__fighter_a__last_name", "fight__fighter_b__last_name", "winner__last_name")
    list_filter = ("method",)

@admin.register(HistoricalPick)
class HistoricalPickAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "event_name",
        "fight_name",
        "pick_name",
        "bet_type",
        "stake",
        "odds",
        "outcome",
        "profit_loss",
    )
    search_fields = ("event_name", "fight_name", "pick_name", "bet_type")
    list_filter = ("outcome", "bet_type", "country", "date")
    readonly_fields = ("source_hash", "imported_at")
