from django.urls import path, re_path
from .consumers import HubConsumer

websocket_urlpatterns=[
path("ws/rpg/hub/", HubConsumer.as_asgi()),
#path("ws/rpg/tables/<int:table_id>/", TableConsumer.as_asgi()),
]
