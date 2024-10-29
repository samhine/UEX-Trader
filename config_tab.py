from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from config_manager import ConfigManager
import logging


class ConfigTab(QWidget):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.config_manager = ConfigManager()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        api_key_label = QLabel("UEXcorp API Key:")
        self.api_key_input = QLineEdit(self.config_manager.get_api_key())
        self.api_key_input.setEchoMode(QLineEdit.Password)

        # Create the eye button for API Key
        self.show_api_key_button = QPushButton("👁", self)
        self.show_api_key_button.setFixedSize(30, 30)  # Adjust size as needed
        self.show_api_key_button.pressed.connect(self.show_api_key)
        self.show_api_key_button.released.connect(self.hide_api_key)

        secret_key_label = QLabel("UEXcorp Secret Key:")
        self.secret_key_input = QLineEdit(self.config_manager.get_secret_key())
        self.secret_key_input.setEchoMode(QLineEdit.Password)

        # Create the eye button for Secret Key
        self.show_secret_key_button = QPushButton("👁", self)
        self.show_secret_key_button.setFixedSize(30, 30)  # Adjust size as needed
        self.show_secret_key_button.pressed.connect(self.show_secret_key)
        self.show_secret_key_button.released.connect(self.hide_secret_key)

        is_production_label = QLabel("Is Production:")
        self.is_production_input = QComboBox()
        self.is_production_input.addItems(["False", "True"])
        self.is_production_input.setCurrentText(str(self.config_manager.get_is_production()))

        debug_label = QLabel("Debug Mode:")
        self.debug_input = QComboBox()
        self.debug_input.addItems(["False", "True"])
        self.debug_input.setCurrentText(str(self.config_manager.get_debug()))

        appearance_label = QLabel("Appearance Mode:")
        self.appearance_input = QComboBox()
        self.appearance_input.addItems(["Light", "Dark"])
        self.appearance_input.setCurrentText(self.config_manager.get_appearance_mode())
        self.appearance_input.currentIndexChanged.connect(self.update_appearance_mode)

        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)

        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.show_api_key_button)
        layout.addWidget(secret_key_label)
        layout.addWidget(self.secret_key_input)
        layout.addWidget(self.show_secret_key_button)
        layout.addWidget(is_production_label)
        layout.addWidget(self.is_production_input)
        layout.addWidget(debug_label)
        layout.addWidget(self.debug_input)
        layout.addWidget(appearance_label)
        layout.addWidget(self.appearance_input)
        layout.addWidget(save_config_button)

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
        new_appearance = self.appearance_input.currentText()
        self.config_manager.set_appearance_mode(new_appearance)
        self.main_widget.apply_appearance_mode(new_appearance)

    def save_configuration(self):
        self.config_manager.set_api_key(self.api_key_input.text())
        self.config_manager.set_secret_key(self.secret_key_input.text())
        self.config_manager.set_is_production(self.is_production_input.currentText() == "True")
        self.config_manager.set_debug(self.debug_input.currentText() == "True")
        self.config_manager.set_appearance_mode(self.appearance_input.currentText())

        # Reconfigure logging based on the new debug setting
        debug = self.config_manager.get_debug()
        logging_level = logging.DEBUG if debug else logging.INFO
        logging.getLogger().setLevel(logging_level)  # Update the root logger's level
        logger = logging.getLogger(__name__)
        logger.debug("Logging level set to: %s", logging_level)

        QMessageBox.information(self, "Configuration", "Configuration saved successfully!")
