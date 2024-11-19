# translation_manager.py
import configparser


class TranslationManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, translation_file="translations.ini"):
        if not hasattr(self, 'initialized'):  # Ensure __init__ is only called once
            self.translation_file = translation_file
            self.translation_config = configparser.ConfigParser()
            self.load_translations()
            self.initialized = True
            self.available_langs = [
                "en",
                "fr",
                "ru"
            ]

    def load_translations(self):
        self.translation_config.read(self.translation_file)

    def get_available_lang(self):
        return self.available_langs

    def get_lang_name(self, lang):
        for item in self.available_langs:
            if lang is item or lang == item:
                return self.get_translation("current_language", lang)
        return "Unknown"

    # Use "ISO 639 language codes" as lang
    def get_translation(self, key, lang="en"):
        for item in self.available_langs:
            if lang is item or lang == item:
                value = self.translation_config.get(lang, key, fallback=key)
                if value == key:
                    return self.translation_config.get("en", key, fallback=key)
                return value
        return self.translation_config.get("en", key, fallback=key)
