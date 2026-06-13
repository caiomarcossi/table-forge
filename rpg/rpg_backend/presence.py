_online={}

def user_connected(user_id, username, location, table_owner=None):
	_online[user_id]={"username": username, "location": location, "table_owner": table_owner}

def user_disconnected(user_id):
	_online.pop(user_id, None)

def get_user_presence(user_id):
	return _online.get(user_id)

def get_all_online():
	return dict(_online)

def get_online_excluding(user_id):
	return {uid: data for uid, data in _online.items() if uid != user_id}
