hub_texts={
	"pt-BR": {
		"hub_connected": "Hub conectado.",
		"table_create": "Criar mesa",
		"table_join": "Entrar em mesa",
		"hub_exit": "Sair",
		"table_created": "Mesa criada.",
		"table_joined": "Você entrou na mesa de {owner}.",
		"table_list_empty": "Nenhuma mesa pública disponível.",
		"table_list_label": "Mesa de {owner}",
		"table_list_label_invited": "Mesa de {owner} (convite)",
		"table_list_cancel": "Cancelar",
		"table_not_found": "Mesa não encontrada.",
		"hub_chat_only_private": "Chat público disponível apenas dentro de uma mesa. Use /w <usuário> <mensagem> para mensagem privada.",
		"private_message_sent": "→ {username}: {message}",
		"private_message_from": "← {username}: {message}",
		"private_message_user_not_found": "Usuário não encontrado.",
		"private_message_format": "Use: /w <usuário> <mensagem>",
		"client_invalid_message": "Mensagem inválida recebida pelo cliente.",
		"connection_closed": "Conexão em tempo real encerrada.",
	},
	"en": {
		"hub_connected": "Hub connected.",
		"table_create": "Create table",
		"table_join": "Join table",
		"hub_exit": "Exit",
		"table_created": "Table created.",
		"table_joined": "You joined {owner}'s table.",
		"table_list_empty": "No public tables available.",
		"table_list_label": "{owner}'s table",
		"table_list_label_invited": "{owner}'s table (invite)",
		"table_list_cancel": "Cancel",
		"table_not_found": "Table not found.",
		"hub_chat_only_private": "Public chat only available inside a table. Use /w <user> <message> for private message.",
		"private_message_sent": "→ {username}: {message}",
		"private_message_from": "← {username}: {message}",
		"private_message_user_not_found": "User not found.",
		"private_message_format": "Use: /w <user> <message>",
		"client_invalid_message": "Invalid message received by the client.",
		"connection_closed": "Real-time connection closed.",
	}
}

def get_hub_language(user):
	if hasattr(user, "profile"):
		return user.profile.default_language
	return "pt-BR"

def get_hub_texts_for_language(language):
	return hub_texts.get(language, hub_texts["pt-BR"])

def get_hub_texts(user):
	return get_hub_texts_for_language(get_hub_language(user))

def get_hub_actions_for_language(language, logout_url):
	texts=get_hub_texts_for_language(language)
	from .social import get_social_texts_for_language
	stexts=get_social_texts_for_language(language)
	return [
		{"type": "table.create", "label": texts["table_create"]},
		{"type": "table.join", "label": texts["table_join"]},
		{"type": "social.open", "label": stexts["social_label"]},
		{"type": "hub.exit", "label": texts["hub_exit"], "logout_url": logout_url},
	]

def get_hub_payload_for_language(language, logout_url):
	texts=get_hub_texts_for_language(language)
	return {
		"type": "hub.connected",
		"message": texts["hub_connected"],
		"actions": get_hub_actions_for_language(language, logout_url),
		"messages": {
			"client_invalid_message": texts["client_invalid_message"],
			"connection_closed": texts["connection_closed"],
		},
	}

def get_hub_payload(user, logout_url):
	return get_hub_payload_for_language(get_hub_language(user), logout_url)
