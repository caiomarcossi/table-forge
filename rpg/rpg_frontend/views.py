from django.shortcuts import redirect, render
from django.contrib.auth import login
from .forms import SignupForm

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
	return render(request, "rpg_frontend/login_pt.html")

def login_en(request):
	return render(request, "rpg_frontend/login_en.html")

def signup_pt(request):
	return signup_user(request, "pt")

def signup_en(request):
	return signup_user(request, "en")

def rpg_home(request):
	if request.user.is_authenticated:
		return render(request, "rpg_frontend/game_placeholder.html")
	return redirect("login_auto")

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
