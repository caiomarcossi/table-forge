import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BaseJsonConsumer(AsyncWebsocketConsumer):
	async def send_json(self, data):
		await self.send(text_data=json.dumps(data, ensure_ascii=False))

	async def send_error_json(self, message):
		await self.send_json({"type": "error", "message": message})

	async def receive_json(self, text_data):
		try:
			return json.loads(text_data)
		except json.JSONDecodeError:
			await self.send_error_json("invalid_json")
			return None

class HubConsumer(BaseJsonConsumer):
	connected_dict={
		"type": "hub.connected",
		"message": "hub_connected",
		"actions": [
			"table.create",
			"table.join",
			"hub.exit",
		],
	}
	async def connect(self):
		self.user=self.scope["user"]
		if self.user.is_anonymous:
			await self.close()
			return
		await self.accept()
		await self.send_json(self.connected_dict)

	async def disconnect(self, close_code):
		pass

	async def receive(self, text_data=None, bytes_data=None):
		if text_data is None:
			return
		data=await self.receive_json(text_data)
		if data is None:
			return
		event=data.get("type")
		if event=="hub.exit":
			await self.close()
			return

		await self.send_error_json("hub_unknown_action")


