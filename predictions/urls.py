from django.urls import path
from . import views

app_name = "predictions"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
]
