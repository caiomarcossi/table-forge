import json
import uuid
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from channels.generic.websocket import AsyncWebsocketConsumer
from .hub import get_hub_language, get_hub_payload_for_language, get_hub_texts_for_language, get_hub_actions_for_language
from .tables import get_table_texts_for_language, get_table_payload_for_language
from .social import get_social_texts_for_language, get_social_menu, get_friends_menu
from . import presence
from . import game
from .sounds import (
	SOUND_TABLE_CREATED,
	SOUND_TABLE_JOINED,
	SOUND_TABLE_LEAVED,
	SOUND_CHAT_MESSAGE,
	SOUND_PRIVATE_MESSAGE,
	SOUND_PLAYER_CONNECTED,
	SOUND_PLAYER_DISCONNECTED,
	SOUND_DICE_ROLL,
	SOUND_COIN_FLIP,
)

User=get_user_model()

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
		await presence.user_connected(self.user.id, self.user.username, location, table_owner)
		friend_ids=await self.db_get_friend_ids()
		for friend_id in friend_ids:
			await self.channel_layer.group_send(f"user_{friend_id}", {
				"type": "forward_json",
				"data": {
					"type": "player.connected",
					"username": self.user.username,
					"sound": SOUND_PLAYER_CONNECTED,
				},
			})

	async def leave_global_presence(self):
		await presence.user_disconnected(self.user.id)
		friend_ids=await self.db_get_friend_ids()
		for friend_id in friend_ids:
			await self.channel_layer.group_send(f"user_{friend_id}", {
				"type": "forward_json",
				"data": {
					"type": "player.disconnected",
					"username": self.user.username,
					"sound": SOUND_PLAYER_DISCONNECTED,
				},
			})

	async def forward_json(self, event):
		await self.send_json(event["data"])

	@database_sync_to_async
	def set_session_table_token(self, token):
		self.scope["session"]["current_table_token"]=token
		self.scope["session"].save()

	@database_sync_to_async
	def clear_session_table_token(self):
		if "current_table_token" in self.scope["session"]:
			del self.scope["session"]["current_table_token"]
			self.scope["session"].save()

	async def handle_private_message(self, raw_message, texts):
		rest=raw_message[1:]
		if rest.startswith("@"):
			content=rest[1:].strip()
			target=getattr(self, "last_pm_target", None)
			if not target:
				await self.send_json({"type": "hub.history", "message": texts["private_no_target"]})
				return
		elif not rest or rest[0]==" ":
			content=rest.strip()
			target=getattr(self, "last_pm_sender", None)
			if not target:
				await self.send_json({"type": "hub.history", "message": texts["private_no_sender"]})
				return
		else:
			parts=rest.split(" ", 1)
			target=parts[0]
			content=parts[1].strip() if len(parts)>1 else ""
			if not content:
				await self.send_json({"type": "hub.history", "message": texts["private_message_format"]})
				return
			self.last_pm_target=target
		if not content:
			await self.send_json({"type": "hub.history", "message": texts["private_message_format"]})
			return
		recipient=await get_user_by_username(target)
		if recipient is None:
			await self.send_json({"type": "hub.history", "message": texts["private_message_user_not_found"]})
			return
		await self.channel_layer.group_send(f"user_{recipient.id}", {
			"type": "receive.private.message",
			"from_username": self.user.username,
			"message": content,
		})
		await self.send_json({
			"type": "hub.history",
			"message": texts["private_message_sent"].format(username=target, message=content),
		})

	async def receive_private_message(self, event):
		self.last_pm_sender=event["from_username"]
		texts=get_hub_texts_for_language(self.language)
		await self.send_json({
			"type": "message.private",
			"message": texts["private_message_from"].format(username=event["from_username"], message=event["message"]),
			"sound": SOUND_PRIVATE_MESSAGE,
		})


	@database_sync_to_async
	def db_get_friend_ids(self):
		from .models import Friendship
		return list(Friendship.objects.filter(user=self.user).values_list("friend_id", flat=True))


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
				"table_token": str(table.token),
				"message": texts["table_created"],
				"sound": SOUND_TABLE_CREATED,
			})
			return

		if event=="table.list":
			public, invited=await self.db_list_tables()
			tables=[]
			for t in public:
				tables.append({"token": str(t.token), "owner": t.owner.username, "label": texts["table_list_label"].format(owner=t.owner.username), "invited": False})
			for t in invited:
				tables.append({"token": str(t.token), "owner": t.owner.username, "label": texts["table_list_label_invited"].format(owner=t.owner.username), "invited": True})
			await self.send_json({
				"type": "hub.table_list",
				"tables": tables,
				"empty_message": texts["table_list_empty"],
				"cancel_label": texts["table_list_cancel"],
			})
			return

		if event=="table.join":
			table_token=data.get("table_token")
			if not table_token:
				return
			table, error=await self.db_join_table(table_token)
			if error:
				await self.send_json({"type": "hub.history", "message": texts["table_not_found"]})
				return
			await self.send_json({
				"type": "table.joined",
				"table_token": str(table.token),
				"owner": table.owner.username,
				"message": texts["table_joined"].format(owner=table.owner.username),
				"sound": SOUND_TABLE_JOINED,
			})
			return

		if event=="hub.chat":
			message=data.get("message", "").strip()
			if not message:
				return
			if message.startswith("@"):
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
			friends=await self.db_get_friends()
			if not friends:
				await self.send_json({"type": "hub.history", "message": stexts["no_friends"]})
			else:
				for friend_id,username in friends:
					p=await presence.get_user_presence(friend_id)
					if p is None:
						line=stexts["friend_offline"].format(username=username)
					elif p["location"]=="hub":
						line=stexts["friend_online_hub"].format(username=username)
					else:
						line=stexts["friend_online_table"].format(username=username,owner=p.get("table_owner") or "")
					await self.send_json({"type": "hub.history", "message": line})
			await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
			return

		if event=="friends.add.open":
			stexts=get_social_texts_for_language(self.language)
			online=await presence.get_online_excluding(self.user.id)
			if not online:
				await self.send_json({"type": "hub.history", "message": stexts["no_online_players"]})
				await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
				return
			friend_ids,pending_ids=await self.db_get_friend_and_pending_ids()
			actions=[]
			for uid,data in online.items():
				if uid in friend_ids or uid in pending_ids:
					continue
				if data["location"]=="hub":
					label=stexts["add_player_hub"].format(username=data["username"])
				else:
					label=stexts["add_player_table"].format(username=data["username"],owner=data.get("table_owner") or "")
				actions.append({"type":"friends.add.request","user_id":uid,"label":label})
			if not actions:
				await self.send_json({"type": "hub.history", "message": stexts["no_online_players"]})
				await self.send_json({"type": "hub.menu", "actions": [{"type": "friends.open", "label": stexts["friends_back_to_friends"]}]})
				return
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
	def db_join_table(self, table_token):
		from .models import Table, TableInvite
		try:
			table=Table.objects.select_related("owner").get(token=table_token)
		except (Table.DoesNotExist, ValueError, ValidationError):
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
	def db_get_friends(self):
		from .models import Friendship
		return [(f.friend.id,f.friend.username) for f in Friendship.objects.filter(user=self.user).select_related("friend")]

	@database_sync_to_async
	def db_get_friend_and_pending_ids(self):
		from .models import Friendship, FriendRequest
		friend_ids=set(Friendship.objects.filter(user=self.user).values_list("friend_id",flat=True))
		pending_ids=set(FriendRequest.objects.filter(sender=self.user).values_list("receiver_id",flat=True))
		return friend_ids,pending_ids

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
		self.table_token=self.scope["url_route"]["kwargs"]["table_token"]
		try:
			uuid.UUID(self.table_token)
		except ValueError:
			await self.close()
			return
		table=await self.db_get_table()
		if table is None:
			await self.close()
			return
		self.owner_username=table.owner.username
		self.owner_id=table.owner.id
		self.is_private=table.is_private
		self.language=await get_consumer_language(self.user)
		self.table_group=f"table_{self.table_token}"
		await self.channel_layer.group_add(self.table_group, self.channel_name)
		await self.join_personal_group()
		await self.join_global_presence("table", table_owner=self.owner_username)
		await self.set_session_table_token(self.table_token)
		await self.accept()
		self.wizard=None
		await game.player_joined(self.table_token,self.user.id,self.user.username)
		payload=get_table_payload_for_language(
			self.language, self.table_token, self.owner_username, self.is_private, reverse("rpg_home")
		)
		payload["actions"]=await self.build_actions_list()
		await self.send_json(payload)

	async def disconnect(self, close_code):
		if hasattr(self, "table_group"):
			texts=get_table_texts_for_language(self.language)
			if await game.is_in_progress(self.table_token) and await game.get_master_id(self.table_token)==self.user.id:
				await game.stop_game(self.table_token)
				await self.channel_layer.group_send(self.table_group,{
					"type":"forward_json",
					"data":{"type":"hub.history","message":texts["game_master_disconnected"]},
				})
				await self.channel_layer.group_send(self.table_group,{"type":"refresh_actions"})
			await game.player_left(self.table_token,self.user.id)
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
			await self.clear_session_table_token()
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
			if await game.is_in_progress(self.table_token):
				await self.send_json({
					"type":"hub.menu",
					"message":texts["game_leave_confirm_prompt"],
					"actions":[
						{"type":"table.leave.confirm","label":texts["game_leave_confirm_yes"]},
						{"type":"game.wizard.cancel","label":texts["game_leave_cancel"]},
					],
				})
			else:
				await self.close()
			return

		if event=="table.leave.confirm":
			await self.close()
			return

		if event=="game.wizard.cancel":
			self.wizard=None
			await self.send_current_actions()
			return

		if event=="game.start":
			if await game.is_in_progress(self.table_token):
				await self.send_json({"type":"hub.history","message":texts["game_already_in_progress"]})
				return
			if await game.get_player_count(self.table_token)<2:
				await self.send_json({"type":"hub.history","message":texts["game_start_need_players"]})
				return
			self.wizard={"type":"start","step":"master","data":{}}
			players=await game.get_players(self.table_token)
			actions=[{"type":"game.wizard.select","user_id":uid,"username":uname,"label":uname} for uid,uname in players.items()]
			actions.append({"type":"game.wizard.cancel","label":texts["game_cancel"]})
			await self.send_json({"type":"hub.menu","message":texts["game_select_master"],"actions":actions})
			return

		if event=="game.stop":
			if await game.get_master_id(self.table_token)!=self.user.id:
				return
			await game.stop_game(self.table_token)
			await self.channel_layer.group_send(self.table_group,{
				"type":"forward_json",
				"data":{"type":"hub.history","message":texts["game_stopped"]},
			})
			await self.broadcast_refresh_actions()
			return

		if event=="game.dice.assign":
			if await game.get_master_id(self.table_token)!=self.user.id:
				return
			self.wizard={"type":"dice","step":"player","data":{}}
			await self.send_wizard_player_select(texts,texts["game_dice_select_player"])
			return

		if event=="game.coin.assign":
			if await game.get_master_id(self.table_token)!=self.user.id:
				return
			self.wizard={"type":"coin","step":"player","data":{}}
			await self.send_wizard_player_select(texts,texts["game_coin_select_player"])
			return

		if event=="game.master.pass":
			if await game.get_master_id(self.table_token)!=self.user.id:
				return
			self.wizard={"type":"pass","step":"player","data":{}}
			await self.send_wizard_player_select(texts,texts["game_pass_select"],exclude_self=True)
			return

		if event=="game.wizard.select":
			await self.handle_wizard_select(data,texts)
			return

		if event=="game.wizard.input":
			await self.handle_wizard_input(data.get("value",""),texts)
			return

		if event=="game.dice.roll":
			await self.handle_dice_roll(texts)
			return

		if event=="game.coin.flip":
			await self.handle_coin_flip(texts)
			return

		if event=="chat.send":
			message=data.get("message", "").strip()
			if not message:
				return
			if message.startswith("@"):
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

	async def build_actions_list(self):
		texts=get_table_texts_for_language(self.language)
		in_game=await game.is_in_progress(self.table_token)
		master_id=await game.get_master_id(self.table_token) if in_game else None
		challenge=await game.get_challenge(self.table_token,self.user.id)
		actions=[]
		if in_game:
			if self.user.id==master_id:
				actions+=[
					{"type":"game.dice.assign","label":texts["game_assign_dice"]},
					{"type":"game.coin.assign","label":texts["game_assign_coin"]},
					{"type":"game.master.pass","label":texts["game_pass_master"]},
					{"type":"game.stop","label":texts["game_stop"]},
				]
		elif self.user.id==self.owner_id:
			actions.append({"type":"game.start","label":texts["game_start"]})
		if challenge:
			if challenge["type"]=="dice":
				actions.append({"type":"game.dice.roll","label":texts["game_dice_roll"]})
			elif challenge["type"]=="coin":
				flipped=len(challenge.get("results",[]))
				total=challenge["count"]
				actions.append({"type":"game.coin.flip","label":texts["game_coin_flip"].format(current=flipped+1,total=total)})
		actions.append({"type":"table.leave","label":texts["table_leave"]})
		if self.is_private:
			actions.append({"type":"table.invite","label":texts["table_invite_button"]})
		return actions

	async def send_current_actions(self):
		await self.send_json({"type":"hub.menu","actions":await self.build_actions_list()})

	async def broadcast_refresh_actions(self):
		await self.channel_layer.group_send(self.table_group,{"type":"refresh_actions"})

	async def refresh_actions(self,event):
		await self.send_current_actions()

	async def send_wizard_player_select(self,texts,prompt,exclude_self=False):
		players=await game.get_players(self.table_token)
		actions=[]
		for uid,uname in players.items():
			if exclude_self and uid==self.user.id:
				continue
			actions.append({"type":"game.wizard.select","user_id":uid,"username":uname,"label":uname})
		actions.append({"type":"game.wizard.cancel","label":texts["game_cancel"]})
		await self.send_json({"type":"hub.menu","message":prompt,"actions":actions})

	async def handle_wizard_select(self,data,texts):
		if not self.wizard:
			return
		w=self.wizard
		if w["type"]=="start" and w["step"]=="master":
			uid=data.get("user_id")
			uname=data.get("username")
			if uid is None:
				return
			await game.start_game(self.table_token,uid,uname)
			self.wizard=None
			for player_id in await game.get_players(self.table_token):
				msg=texts["game_started_for_master"] if player_id==uid else texts["game_started_for_player"].format(master=uname)
				await self.channel_layer.group_send(f"user_{player_id}",{
					"type":"forward_json","data":{"type":"hub.history","message":msg},
				})
			await self.broadcast_refresh_actions()
			return
		if w["type"]=="dice" and w["step"]=="player":
			uid=data.get("user_id")
			uname=data.get("username")
			if uid is None:
				return
			w["data"]["player_id"]=uid
			w["data"]["player_username"]=uname
			w["step"]="sides"
			await self.send_json({"type":"hub.input","prompt":texts["game_dice_sides_prompt"],"action":"game.wizard.input"})
			return
		if w["type"]=="dice" and w["step"]=="condition":
			op=data.get("value")
			if op not in ("gt","gte","lt","lte","eq"):
				return
			w["data"]["condition"]=op
			w["step"]="target"
			sides=w["data"]["sides"]
			await self.send_json({"type":"hub.input","prompt":texts["game_dice_target_prompt"].format(sides=sides),"action":"game.wizard.input"})
			return
		if w["type"]=="coin" and w["step"]=="player":
			uid=data.get("user_id")
			uname=data.get("username")
			if uid is None:
				return
			w["data"]["player_id"]=uid
			w["data"]["player_username"]=uname
			w["step"]="count"
			await self.send_json({"type":"hub.input","prompt":texts["game_coin_count_prompt"],"action":"game.wizard.input"})
			return
		if w["type"]=="pass" and w["step"]=="player":
			uid=data.get("user_id")
			uname=data.get("username")
			if uid is None:
				return
			old_uname=self.user.username
			await game.set_master(self.table_token,uid,uname)
			self.wizard=None
			for player_id in await game.get_players(self.table_token):
				if player_id==self.user.id:
					msg=texts["game_passed_from_old"].format(new_master=uname)
				elif player_id==uid:
					msg=texts["game_passed_to_new"]
				else:
					msg=texts["game_passed_to_others"].format(old_master=old_uname,new_master=uname)
				await self.channel_layer.group_send(f"user_{player_id}",{
					"type":"forward_json","data":{"type":"hub.history","message":msg},
				})
			await self.broadcast_refresh_actions()
			return

	async def handle_wizard_input(self,value,texts):
		if not self.wizard:
			return
		w=self.wizard
		if w["type"]=="dice" and w["step"]=="sides":
			try:
				sides=int(value)
				if not 2<=sides<=100:
					raise ValueError
			except ValueError:
				await self.send_json({"type":"hub.input","prompt":texts["game_dice_sides_invalid"],"action":"game.wizard.input"})
				return
			w["data"]["sides"]=sides
			w["step"]="condition"
			actions=[
				{"type":"game.wizard.select","value":"gte","label":texts["game_dice_cond_gte"]},
				{"type":"game.wizard.select","value":"lte","label":texts["game_dice_cond_lte"]},
				{"type":"game.wizard.select","value":"gt","label":texts["game_dice_cond_gt"]},
				{"type":"game.wizard.select","value":"lt","label":texts["game_dice_cond_lt"]},
				{"type":"game.wizard.select","value":"eq","label":texts["game_dice_cond_eq"]},
			]
			await self.send_json({"type":"hub.menu","message":texts["game_dice_select_condition"],"actions":actions})
			return
		if w["type"]=="dice" and w["step"]=="target":
			sides=w["data"]["sides"]
			try:
				target=int(value)
				if not 1<=target<=sides:
					raise ValueError
			except ValueError:
				await self.send_json({"type":"hub.input","prompt":texts["game_dice_target_invalid"].format(sides=sides),"action":"game.wizard.input"})
				return
			target_pid=w["data"]["player_id"]
			player_uname=w["data"]["player_username"]
			op=w["data"]["condition"]
			cond_text=texts[f"game_dice_cond_text_{op}"].format(target=target)
			self.wizard=None
			await game.set_challenge(self.table_token,target_pid,{"type":"dice","sides":sides,"condition":op,"target":target})
			for player_id in await game.get_players(self.table_token):
				if player_id==target_pid:
					msg=texts["game_dice_challenge_self"].format(sides=sides,condition=cond_text)
				else:
					msg=texts["game_dice_challenge_others"].format(player=player_uname,sides=sides,condition=cond_text)
				await self.channel_layer.group_send(f"user_{player_id}",{
					"type":"forward_json","data":{"type":"hub.history","message":msg},
				})
			await self.broadcast_refresh_actions()
			return
		if w["type"]=="coin" and w["step"]=="count":
			try:
				count=int(value)
				if not 1<=count<=20:
					raise ValueError
			except ValueError:
				await self.send_json({"type":"hub.input","prompt":texts["game_coin_count_invalid"],"action":"game.wizard.input"})
				return
			w["data"]["count"]=count
			w["step"]="heads"
			await self.send_json({"type":"hub.input","prompt":texts["game_coin_heads_prompt"].format(count=count),"action":"game.wizard.input"})
			return
		if w["type"]=="coin" and w["step"]=="heads":
			count=w["data"]["count"]
			parsed=game.parse_coin_cond(value)
			if parsed is None:
				await self.send_json({"type":"hub.input","prompt":texts["game_coin_cond_invalid"],"action":"game.wizard.input"})
				return
			n,op=parsed
			if n<0 or n>count:
				await self.send_json({"type":"hub.input","prompt":texts["game_coin_cond_exceeds_total"].format(max=count),"action":"game.wizard.input"})
				return
			w["data"]["heads"]=(n,op)
			remaining=count-n
			w["step"]="tails"
			await self.send_json({"type":"hub.input","prompt":texts["game_coin_tails_prompt"].format(remaining=remaining),"action":"game.wizard.input"})
			return
		if w["type"]=="coin" and w["step"]=="tails":
			count=w["data"]["count"]
			heads_n,_=w["data"]["heads"]
			remaining=count-heads_n
			parsed=game.parse_coin_cond(value)
			if parsed is None:
				await self.send_json({"type":"hub.input","prompt":texts["game_coin_cond_invalid"],"action":"game.wizard.input"})
				return
			n,op=parsed
			if n<0 or n>remaining:
				await self.send_json({"type":"hub.input","prompt":texts["game_coin_cond_exceeds_total"].format(max=remaining),"action":"game.wizard.input"})
				return
			tails=(n,op)
			heads=w["data"]["heads"]
			target_pid=w["data"]["player_id"]
			player_uname=w["data"]["player_username"]
			cond_text=self.build_coin_condition_text(texts,count,heads,tails)
			self.wizard=None
			await game.set_challenge(self.table_token,target_pid,{"type":"coin","count":count,"heads":heads,"tails":tails,"results":[]})
			for player_id in await game.get_players(self.table_token):
				if player_id==target_pid:
					msg=texts["game_coin_challenge_self"].format(count=count,condition=cond_text)
				else:
					msg=texts["game_coin_challenge_others"].format(player=player_uname,count=count,condition=cond_text)
				await self.channel_layer.group_send(f"user_{player_id}",{
					"type":"forward_json","data":{"type":"hub.history","message":msg},
				})
			await self.broadcast_refresh_actions()
			return

	async def handle_dice_roll(self,texts):
		challenge=await game.get_challenge(self.table_token,self.user.id)
		if not challenge or challenge["type"]!="dice":
			await self.send_json({"type":"hub.history","message":texts["game_no_challenge"]})
			return
		result=game.roll_die(challenge["sides"])
		for player_id in await game.get_players(self.table_token):
			if player_id==self.user.id:
				msg=texts["game_dice_rolled_self"].format(result=result)
			else:
				msg=texts["game_dice_rolled_others"].format(player=self.user.username,result=result)
			await self.channel_layer.group_send(f"user_{player_id}",{
				"type":"forward_json","data":{"type":"hub.history","message":msg,"sound":SOUND_DICE_ROLL},
			})
		success=game.check_dice(result,challenge["condition"],challenge["target"])
		result_msg=texts["game_dice_success"] if success else texts["game_dice_failure"]
		await self.channel_layer.group_send(self.table_group,{
			"type":"forward_json","data":{"type":"hub.history","message":result_msg},
		})
		await game.clear_challenge(self.table_token,self.user.id)
		await self.broadcast_refresh_actions()

	async def handle_coin_flip(self,texts):
		challenge=await game.get_challenge(self.table_token,self.user.id)
		if not challenge or challenge["type"]!="coin":
			await self.send_json({"type":"hub.history","message":texts["game_no_challenge"]})
			return
		result=game.flip_coin()
		challenge["results"].append(result)
		await game.set_challenge(self.table_token,self.user.id,challenge)
		flipped=len(challenge["results"])
		total=challenge["count"]
		if result=="heads":
			msg_self=texts["game_coin_flipped_self_heads"]
			msg_others=texts["game_coin_flipped_heads"].format(player=self.user.username)
		else:
			msg_self=texts["game_coin_flipped_self_tails"]
			msg_others=texts["game_coin_flipped_tails"].format(player=self.user.username)
		for player_id in await game.get_players(self.table_token):
			msg=msg_self if player_id==self.user.id else msg_others
			await self.channel_layer.group_send(f"user_{player_id}",{
				"type":"forward_json","data":{"type":"hub.history","message":msg,"sound":SOUND_COIN_FLIP},
			})
		if flipped>=total:
			heads_count=challenge["results"].count("heads")
			tails_count=challenge["results"].count("tails")
			heads_n,heads_op=challenge["heads"]
			tails_n,tails_op=challenge["tails"]
			success=game.check_coin_count(heads_count,heads_op,heads_n) and game.check_coin_count(tails_count,tails_op,tails_n)
			result_msg=texts["game_coin_success"] if success else texts["game_coin_failure"]
			await self.channel_layer.group_send(self.table_group,{
				"type":"forward_json","data":{"type":"hub.history","message":result_msg},
			})
			await game.clear_challenge(self.table_token,self.user.id)
			await self.broadcast_refresh_actions()
		else:
			await self.send_current_actions()

	def build_coin_cond_phrase(self,texts,n,op,side_key):
		side=texts[side_key]
		if op=="exact":
			key="game_coin_phrase_exact_singular" if n==1 else "game_coin_phrase_exact_plural"
			return texts[key].format(n=n,side=side)
		return texts[f"game_coin_phrase_{op}"].format(n=n,side=side)

	def build_coin_condition_text(self,texts,count,heads,tails):
		heads_n,heads_op=heads
		tails_n,tails_op=tails
		parts=[]
		if not (heads_n==0 and heads_op=="exact"):
			parts.append(self.build_coin_cond_phrase(texts,heads_n,heads_op,"game_coin_side_heads"))
		if not (tails_n==0 and tails_op=="exact"):
			parts.append(self.build_coin_cond_phrase(texts,tails_n,tails_op,"game_coin_side_tails"))
		if not parts:
			return ""
		if len(parts)==1:
			return parts[0]
		return texts["game_coin_phrase_combined"].format(a=parts[0],b=parts[1])

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
			return Table.objects.select_related("owner").get(token=self.table_token, members=self.user)
		except Table.DoesNotExist:
			return None

	@database_sync_to_async
	def db_invite_user(self, username):
		from .models import Table, TableInvite
		try:
			recipient=User.objects.get(username=username)
		except User.DoesNotExist:
			return None, "not_found"
		table=Table.objects.get(token=self.table_token)
		TableInvite.objects.get_or_create(table=table, invited_user=recipient)
		return recipient, None
