import json
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.urls import reverse
from channels.generic.websocket import AsyncWebsocketConsumer
from .hub import get_hub_language, get_hub_payload_for_language, get_hub_texts_for_language, get_hub_actions_for_language
from .tables import get_table_texts_for_language, get_table_payload_for_language
from .social import get_social_texts_for_language, get_social_menu, get_friends_menu
from . import presence
from .sounds import (
	SOUND_TABLE_CREATED,
	SOUND_TABLE_JOINED,
	SOUND_TABLE_LEAVED,
	SOUND_CHAT_MESSAGE,
	SOUND_PRIVATE_MESSAGE,
	SOUND_PLAYER_CONNECTED,
	SOUND_PLAYER_DISCONNECTED,
)

User=get_user_model()
GLOBAL_PRESENCE_GROUP="global_presence"

@database_sync_to_async
def get_consumer_language(user):
	return get_hub_language(user)

@database_sync_to_async
def get_user_by_username(username):
	try:
		return User.objects.get(username=username)
	except User.DoesNotExist:
		return None

def parse_command(message, prefix):
	if not message.startswith(prefix+" "):
		return None
	rest=message[len(prefix)+1:].strip()
	return rest or None


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

	async def join_personal_group(self):
		self.personal_group=f"user_{self.user.id}"
		await self.channel_layer.group_add(self.personal_group, self.channel_name)

	async def leave_personal_group(self):
		await self.channel_layer.group_discard(self.personal_group, self.channel_name)

	async def join_global_presence(self, location, table_owner=None):
		presence.user_connected(self.user.id, self.user.username, location, table_owner)
		await self.channel_layer.group_add(GLOBAL_PRESENCE_GROUP, self.channel_name)
		await self.channel_layer.group_send(GLOBAL_PRESENCE_GROUP, {
			"type": "forward_json",
			"data": {
				"type": "player.connected",
				"username": self.user.username,
				"sound": SOUND_PLAYER_CONNECTED,
			},
		})

	async def leave_global_presence(self):
		presence.user_disconnected(self.user.id)
		await self.channel_layer.group_send(GLOBAL_PRESENCE_GROUP, {
			"type": "forward_json",
			"data": {
				"type": "player.disconnected",
				"username": self.user.username,
				"sound": SOUND_PLAYER_DISCONNECTED,
			},
		})
		await self.channel_layer.group_discard(GLOBAL_PRESENCE_GROUP, self.channel_name)

	async def forward_json(self, event):
		await self.send_json(event["data"])

	async def handle_private_message(self, raw_message, texts):
		rest=parse_command(raw_message, "/w")
		if rest is None:
			await self.send_json({"type": "hub.history", "message": texts["private_message_format"]})
			return
		parts=rest.split(" ", 1)
		if len(parts) < 2 or not parts[1].strip():
			await self.send_json({"type": "hub.history", "message": texts["private_message_format"]})
			return
		username, content=parts[0], parts[1]
		recipient=await get_user_by_username(username)
		if recipient is None:
			await self.send_json({"type": "hub.history", "message": texts["private_message_user_not_found"]})
			return
		await self.channel_layer.group_send(f"user_{recipient.id}", {
			"type": "forward_json",
			"data": {
				"type": "message.private",
				"message": texts["private_message_from"].format(username=self.user.username, message=content),
				"sound": SOUND_PRIVATE_MESSAGE,
			},
		})
		await self.send_json({
			"type": "hub.history",
			"message": texts["private_message_sent"].format(username=username, message=content),
		})


