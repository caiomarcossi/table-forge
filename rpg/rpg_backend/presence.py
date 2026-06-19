from django.core.cache import cache

_KEY="presence:{}"
_INDEX="presence:_index"

async def user_connected(user_id,username,location,table_owner=None):
	await cache.aset(_KEY.format(user_id),{"username":username,"location":location,"table_owner":table_owner},timeout=None)
	index=await cache.aget(_INDEX) or []
	if user_id not in index:
		index.append(user_id)
		await cache.aset(_INDEX,index,timeout=None)

async def user_disconnected(user_id):
	await cache.adelete(_KEY.format(user_id))
	index=await cache.aget(_INDEX) or []
	if user_id in index:
		index.remove(user_id)
		await cache.aset(_INDEX,index,timeout=None)

async def get_user_presence(user_id):
	return await cache.aget(_KEY.format(user_id))

async def get_all_online():
	index=await cache.aget(_INDEX) or []
	result={}
	for uid in index:
		data=await cache.aget(_KEY.format(uid))
		if data:
			result[uid]=data
	return result

async def get_online_excluding(user_id):
	online=await get_all_online()
	return {uid:data for uid,data in online.items() if uid!=user_id}

_OWNER="presence:owner:{}"

async def claim_connection(user_id,channel_name):
	await cache.aset(_OWNER.format(user_id),channel_name,timeout=None)

async def is_current_connection(user_id,channel_name):
	return await cache.aget(_OWNER.format(user_id))==channel_name

async def release_connection(user_id,channel_name):
	if await cache.aget(_OWNER.format(user_id))==channel_name:
		await cache.adelete(_OWNER.format(user_id))
