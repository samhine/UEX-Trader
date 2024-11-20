from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from config_manager import ConfigManager
from translation_manager import TranslationManager
import asyncio


class ConfigTab(QWidget):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        # Initial the ConfigManager instance only once
        if ConfigManager._instance is None:
            self.config_manager = ConfigManager()
            asyncio.get_event_loop().run_until_complete(self.config_manager.initialize())
        else:
            self.config_manager = ConfigManager._instance
        # Initialize the TranslationManager instance only once
        if TranslationManager._instance is None:
            self.translation_manager = TranslationManager()
        else:
            self.translation_manager = TranslationManager._instance
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.api_key_label = QLabel(self.translation_manager.get_translation("config_uexcorp_apikey",
                                                                             self.config_manager.get_lang())+":")
        self.api_key_input = QLineEdit(self.config_manager.get_api_key())
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.editingFinished.connect(self.update_api_key)

        # Create the eye button for API Key
        self.show_api_key_button = QPushButton("👁", self)
        self.show_api_key_button.setFixedSize(30, 30)  # Adjust size as needed
        self.show_api_key_button.pressed.connect(self.show_api_key)
        self.show_api_key_button.released.connect(self.hide_api_key)

        self.secret_key_label = QLabel(self.translation_manager.get_translation("config_uexcorp_secretkey",
                                                                                self.config_manager.get_lang())+":")
        self.secret_key_input = QLineEdit(self.config_manager.get_secret_key())
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.secret_key_input.editingFinished.connect(self.update_secret_key)

        # Create the eye button for Secret Key
        self.show_secret_key_button = QPushButton("👁", self)
        self.show_secret_key_button.setFixedSize(30, 30)  # Adjust size as needed
        self.show_secret_key_button.pressed.connect(self.show_secret_key)
        self.show_secret_key_button.released.connect(self.hide_secret_key)

        self.is_production_label = QLabel(self.translation_manager.get_translation("config_isproduction",
                                                                                   self.config_manager.get_lang())+":")
        self.is_production_input = QComboBox()
        self.is_production_input.addItems(["True", "False"])
        self.is_production_input.setCurrentText(str(self.config_manager.get_is_production()))
        self.is_production_input.currentIndexChanged.connect(self.update_is_production)

        self.debug_label = QLabel(self.translation_manager.get_translation("config_debugmode",
                                                                           self.config_manager.get_lang())+":")
        self.debug_input = QComboBox()
        self.debug_input.addItems(["False", "True"])
        self.debug_input.setCurrentText(str(self.config_manager.get_debug()))
        self.debug_input.currentIndexChanged.connect(self.update_debug_mode)

        self.appearance_label = QLabel(self.translation_manager.get_translation("config_appearancemode",
                                                                                self.config_manager.get_lang())+":")
        self.appearance_input = QComboBox()
        self.appearance_input.addItem(self.translation_manager.get_translation("appearance_dark",
                                                                               self.config_manager.get_lang()), "Dark")
        self.appearance_input.addItem(self.translation_manager.get_translation("appearance_light",
                                                                               self.config_manager.get_lang()), "Light")
        self.appearance_input.setCurrentIndex(self.appearance_input.findData(self.config_manager.get_appearance_mode()))
        self.appearance_input.currentIndexChanged.connect(self.update_appearance_mode)
        self.update_appearance_mode()

        self.language_label = QLabel(self.translation_manager.get_translation("config_language",
                                                                              self.config_manager.get_lang())+":")
        self.language_input = QComboBox()
        langs = self.translation_manager.get_available_lang()
        for lang in langs:
            self.language_input.addItem(self.translation_manager.get_translation("current_language", lang), lang)
        self.language_input.setCurrentIndex(self.language_input.findData(self.config_manager.get_lang()))
        self.language_input.currentIndexChanged.connect(self.update_lang)

        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.show_api_key_button)
        layout.addWidget(self.secret_key_label)
        layout.addWidget(self.secret_key_input)
        layout.addWidget(self.show_secret_key_button)
        layout.addWidget(self.is_production_label)
        layout.addWidget(self.is_production_input)
        layout.addWidget(self.debug_label)
        layout.addWidget(self.debug_input)
        layout.addWidget(self.appearance_label)
        layout.addWidget(self.appearance_input)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_input)

        self.setLayout(layout)

    def show_api_key(self):
        self.api_key_input.setEchoMode(QLineEdit.Normal)

    def hide_api_key(self):
        self.api_key_input.setEchoMode(QLineEdit.Password)

    def show_secret_key(self):
        self.secret_key_input.setEchoMode(QLineEdit.Normal)

    def hide_secret_key(self):
        self.secret_key_input.setEchoMode(QLineEdit.Password)

    def update_appearance_mode(self):
        new_appearance = self.appearance_input.currentData()
        self.config_manager.set_appearance_mode(new_appearance)
        self.main_widget.apply_appearance_mode(new_appearance)

    def update_lang(self):
        new_lang = self.language_input.currentData()
        self.config_manager.set_lang(new_lang)
        self.main_widget.initUI(new_lang)

    def update_is_production(self):
        self.config_manager.set_is_production(self.is_production_input.currentText() == "True")

    def update_debug_mode(self):
        self.config_manager.set_debug(self.debug_input.currentText() == "True")

    def update_api_key(self):
        self.config_manager.set_api_key(self.api_key_input.text())

    def update_secret_key(self):
        self.config_manager.set_secret_key(self.secret_key_input.text())

    def set_gui_enabled(self, enabled):
        for input in self.findChildren(QLineEdit):
            input.setEnabled(enabled)
        for combo in self.findChildren(QComboBox):
            combo.setEnabled(enabled)
        for button in self.findChildren(QPushButton):
            button.setEnabled(enabled)
