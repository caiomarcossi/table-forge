from django.conf import settings

SOUND_CONNECTION="connected"
SOUND_DICE_ROLL="dice_roll"
SOUND_CHAT_MESSAGE="chat"
SOUND_PRIVATE_MESSAGE="private_message"
SOUND_ERROR="error"
SOUND_TABLE_CREATED="table_created"
SOUND_TABLE_JOINED="table_joined"
SOUND_TABLE_LEAVED="table_leaved"
SOUND_PLAYER_CONNECTED="player_connected"
SOUND_PLAYER_DISCONNECTED="player_disconnected"

VALID_SOUNDS={
	SOUND_CONNECTION,
	SOUND_DICE_ROLL,
	SOUND_CHAT_MESSAGE,
	SOUND_PRIVATE_MESSAGE,
	SOUND_ERROR,
	SOUND_TABLE_CREATED,
	SOUND_TABLE_JOINED,
	SOUND_TABLE_LEAVED,
	SOUND_PLAYER_CONNECTED,
	SOUND_PLAYER_DISCONNECTED,
}

def get_sound_path(sound_id):
	return settings.BASE_DIR / "rpg_backend" / "audio" / f"{sound_id}.ogg"
