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
		UserProfile.objects.create(user=instance)

class Table(models.Model):
	owner=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_tables")
	members=models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="tables", blank=True)
	is_private=models.BooleanField(default=False)
	created_at=models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"mesa de {self.owner.username}"

class FriendRequest(models.Model):
	sender=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_requests")
	receiver=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_requests")
	created_at=models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together=("sender", "receiver")

	def __str__(self):
		return f"{self.sender.username} → {self.receiver.username}"

class Friendship(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friendships")
	friend=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_of")
	created_at=models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together=("user", "friend")

	def __str__(self):
		return f"{self.user.username} ↔ {self.friend.username}"

class TableInvite(models.Model):
	table=models.ForeignKey(Table, on_delete=models.CASCADE, related_name="invites")
	invited_user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="table_invites")
	created_at=models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together=("table", "invited_user")

	def __str__(self):
		return f"{self.invited_user.username} → {self.table}"
