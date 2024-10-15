# user_functions.py
import configparser
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        self.config.read(self.config_file)

    def save_config(self):
        with open(self.config_file, "w") as f:
            self.config.write(f)

    def get_api_key(self):
        return self.config.get("API", "key", fallback="")

    def set_api_key(self, key):
        self.config["API"] = {"key": key}
        self.save_config()

    def get_is_production(self):
        return self.config.getboolean("SETTINGS", "is_production", fallback=False)

    def set_is_production(self, is_production):
        self.config["SETTINGS"] = {"is_production": str(is_production)}
        self.save_config()

    def get_debug(self):
        return self.config.getboolean("SETTINGS", "debug", fallback=False)

    def set_debug(self, debug):
        self.config["SETTINGS"]["debug"] = str(debug)
        self.save_config()

    def get_appearance_mode(self):
        return self.config.get("SETTINGS", "appearance_mode", fallback="Light")

    def set_appearance_mode(self, mode):
        self.config["SETTINGS"]["appearance_mode"] = mode
        self.save_config()
