from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "predictions"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("api/fights/<int:fight_id>/fighters/", views.fight_fighters_api, name="fight_fighters_api"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LoginView.as_view(),
        name="logout",
    ),
    path(
        "bets/",
        views.bet_list,
        name="bet_list"
    ),
    path(
        "bets/add/",
        views.add_bet,
        name="add_bet",
    ),
]