class HubConsumer(BaseJsonConsumer):
	async def connect(self):
		self.user=self.scope["user"]
		if self.user.is_anonymous:
			await self.close()
			return
		self.language=await get_consumer_language(self.user)
		await self.join_personal_group()
		await self.join_global_presence("hub")
		await self.accept()
		await self.send_json(get_hub_payload_for_language(self.language, reverse("logout")))

	async def disconnect(self, close_code):
		if hasattr(self, "personal_group"):
			await self.leave_personal_group()
		if hasattr(self, "user") and not self.user.is_anonymous:
			await self.leave_global_presence()

	async def send_friends_menu(self):
		count=await self.db_get_pending_requests_count()
		await self.send_json(get_friends_menu(self.language, count))

	async def receive(self, text_data=None, bytes_data=None):
		if text_data is None:
			return
		data=await self.receive_json(text_data)
		if data is None:
			return
		event=data.get("type")
		texts=get_hub_texts_for_language(self.language)

		if event=="hub.exit":
			await self.close()
			return

		if event=="hub.main":
			await self.send_json({
				"type": "hub.menu",
				"actions": get_hub_actions_for_language(self.language, reverse("logout")),
			})
			return

		if event=="table.create":
			table=await self.db_create_table()
			await self.send_json({
				"type": "table.created",
				"table_id": table.id,
				"message": texts["table_created"],
				"sound": SOUND_TABLE_CREATED,
			})
			return

		if event=="table.list":
			public, invited=await self.db_list_tables()
			tables=[]
			for t in public:
				tables.append({"id": t.id, "owner": t.owner.username, "label": texts["table_list_label"].format(owner=t.owner.username), "invited": False})
			for t in invited:
				tables.append({"id": t.id, "owner": t.owner.username, "label": texts["table_list_label_invited"].format(owner=t.owner.username), "invited": True})
			await self.send_json({
				"type": "hub.table_list",
				"tables": tables,
				"empty_message": texts["table_list_empty"],
				"cancel_label": texts["table_list_cancel"],
			})
			return

		if event=="table.join":
			table_id=data.get("table_id")
			if not table_id:
				return
			table, error=await self.db_join_table(table_id)
			if error:
				await self.send_json({"type": "hub.history", "message": texts["table_not_found"]})
				return
			await self.send_json({
				"type": "table.joined",
				"table_id": table.id,
				"owner": table.owner.username,
				"message": texts["table_joined"].format(owner=table.owner.username),
				"sound": SOUND_TABLE_JOINED,
			})
			return

		if event=="hub.chat":
			message=data.get("message", "").strip()
			if not message:
				return
			if message.startswith("/w "):
				await self.handle_private_message(message, texts)
			else:
				await self.send_json({"type": "hub.history", "message": texts["hub_chat_only_private"]})
			return

		if event=="social.open":
			await self.send_json(get_social_menu(self.language))
			return

		if event=="friends.open":
			await self.send_friends_menu()
			return

		if event=="friends.list":
			stexts=get_social_texts_for_language(self.language)
			friends=await self.db_get_friends_with_presence()
			if not friends:
				await self.send_json({"type": "hub.history", "message": stexts["no_friends"]})
			else:
				for f in friends:
					p=f["presence"]
					if p is None:
						line=stexts["friend_offline"].format(username=f["username"])
					elif p["location"]=="hub":
						line=stexts["friend_online_hub"].format(username=f["username"])
					else:
						line=stexts["friend_online_table"].format(username=f["username"], owner=p["table_owner"] or "")
					await self.send_json({"type": "hub.history", "message": line})
			await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
			return

		if event=="friends.add.open":
			stexts=get_social_texts_for_language(self.language)
			players=await self.db_get_online_for_add()
			if not players:
				await self.send_json({"type": "hub.history", "message": stexts["no_online_players"]})
				await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
				return
			actions=[]
			for p in players:
				if p["presence"]["location"]=="hub":
					label=stexts["add_player_hub"].format(username=p["username"])
				else:
					label=stexts["add_player_table"].format(username=p["username"], owner=p["presence"]["table_owner"] or "")
				actions.append({"type": "friends.add.request", "user_id": p["user_id"], "label": label})
			actions.append({"type": "friends.open", "label": stexts["friends_back_to_friends"]})
			await self.send_json({"type": "hub.menu", "actions": actions})
			return

		if event=="friends.add.request":
			stexts=get_social_texts_for_language(self.language)
			user_id=data.get("user_id")
			if not user_id:
				return
			target, error=await self.db_send_friend_request(user_id)
			if error=="not_found":
				await self.send_json({"type": "hub.history", "message": stexts["friend_not_found"]})
			elif error=="already_friends":
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_already_friends"].format(username=target.username)})
			elif error=="already_sent":
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_already_sent"].format(username=target.username)})
			else:
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_sent"].format(username=target.username)})
				await self.channel_layer.group_send(f"user_{target.id}", {
					"type": "forward_json",
					"data": {"type": "hub.history", "message": stexts["friend_request_received_notification"].format(username=self.user.username)},
				})
			await self.send_friends_menu()
			return

		if event=="friends.remove.open":
			stexts=get_social_texts_for_language(self.language)
			friends=await self.db_get_friends_for_remove()
			if not friends:
				await self.send_json({"type": "hub.history", "message": stexts["no_friends_to_remove"]})
				await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
				return
			actions=[{"type": "friends.remove.confirm", "user_id": f.friend.id, "label": stexts["remove_friend_label"].format(username=f.friend.username)} for f in friends]
			actions.append({"type": "friends.open", "label": stexts["friends_back_to_friends"]})
			await self.send_json({"type": "hub.menu", "actions": actions})
			return

		if event=="friends.remove.confirm":
			stexts=get_social_texts_for_language(self.language)
			user_id=data.get("user_id")
			if not user_id:
				return
			target, error=await self.db_remove_friend(user_id)
			if error:
				await self.send_json({"type": "hub.history", "message": stexts["friend_not_found"]})
			else:
				await self.send_json({"type": "hub.history", "message": stexts["friend_removed"].format(username=target.username)})
			await self.send_friends_menu()
			return

		if event=="friends.requests.open":
			stexts=get_social_texts_for_language(self.language)
			requests=await self.db_get_pending_requests()
			if not requests:
				await self.send_json({"type": "hub.history", "message": stexts["no_pending_requests"]})
				await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
				return
			actions=[]
			for req in requests:
				actions.append({"type": "friends.request.accept", "request_id": req.id, "label": stexts["accept_request_label"].format(username=req.sender.username)})
				actions.append({"type": "friends.request.decline", "request_id": req.id, "label": stexts["decline_request_label"].format(username=req.sender.username)})
			actions.append({"type": "friends.open", "label": stexts["friends_back_to_friends"]})
			await self.send_json({"type": "hub.menu", "actions": actions})
			return

		if event=="friends.request.accept":
			stexts=get_social_texts_for_language(self.language)
			request_id=data.get("request_id")
			if not request_id:
				return
			sender, error=await self.db_accept_request(request_id)
			if error:
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_not_found"]})
			else:
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_accepted"].format(username=sender.username)})
				await self.channel_layer.group_send(f"user_{sender.id}", {
					"type": "forward_json",
					"data": {"type": "hub.history", "message": stexts["friend_request_accepted_notification"].format(username=self.user.username)},
				})
			await self.send_friends_menu()
			return

		if event=="friends.request.decline":
			stexts=get_social_texts_for_language(self.language)
			request_id=data.get("request_id")
			if not request_id:
				return
			sender, error=await self.db_decline_request(request_id)
			if error:
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_not_found"]})
			else:
				await self.send_json({"type": "hub.history", "message": stexts["friend_request_declined"].format(username=sender.username)})
			await self.send_friends_menu()
			return

		await self.send_error_json("hub_unknown_action")

	@database_sync_to_async
	def db_create_table(self):
		from .models import Table
		table=Table.objects.create(owner=self.user)
		table.members.add(self.user)
		return table

	@database_sync_to_async
	def db_list_tables(self):
		from .models import Table, TableInvite
		public=list(Table.objects.filter(is_private=False).exclude(members=self.user).select_related("owner"))
		invited_ids=TableInvite.objects.filter(invited_user=self.user).values_list("table_id", flat=True)
		invited=list(Table.objects.filter(id__in=invited_ids, is_private=True).select_related("owner"))
		return public, invited

	@database_sync_to_async
	def db_join_table(self, table_id):
		from .models import Table, TableInvite
		try:
			table=Table.objects.select_related("owner").get(id=table_id)
		except Table.DoesNotExist:
			return None, "not_found"
		if table.is_private:
			invite=TableInvite.objects.filter(table=table, invited_user=self.user).first()
			if not invite:
				return None, "private"
			invite.delete()
		table.members.add(self.user)
		return table, None

	@database_sync_to_async
	def db_get_pending_requests_count(self):
		from .models import FriendRequest
		return FriendRequest.objects.filter(receiver=self.user).count()

	@database_sync_to_async
	def db_get_friends_with_presence(self):
		from .models import Friendship
		friendships=list(Friendship.objects.filter(user=self.user).select_related("friend"))
		return [{"username": f.friend.username, "presence": presence.get_user_presence(f.friend.id)} for f in friendships]

	@database_sync_to_async
	def db_get_online_for_add(self):
		from .models import Friendship, FriendRequest
		online=presence.get_online_excluding(self.user.id)
		if not online:
			return []
		friend_ids=set(Friendship.objects.filter(user=self.user).values_list("friend_id", flat=True))
		pending_ids=set(FriendRequest.objects.filter(sender=self.user).values_list("receiver_id", flat=True))
		return [
			{"user_id": uid, "username": data["username"], "presence": data}
			for uid, data in online.items()
			if uid not in friend_ids and uid not in pending_ids
		]

	@database_sync_to_async
	def db_send_friend_request(self, user_id):
		from .models import Friendship, FriendRequest
		try:
			target=User.objects.get(id=user_id)
		except User.DoesNotExist:
			return None, "not_found"
		if Friendship.objects.filter(user=self.user, friend=target).exists():
			return target, "already_friends"
		_, created=FriendRequest.objects.get_or_create(sender=self.user, receiver=target)
		if not created:
			return target, "already_sent"
		return target, None

	@database_sync_to_async
	def db_get_friends_for_remove(self):
		from .models import Friendship
		return list(Friendship.objects.filter(user=self.user).select_related("friend"))

	@database_sync_to_async
	def db_remove_friend(self, user_id):
		from .models import Friendship
		try:
			target=User.objects.get(id=user_id)
		except User.DoesNotExist:
			return None, "not_found"
		Friendship.objects.filter(user=self.user, friend=target).delete()
		Friendship.objects.filter(user=target, friend=self.user).delete()
		return target, None

	@database_sync_to_async
	def db_get_pending_requests(self):
		from .models import FriendRequest
		return list(FriendRequest.objects.filter(receiver=self.user).select_related("sender"))

	@database_sync_to_async
	def db_accept_request(self, request_id):
		from .models import FriendRequest, Friendship
		try:
			req=FriendRequest.objects.select_related("sender").get(id=request_id, receiver=self.user)
		except FriendRequest.DoesNotExist:
			return None, "not_found"
		sender=req.sender
		req.delete()
		Friendship.objects.get_or_create(user=self.user, friend=sender)
		Friendship.objects.get_or_create(user=sender, friend=self.user)
		return sender, None

	@database_sync_to_async
	def db_decline_request(self, request_id):
		from .models import FriendRequest
		try:
			req=FriendRequest.objects.select_related("sender").get(id=request_id, receiver=self.user)
		except FriendRequest.DoesNotExist:
			return None, "not_found"
		sender=req.sender
		req.delete()
		return sender, None


