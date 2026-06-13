import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('rpg_backend', '0003_remove_name_joincode_add_tableinvite'),
		migrations.swappable_dependency(settings.AUTH_USER_MODEL),
	]

	operations = [
		migrations.CreateModel(
			name='FriendRequest',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_requests', to=settings.AUTH_USER_MODEL)),
				('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_requests', to=settings.AUTH_USER_MODEL)),
			],
			options={
				'unique_together': {('sender', 'receiver')},
			},
		),
		migrations.CreateModel(
			name='Friendship',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friendships', to=settings.AUTH_USER_MODEL)),
				('friend', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friend_of', to=settings.AUTH_USER_MODEL)),
			],
			options={
				'unique_together': {('user', 'friend')},
			},
		),
	]
