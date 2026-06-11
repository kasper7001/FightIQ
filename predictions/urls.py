from django.urls import path
from . import views

app_name = "predictions"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("api/fights/<int:fight_id>/fighters/", views.fight_fighters_api, name="fight_fighters_api"),
]
