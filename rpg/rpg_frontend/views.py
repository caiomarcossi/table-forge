from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from rpg_backend.models import Table
from rpg_backend.hub import get_hub_texts_for_language
from .forms import SignupForm, LoginForm

def browser_prefers_portuguese(request):
	accept_language=request.headers.get("Accept-Language", "").lower()
	return (
		"pt-br" in accept_language
		or "pt-pt" in accept_language
		or accept_language.startswith("pt")
	)

def login_auto_language(request):
	if(browser_prefers_portuguese(request)):
		return redirect("login_pt")
	return redirect("login_en")

def signup_auto_language(request):
	if(browser_prefers_portuguese(request)):
		return redirect("signup_pt")
	return redirect("signup_en")

def login_pt(request):
	return login_user(request, "pt")

def login_en(request):
	return login_user(request, "en")

def signup_pt(request):
	return signup_user(request, "pt")

def signup_en(request):
	return signup_user(request, "en")

def rpg_home(request):
	if not request.user.is_authenticated:
		return redirect("login_auto")
	language="pt-BR"
	if hasattr(request.user, "profile"):
		language=request.user.profile.default_language
	initial_table_token=request.session.get("current_table_token")
	if initial_table_token and not Table.objects.filter(token=initial_table_token, members=request.user).exists():
		del request.session["current_table_token"]
		initial_table_token=None
	ui=get_hub_texts_for_language(language)
	return render(request, "rpg_frontend/hub.html", {
		"language": language,
		"page_title": "Table Forge",
		"initial_table_token": initial_table_token,
		"ui_history_title": ui["ui_history_title"],
		"ui_game_title": ui["ui_game_title"],
		"ui_actions_title": ui["ui_actions_title"],
		"ui_chat_label": ui["ui_chat_label"],
		"ui_send_button": ui["ui_send_button"],
	})

def signup_user(request, language):
	template_name="rpg_frontend/signup_pt.html"
	if language=="en":
		template_name="rpg_frontend/signup_en.html"
	if request.method=="POST":
		form=SignupForm(request.POST)
		if form.is_valid():
			user=form.save(language=language)
			login(request, user)
			return redirect("rpg_home")
		return render(request, template_name, {"form": form})
	form=SignupForm()
	return render(request, template_name, {"form": form})

def logout_user(request):
	logout(request)
	return redirect("rpg_home")

def login_user(request, language):
	template_name="rpg_frontend/login_pt.html"
	if language=="en":
		template_name="rpg_frontend/login_en.html"
	if request.user.is_authenticated:
		return redirect("rpg_home")
	if request.method=="POST":
		form=LoginForm(request.POST, request=request)
		if form.is_valid():
			login(request, form.get_user())
			return redirect("rpg_home")
		return render(request, template_name, {"form": form})
	form=LoginForm()
	return render(request, template_name, {"form": form})
