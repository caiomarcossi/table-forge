from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
	gender_choices=[
		("not_informed", "gender_not_informed"),
		("male", "gender_male"),
		("female", "gender_female"),
		("other", "gender_other"),
	]

	language_choices=[
		("pt-BR", "language_pt_br"),
		("en", "language_en"),
	]
	user=models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	full_name=models.CharField(max_length=150, blank=True)
	gender=models.CharField(max_length=20, choices=gender_choices, default="not_informed")
	birth_date=models.DateField(null=True, blank=True)
	default_language=models.CharField(max_length=10, choices=language_choices, default="pt-BR")
	created_at=models.DateTimeField(auto_now_add=True)
	updated_at=models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.full_name or self.user.username

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		UserProfile.objects.create(user=instance, )
