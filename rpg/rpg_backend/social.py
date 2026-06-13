social_texts={
	"pt-BR": {
		"social_label": "Opções sociais",
		"social_back": "Voltar",
		"friends_label": "Amigos",
		"friends_list_label": "Ver amigos",
		"friends_add_label": "Adicionar amigo",
		"friends_remove_label": "Remover amigo",
		"friends_back": "Voltar para opções sociais",
		"friends_pending_label": "Pedidos pendentes: {count}",
		"friends_back_to_friends": "Voltar para amigos",
		"no_friends": "Você não tem amigos na lista.",
		"no_online_players": "Nenhum jogador online disponível para adicionar.",
		"no_friends_to_remove": "Você não tem amigos para remover.",
		"no_pending_requests": "Nenhum pedido de amizade pendente.",
		"friend_online_hub": "{username} — online (hub)",
		"friend_online_table": "{username} — online (mesa de {owner})",
		"friend_offline": "{username} — offline",
		"add_player_hub": "{username} (hub)",
		"add_player_table": "{username} (mesa de {owner})",
		"friend_request_sent": "Pedido de amizade enviado para {username}.",
		"friend_request_already_sent": "Você já enviou um pedido para {username}.",
		"friend_request_already_friends": "{username} já é seu amigo.",
		"friend_request_received_notification": "{username} te enviou um pedido de amizade.",
		"accept_request_label": "Aceitar pedido de {username}",
		"decline_request_label": "Recusar pedido de {username}",
		"friend_request_accepted": "Você aceitou o pedido de {username}.",
		"friend_request_accepted_notification": "{username} aceitou seu pedido de amizade.",
		"friend_request_declined": "Você recusou o pedido de {username}.",
		"friend_request_not_found": "Pedido de amizade não encontrado.",
		"remove_friend_label": "Remover {username}",
		"friend_removed": "{username} foi removido da sua lista de amigos.",
		"friend_not_found": "Usuário não encontrado.",
	},
	"en": {
		"social_label": "Social options",
		"social_back": "Back",
		"friends_label": "Friends",
		"friends_list_label": "View friends",
		"friends_add_label": "Add friend",
		"friends_remove_label": "Remove friend",
		"friends_back": "Back to social options",
		"friends_pending_label": "Pending requests: {count}",
		"friends_back_to_friends": "Back to friends",
		"no_friends": "You have no friends in your list.",
		"no_online_players": "No online players available to add.",
		"no_friends_to_remove": "You have no friends to remove.",
		"no_pending_requests": "No pending friend requests.",
		"friend_online_hub": "{username} — online (hub)",
		"friend_online_table": "{username} — online ({owner}'s table)",
		"friend_offline": "{username} — offline",
		"add_player_hub": "{username} (hub)",
		"add_player_table": "{username} ({owner}'s table)",
		"friend_request_sent": "Friend request sent to {username}.",
		"friend_request_already_sent": "You already sent a request to {username}.",
		"friend_request_already_friends": "{username} is already your friend.",
		"friend_request_received_notification": "{username} sent you a friend request.",
		"accept_request_label": "Accept request from {username}",
		"decline_request_label": "Decline request from {username}",
		"friend_request_accepted": "You accepted {username}'s request.",
		"friend_request_accepted_notification": "{username} accepted your friend request.",
		"friend_request_declined": "You declined {username}'s request.",
		"friend_request_not_found": "Friend request not found.",
		"remove_friend_label": "Remove {username}",
		"friend_removed": "{username} was removed from your friends list.",
		"friend_not_found": "User not found.",
	}
}

def get_social_texts_for_language(language):
	return social_texts.get(language, social_texts["pt-BR"])

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
