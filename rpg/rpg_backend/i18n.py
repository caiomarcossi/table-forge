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

class I18n:
	def __init__(self, namespace, language=DEFAULT_LANGUAGE):
		self.namespace=namespace
		self.language=language
		self.__translation_dict=load_translations(namespace, language)

	def change_language(self, language):
		self.language=language
		self.__translation_dict=load_translations(self.namespace, language)

	def get_language(self):
		return self.language

	def available_languages(self):
		namespace_dir=TRANSLATIONS_DIR / self.namespace
		if not namespace_dir.is_dir():
			return [self.language]
		return sorted(f.stem for f in namespace_dir.glob("*.json"))

	def t(self, key):
		return self.__translation_dict.get(key, key)
