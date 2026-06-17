from .i18n import load_translations

def get_table_texts_for_language(language):
	return load_translations("tables", language)

def get_table_payload_for_language(language, table_token, owner_username, is_private, hub_url):
	texts=get_table_texts_for_language(language)
	actions=[
		{"type": "table.leave", "label": texts["table_leave"], "hub_url": hub_url},
	]
	if is_private:
		actions.append({"type": "table.invite", "label": texts["table_invite_button"]})
	return {
		"type": "table.connected",
		"table_token": table_token,
		"owner": owner_username,
		"message": texts["table_connected"].format(owner=owner_username),
		"actions": actions,
		"messages": {
			"client_invalid_message": texts["client_invalid_message"],
			"connection_closed": texts["connection_closed"],
		},
	}
