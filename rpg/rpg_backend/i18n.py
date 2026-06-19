import json
from django.conf import settings

TRANSLATIONS_DIR=settings.BASE_DIR / "rpg_backend" / "translations"
DEFAULT_LANGUAGE="pt-BR"

def load_translations(namespace, language):
	path=TRANSLATIONS_DIR / namespace / f"{language}.json"
	if not path.is_file():
		path=TRANSLATIONS_DIR / namespace / f"{DEFAULT_LANGUAGE}.json"
	with open(path, "r", encoding="utf-8") as file:
		return json.load(file)
