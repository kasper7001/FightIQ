from django.contrib import admin
from .models import Fighter, Event, Fight, Prediction, Result


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
    search_fields = ("fighter_a__first_name", "fighter_a__last_name", "fighter_b__first_name", "fighter_b__last_name")
    list_filter = ("event", "weight_class")


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("fight", "predicted_winner", "method", "confidence", "updated_at")
    search_fields = ("fight__fighter_a__last_name", "fight__fighter_b__last_name", "predicted_winner__last_name")
    list_filter = ("method", "confidence")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("fight", "winner", "method", "round_finished")
    search_fields = ("fight__fighter_a__last_name", "fight__fighter_b__last_name", "winner__last_name")
    list_filter = ("method",)
