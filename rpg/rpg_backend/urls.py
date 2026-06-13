from django.urls import path
from . import views

urlpatterns = [
	path("sounds/<str:sound_id>/", views.sound_serve, name="sound_serve"),
]
