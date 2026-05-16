from django.urls import path
from . import views

urlpatterns = [
	path("", views.rpg_home, name="rpg_home"),
	path("login/", views.login_auto_language, name="login_auto"),
	path("signup/", views.signup_auto_language, name="signup_auto"),
	path("pt/login/", views.login_pt, name="login_pt"),
	path("pt/signup/", views.signup_pt, name="signup_pt"),
	path("en/login/", views.login_en, name="login_en"),
	path("en/signup/", views.signup_en, name="signup_en"),
]
