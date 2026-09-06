from django.contrib import admin
from .models import Fighter, Event, Fight, Prediction, Result, HistoricalPick, Bet, BetSelection
from .forms import PredictionAdminForm, ResultAdminForm

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
    form = PredictionAdminForm

    list_display = ("fight", "predicted_winner", "method", "confidence", "updated_at")
    search_fields = (
        "fight__fighter_a__first_name",
        "fight__fighter_a__last_name",
        "fight__fighter_b__first_name",
        "fight__fighter_b__last_name",
        "predicted_winner__first_name",
        "predicted_winner__last_name",
        "user__username",
    )
    list_filter = ("method", "confidence")

    autocomplete_fields = ("fight",)

    exclude = ("user",)

    class Media:
        js = ("predictions/js/prediction_admin.js",)

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    form = ResultAdminForm

    list_display = ("fight", "winner", "method", "round_finished")
    search_fields = (
        "fight__fighter_a__first_name",
        "fight__fighter_a__last_name",
        "fight__fighter_b__first_name",
        "fight__fighter_b__last_name",
        "winner__first_name",
        "winner__last_name",
    )
    list_filter = ("method",)

    autocomplete_fields = ("fight",)

    class Media:
        js = ("predictions/js/result_admin.js",)

@admin.register(HistoricalPick)
class HistoricalPickAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "user",
        "promotion",
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
    list_filter = ("user", "promotion", "outcome", "bet_type", "country", "date")
    readonly_fields = ("source_hash", "imported_at")

class BetSelectionInline(admin.TabularInline):
    model = BetSelection
    extra = 1
    autocomplete_fields = ("fight",)


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = (
        "placed_at",
        "user",
        "bet_type",
        "stake_units",
        "display_odds",
        "display_status",
        "display_profit_loss",
    )

    list_filter = (
        "bet_type",
        "placed_at",
    )

    search_fields = (
        "user__username",
        "selections__selection",
        "selections__fight__fighter_a__last_name",
        "selections__fight__fighter_b__last_name",
    )

    exclude = ("user",)

    inlines = [BetSelectionInline]

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user

        super().save_model(request, obj, form, change)

    @admin.display(description="Odds")
    def display_odds(self, obj):
        return obj.combined_odds() or "-"

    @admin.display(description="Status")
    def display_status(self, obj):
        return obj.status()

    @admin.display(description="P/L")
    def display_profit_loss(self, obj):
        value = obj.profit_loss()

        if value is None:
            return "-"

        return f"{value}u"


@admin.register(BetSelection)
class BetSelectionAdmin(admin.ModelAdmin):
    list_display = (
        "bet",
        "fight",
        "market",
        "selection",
        "odds",
        "outcome",
    )

    list_filter = (
        "market",
        "outcome",
    )

    autocomplete_fields = (
        "bet",
        "fight",
    )

    search_fields = (
        "selection",
        "fight__fighter_a__first_name",
        "fight__fighter_a__last_name",
        "fight__fighter_b__first_name",
        "fight__fighter_b__last_name",
    )
