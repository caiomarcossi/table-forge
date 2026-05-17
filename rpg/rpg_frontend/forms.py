import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class SignupForm(forms.Form):
	username=forms.CharField(max_length=150)
	email=forms.EmailField()
	password=forms.CharField(widget=forms.PasswordInput)
	password_confirm=forms.CharField(widget=forms.PasswordInput)

	def clean_email(self):
		email=self.cleaned_data["email"].strip().lower()
		if User.objects.filter(email=email).exists():
			raise forms.ValidationError("email_already_exists")
		return email

	def clean_username(self):
		username=self.cleaned_data["username"].strip()
		if User.objects.filter(username=username).exists():
			raise forms.ValidationError("username_already_exists")
		return username

	def clean_password(self):
		password=self.cleaned_data["password"]
		if len(password)<8:
			raise forms.ValidationError("password_too_short")
		if not re.search(r"[A-Z]", password):
			raise forms.ValidationError("password_missing_uppercase")
		if not re.search(r"[a-z]", password):
			raise forms.ValidationError("password_missing_lowercase")
		if not re.search(r"[0-9]", password):
			raise forms.ValidationError("password_missing_number")
		if not re.search(r"[^\w\s]", password):
			raise forms.ValidationError("password_missing_special_character")

		return password

	def clean(self):
		cleaned_data=super().clean()
		password=cleaned_data.get("password")
		password_confirm=cleaned_data.get("password_confirm")
		if password and password_confirm and password!=password_confirm:
			raise forms.ValidationError("passwords_do_not_match")
		return cleaned_data

	def save(self, language):
		user=User.objects.create_user(username=self.cleaned_data["username"], email=self.cleaned_data["email"], password=self.cleaned_data["password"])
		user.profile.default_language="pt-BR" if language=="pt" else "en"
		user.profile.save()
		return user

class LoginForm(forms.Form):
	username=forms.CharField(max_length=150)
	password=forms.CharField(widget=forms.PasswordInput)

	def __init__(self, *args, request=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.request=request
		self.user=None

	def clean(self):
		cleaned_data=super().clean()
		username=cleaned_data.get("username")
		password=cleaned_data.get("password")
		if username and password:
			self.user=authenticate(self.request, username=username, password=password)
			if self.user is None:
				raise forms.ValidationError("invalid_login")
		return cleaned_data

	def get_user(self):
		return self.user