class TableConsumer(BaseJsonConsumer):
	async def connect(self):
		self.user=self.scope["user"]
		if self.user.is_anonymous:
			await self.close()
			return
		self.table_id=self.scope["url_route"]["kwargs"]["table_id"]
		table=await self.db_get_table()
		if table is None:
			await self.close()
			return
		self.owner_username=table.owner.username
		self.is_private=table.is_private
		self.language=await get_consumer_language(self.user)
		self.table_group=f"table_{self.table_id}"
		await self.channel_layer.group_add(self.table_group, self.channel_name)
		await self.join_personal_group()
		await self.join_global_presence("table", table_owner=self.owner_username)
		await self.accept()
		await self.send_json(get_table_payload_for_language(
			self.language, self.table_id, self.owner_username, self.is_private, reverse("rpg_home")
		))

	async def disconnect(self, close_code):
		if hasattr(self, "table_group"):
			texts=get_table_texts_for_language(self.language)
			await self.channel_layer.group_send(self.table_group, {
				"type": "forward_json",
				"data": {
					"type": "player.left",
					"username": self.user.username,
					"message": texts["player_left"].format(username=self.user.username),
					"sound": SOUND_TABLE_LEAVED,
				},
			})
			await self.channel_layer.group_discard(self.table_group, self.channel_name)
		if hasattr(self, "personal_group"):
			await self.leave_personal_group()
		if hasattr(self, "user") and not self.user.is_anonymous:
			await self.leave_global_presence()

	async def receive(self, text_data=None, bytes_data=None):
		if text_data is None:
			return
		data=await self.receive_json(text_data)
		if data is None:
			return
		event=data.get("type")
		texts=get_table_texts_for_language(self.language)

		if event=="table.leave":
			await self.close()
			return

		if event=="chat.send":
			message=data.get("message", "").strip()
			if not message:
				return
			if message.startswith("/w "):
				await self.handle_private_message(message, texts)
				return
			if message.startswith("/invite "):
				username=parse_command(message, "/invite")
				if username:
					await self.send_invite(username, texts)
				else:
					await self.send_json({"type": "hub.history", "message": texts["invite_format"]})
				return
			await self.channel_layer.group_send(self.table_group, {
				"type": "forward_json",
				"data": {
					"type": "chat.message",
					"message": texts["chat_message"].format(username=self.user.username, message=message),
					"sound": SOUND_CHAT_MESSAGE,
				},
			})
			return

		if event=="table.invite":
			await self.send_json({"type": "hub.input", "prompt": texts["invite_prompt"], "action": "table.invite.confirm"})
			return

		if event=="table.invite.confirm":
			username=data.get("value", "").strip()
			if username:
				await self.send_invite(username, texts)
			else:
				await self.send_json({"type": "hub.history", "message": texts["invite_format"]})
			return

		await self.send_error_json("table_unknown_action")

	async def send_invite(self, username, texts):
		recipient, error=await self.db_invite_user(username)
		if error=="not_found":
			await self.send_json({"type": "hub.history", "message": texts["invite_user_not_found"]})
			return
		await self.channel_layer.group_send(f"user_{recipient.id}", {
			"type": "forward_json",
			"data": {"type": "hub.history", "message": texts["invite_received"].format(owner=self.user.username)},
		})
		await self.send_json({"type": "hub.history", "message": texts["invite_sent"].format(username=username)})

	@database_sync_to_async
	def db_get_table(self):
		from .models import Table
		try:
			return Table.objects.select_related("owner").get(id=self.table_id, members=self.user)
		except Table.DoesNotExist:
			return None

	@database_sync_to_async
	def db_invite_user(self, username):
		from .models import Table, TableInvite
		try:
			recipient=User.objects.get(username=username)
		except User.DoesNotExist:
			return None, "not_found"
		table=Table.objects.get(id=self.table_id)
		TableInvite.objects.get_or_create(table=table, invited_user=recipient)
		return recipient, None
