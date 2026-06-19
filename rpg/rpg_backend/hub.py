from .i18n import load_translations

def get_hub_language(user):
	if hasattr(user, "profile"):
		return user.profile.default_language
	return "pt-BR"

def get_hub_texts_for_language(language):
	return load_translations("hub", language)

def get_hub_actions_for_language(language, logout_url, landing_url):
	texts=get_hub_texts_for_language(language)
	from .social import get_social_texts_for_language
	stexts=get_social_texts_for_language(language)
	return [
		{"type": "table.create", "label": texts["table_create"]},
		{"type": "table.list", "label": texts["table_join"]},
		{"type": "social.open", "label": stexts["social_label"]},
		{"type": "hub.disconnect", "label": texts["hub_disconnect"], "landing_url": landing_url},
		{"type": "hub.exit", "label": texts["hub_exit"], "logout_url": logout_url},
	]

def get_hub_payload_for_language(language, logout_url, landing_url):
	texts=get_hub_texts_for_language(language)
	return {
		"type": "hub.connected",
		"message": texts["hub_connected"],
		"actions": get_hub_actions_for_language(language, logout_url, landing_url),
		"messages": {
			"client_invalid_message": texts["client_invalid_message"],
			"connection_closed": texts["connection_closed"],
		},
	}
