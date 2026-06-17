from django.urls import path
from .consumers import HubConsumer, TableConsumer

websocket_urlpatterns=[
	path("ws/rpg/hub/", HubConsumer.as_asgi()),
	path("ws/rpg/table/<str:table_token>/", TableConsumer.as_asgi()),
]
