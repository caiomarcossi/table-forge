table_texts={
	"pt-BR": {
		"table_connected": "Conectado à mesa de {owner}.",
		"table_leave": "Sair da mesa",
		"table_invite_button": "Convidar jogador",
		"invite_prompt": "Digite o nome do jogador a convidar:",
		"invite_sent": "Convite enviado para {username}.",
		"invite_received": "{owner} te convidou para uma mesa. Use 'Entrar em mesa' para aceitar.",
		"invite_user_not_found": "Usuário não encontrado.",
		"invite_format": "Use: /invite <usuário>",
		"player_left": "{username} saiu da mesa.",
		"chat_message": "{username}: {message}",
		"private_message_sent": "→ {username}: {message}",
		"private_message_from": "← {username}: {message}",
		"private_message_user_not_found": "Usuário não encontrado.",
		"private_message_format": "Use: /w <usuário> <mensagem>",
		"client_invalid_message": "Mensagem inválida recebida pelo cliente.",
		"connection_closed": "Conexão com a mesa encerrada.",
	},
	"en": {
		"table_connected": "Connected to {owner}'s table.",
		"table_leave": "Leave table",
		"table_invite_button": "Invite player",
		"invite_prompt": "Enter the player's name to invite:",
		"invite_sent": "Invite sent to {username}.",
		"invite_received": "{owner} invited you to a table. Use 'Join table' to accept.",
		"invite_user_not_found": "User not found.",
		"invite_format": "Use: /invite <user>",
		"player_left": "{username} left the table.",
		"chat_message": "{username}: {message}",
		"private_message_sent": "→ {username}: {message}",
		"private_message_from": "← {username}: {message}",
		"private_message_user_not_found": "User not found.",
		"private_message_format": "Use: /w <user> <message>",
		"client_invalid_message": "Invalid message received by the client.",
		"connection_closed": "Connection to table closed.",
	}
}

def get_table_texts_for_language(language):
	return table_texts.get(language, table_texts["pt-BR"])

def get_table_payload_for_language(language, table_id, owner_username, is_private, hub_url):
	texts=get_table_texts_for_language(language)
	actions=[
		{"type": "table.leave", "label": texts["table_leave"], "hub_url": hub_url},
	]
	if is_private:
		actions.append({"type": "table.invite", "label": texts["table_invite_button"]})
	return {
		"type": "table.connected",
		"table_id": table_id,
		"owner": owner_username,
		"message": texts["table_connected"].format(owner=owner_username),
		"actions": actions,
		"messages": {
			"client_invalid_message": texts["client_invalid_message"],
			"connection_closed": texts["connection_closed"],
		},
	}
