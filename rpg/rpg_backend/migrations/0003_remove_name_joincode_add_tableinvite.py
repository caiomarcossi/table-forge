import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('rpg_backend', '0002_table'),
		migrations.swappable_dependency(settings.AUTH_USER_MODEL),
	]

	operations = [
		migrations.RemoveField(model_name='table', name='name'),
		migrations.RemoveField(model_name='table', name='join_code'),
		migrations.CreateModel(
			name='TableInvite',
			fields=[
				('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='rpg_backend.table')),
				('invited_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='table_invites', to=settings.AUTH_USER_MODEL)),
			],
			options={
				'unique_together': {('table', 'invited_user')},
			},
		),
	]
