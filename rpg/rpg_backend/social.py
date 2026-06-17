from .i18n import load_translations

def get_social_texts_for_language(language):
	return load_translations("social", language)

def get_social_menu(language):
	texts=get_social_texts_for_language(language)
	return {
		"type": "hub.menu",
		"actions": [
			{"type": "friends.open", "label": texts["friends_label"]},
			{"type": "hub.main", "label": texts["social_back"]},
		],
	}

def get_friends_menu(language, pending_count):
	texts=get_social_texts_for_language(language)
	actions=[]
	if pending_count > 0:
		actions.append({"type": "friends.requests.open", "label": texts["friends_pending_label"].format(count=pending_count)})
	actions+=[
		{"type": "friends.list", "label": texts["friends_list_label"]},
		{"type": "friends.add.open", "label": texts["friends_add_label"]},
		{"type": "friends.remove.open", "label": texts["friends_remove_label"]},
		{"type": "social.open", "label": texts["friends_back"]},
	]
	return {"type": "hub.menu", "actions": actions}
