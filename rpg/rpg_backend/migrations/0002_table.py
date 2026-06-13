import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('rpg_backend', '0001_initial'),
		migrations.swappable_dependency(settings.AUTH_USER_MODEL),
	]

	operations = [
		migrations.CreateModel(
			name='Table',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('name', models.CharField(max_length=100)),
				('is_private', models.BooleanField(default=False)),
				('join_code', models.CharField(default='', max_length=8, unique=True)),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_tables', to=settings.AUTH_USER_MODEL)),
				('members', models.ManyToManyField(blank=True, related_name='tables', to=settings.AUTH_USER_MODEL)),
			],
		),
	]
