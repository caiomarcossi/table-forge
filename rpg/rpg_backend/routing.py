from django.urls import path
from .consumers import HubConsumer, TableConsumer

websocket_urlpatterns=[
	path("ws/rpg/hub/", HubConsumer.as_asgi()),
	path("ws/rpg/table/<int:table_id>/", TableConsumer.as_asgi()),
]
