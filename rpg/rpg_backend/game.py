import random
from django.core.cache import cache

def _pk(token): return f"game:players:{token}"
def _sk(token): return f"game:state:{token}"
def _ck(token,user_id): return f"game:challenge:{token}:{user_id}"

async def player_joined(token,user_id,username):
	players=await cache.aget(_pk(token)) or {}
	players[str(user_id)]=username
	await cache.aset(_pk(token),players)

async def player_left(token,user_id):
	players=await cache.aget(_pk(token)) or {}
	players.pop(str(user_id),None)
	if players:
		await cache.aset(_pk(token),players)
	else:
		await cache.adelete(_pk(token))
	await cache.adelete(_ck(token,user_id))

async def get_players(token):
	players=await cache.aget(_pk(token)) or {}
	return {int(k):v for k,v in players.items()}

async def get_player_count(token):
	players=await cache.aget(_pk(token)) or {}
	return len(players)

async def is_in_progress(token):
	return await cache.aget(_sk(token)) is not None

async def get_master_id(token):
	state=await cache.aget(_sk(token))
	return state["master_id"] if state else None

async def get_master_username(token):
	state=await cache.aget(_sk(token))
	return state["master_username"] if state else None

async def start_game(token,master_id,master_username):
	await cache.aset(_sk(token),{"master_id":int(master_id),"master_username":master_username})

async def stop_game(token):
	await cache.adelete(_sk(token))
	players=await cache.aget(_pk(token)) or {}
	for user_id in players:
		await cache.adelete(_ck(token,user_id))

async def set_master(token,master_id,master_username):
	state=await cache.aget(_sk(token))
	if state:
		state["master_id"]=int(master_id)
		state["master_username"]=master_username
		await cache.aset(_sk(token),state)

async def set_challenge(token,user_id,challenge):
	await cache.aset(_ck(token,user_id),challenge)

async def get_challenge(token,user_id):
	return await cache.aget(_ck(token,user_id))

async def clear_challenge(token,user_id):
	await cache.adelete(_ck(token,user_id))

def roll_die(sides):
	return random.randint(1,sides)

def flip_coin():
	return random.choice(["heads","tails"])

def check_dice(result,op,target):
	if op=="gt": return result>target
	if op=="gte": return result>=target
	if op=="lt": return result<target
	if op=="lte": return result<=target
	if op=="eq": return result==target
	return False

def check_coin_count(count,op,target):
	if op=="exact": return count==target
	if op=="gte": return count>=target
	if op=="gt": return count>target
	if op=="lte": return count<=target
	if op=="lt": return count<target
	return False

def parse_coin_cond(text):
	text=text.strip()
	if not text: return None
	if text.startswith("+"):
		rest=text[1:].strip()
		try: return (int(rest),"gt")
		except ValueError: return None
	if text.startswith("-"):
		rest=text[1:].strip()
		try: return (int(rest),"lt")
		except ValueError: return None
	if text.endswith("+"):
		rest=text[:-1].strip()
		try: return (int(rest),"gte")
		except ValueError: return None
	if text.endswith("-"):
		rest=text[:-1].strip()
		try: return (int(rest),"lte")
		except ValueError: return None
	try: return (int(text),"exact")
	except ValueError: return None
