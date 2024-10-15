# gui.py
import asyncio
import logging
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QTabWidget,
    QStyleFactory,
    QListWidget,
    QApplication,
    QListWidgetItem
)
import re
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette, QColor
from PyQt5.QtCore import Qt, QVariant
from api import API
from config_manager import ConfigManager
import json

# Configure the root logger at the beginning of your file
# but don't set the level yet, it will be done later
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d')

class UexcorpTrader(QWidget):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.api_key = self.config_manager.get_api_key()
        self.is_production = self.config_manager.get_is_production()
        self.debug = self.config_manager.get_debug()  # Read debug setting from config.ini
        self.appearance_mode = self.config_manager.get_appearance_mode()

        # Configure logging level based on the debug setting
        logging_level = logging.DEBUG if self.debug else logging.INFO
        self.logger.setLevel(logging_level)  # Set the level on the logger instance
        self.logger.debug("Logging level set to: %s", logging_level)  # Log the logging level

        self.api = API(
            self.config_manager.get_api_key(), 
            self.config_manager.get_secret_key(),  # Get secret_key here
            self.is_production, 
            self.debug
        )
        self.star_systems = []
        self.planets = []
        self.terminals = []
        self.commodities = []

        self.initUI()
        self.apply_appearance_mode()

    def initUI(self):
        self.setWindowTitle("UEXcorp Trader")
        self.resize(800, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint |
                            Qt.WindowCloseButtonHint)

        tabs = QTabWidget()
        tabs.addTab(self.create_config_tab(), "Configuration")
        tabs.addTab(self.create_trade_tab(), "Trade Commodity")

        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

        # Ensure the load_data function is awaited
        asyncio.ensure_future(self.load_data())

    def create_config_tab(self):
        config_tab = QWidget()
        layout = QVBoxLayout()

        api_key_label = QLabel("UEXcorp API Key:")
        self.api_key_input = QLineEdit(self.api_key)

        secret_key_label = QLabel("UEXcorp Secret Key:")
        self.secret_key_input = QLineEdit(self.config_manager.get_secret_key())
        self.secret_key_input.setEchoMode(QLineEdit.Password)  # Hide the secret key

        is_production_label = QLabel("Is Production:")
        self.is_production_input = QComboBox()
        self.is_production_input.addItems(["False", "True"])
        self.is_production_input.setCurrentText(str(self.is_production))

        debug_label = QLabel("Debug Mode:")
        self.debug_input = QComboBox()
        self.debug_input.addItems(["False", "True"])
        self.debug_input.setCurrentText(str(self.debug))

        appearance_label = QLabel("Appearance Mode:")
        self.appearance_input = QComboBox()
        self.appearance_input.addItems(["Light", "Dark"])
        self.appearance_input.setCurrentText(self.appearance_mode)

        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)

        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(secret_key_label)
        layout.addWidget(self.secret_key_input)
        layout.addWidget(is_production_label)
        layout.addWidget(self.is_production_input)
        layout.addWidget(debug_label)
        layout.addWidget(self.debug_input)
        layout.addWidget(appearance_label)
        layout.addWidget(self.appearance_input)
        layout.addWidget(save_config_button)

        config_tab.setLayout(layout)
        return config_tab

    def create_trade_tab(self):
        trade_tab = QWidget()
        layout = QVBoxLayout()

        system_label = QLabel("Select System:")
        self.system_combo = QComboBox()
        self.system_combo.currentIndexChanged.connect(lambda: self.update_planets(self.system_combo))
        layout.addWidget(system_label)
        layout.addWidget(self.system_combo)

        planet_label = QLabel("Select Planet:")
        self.planet_combo = QComboBox()
        self.planet_combo.currentIndexChanged.connect(lambda: self.update_terminals(self.planet_combo))
        layout.addWidget(planet_label)
        layout.addWidget(self.planet_combo)

        terminal_label = QLabel("Select Terminal:")
        self.terminal_search_input = QLineEdit()
        self.terminal_search_input.setPlaceholderText("Type to search terminals...")
        self.terminal_search_input.textChanged.connect(self.filter_terminals)
        self.terminal_combo = QComboBox()
        self.terminal_combo.setEditable(True)
        self.terminal_combo.currentIndexChanged.connect(lambda: self.update_commodities(self.terminal_combo))
        layout.addWidget(terminal_label)
        layout.addWidget(self.terminal_search_input)
        layout.addWidget(self.terminal_combo)

        commodity_label = QLabel("Select Commodity:")
        self.commodity_list = QListWidget()
        self.commodity_list.currentItemChanged.connect(
            lambda: asyncio.ensure_future(self.update_price(self.commodity_list, self.terminal_combo))  # Correctly schedule the coroutine
        )
        layout.addWidget(commodity_label)
        layout.addWidget(self.commodity_list)

        amount_label = QLabel("Amount (SCU):")
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QIntValidator(0, 1000000))
        layout.addWidget(amount_label)
        layout.addWidget(self.amount_input)

        # Buy Price
        self.buy_price_label = QLabel("Buy Price (UEC/SCU):")
        self.buy_price_input = QLineEdit()
        self.buy_price_input.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.buy_price_input.setReadOnly(True)  # Initially read-only
        layout.addWidget(self.buy_price_label)
        layout.addWidget(self.buy_price_input)

        # Sell Price
        self.sell_price_label = QLabel("Sell Price (UEC/SCU):")
        self.sell_price_input = QLineEdit()
        self.sell_price_input.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.sell_price_input.setReadOnly(True)  # Initially read-only
        layout.addWidget(self.sell_price_label)
        layout.addWidget(self.sell_price_input)

        # Buy Button
        self.buy_button = QPushButton("Buy Commodity")
        self.buy_button.clicked.connect(lambda: asyncio.ensure_future(self.buy_commodity()))
        self.buy_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.buy_button)

        # Sell Button
        self.sell_button = QPushButton("Sell Commodity")
        self.sell_button.clicked.connect(lambda: asyncio.ensure_future(self.sell_commodity()))
        self.sell_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.sell_button)

        trade_tab.setLayout(layout)
        return trade_tab

    async def load_data(self):
        try:
            self.star_systems = await self.api.fetch_data("/star_systems")
            self.log_api_output(f"Star Systems Loaded: {self.star_systems}", level=logging.INFO)
            self.update_system_combos()
        except Exception as e:
            self.log_api_output(f"Error loading initial data: {e}", level=logging.ERROR)

    def update_system_combos(self):
        self.log_api_output("Updating system combos...", level=logging.INFO)
        self.system_combo.clear()
        for star_system in self.star_systems.get("data", []):
            if star_system.get("is_available") == 1:
                self.system_combo.addItem(star_system["name"], star_system["id"])
        self.log_api_output("System combos updated.", level=logging.INFO)

    def update_planets(self, system_combo):
        system_id = system_combo.currentData()
        self.logger.debug(f"Selected system ID: {system_id}")
        if system_id:
            asyncio.ensure_future(self.update_planets_async(system_id, system_combo))

    async def update_planets_async(self, system_id, system_combo):
        try:
            self.planets = await self.api.fetch_data("/planets", params={'id_star_system': system_id})
            self.update_planet_combo()
        except Exception as e:
            self.log_api_output(f"Error loading planets: {e}", level=logging.ERROR)

    def update_planet_combo(self):
        self.planet_combo.clear()
        for planet in self.planets.get("data", []):
            self.planet_combo.addItem(planet["name"], planet["id"])
        self.logger.debug(f"Planets updated: {self.planets}")

    def update_terminals(self, planet_combo):
        planet_id = planet_combo.currentData()
        self.logger.debug(f"Selected planet ID: {planet_id}")
        if planet_id:
            asyncio.ensure_future(self.update_terminals_async(planet_id, planet_combo))

    async def update_terminals_async(self, planet_id, planet_combo):
        try:
            self.terminals = await self.api.fetch_data("/terminals", params={'id_planet': planet_id})
            self.update_terminal_combo()
        except Exception as e:
            self.log_api_output(f"Error loading terminals: {e}", level=logging.ERROR)

    def update_terminal_combo(self):
        self.terminal_combo.clear()
        for terminal in self.terminals.get("data", []):
            if terminal.get("is_available") == 1 and terminal.get("type") == "commodity":
                self.terminal_combo.addItem(terminal["name"], terminal["id"])
        self.logger.debug(f"Terminals updated: {self.terminals}")

    def filter_terminals(self, text):
        self.terminal_combo.clear()
        for terminal in self.terminals.get("data", []):
            if terminal.get("is_available") == 1 and terminal.get("type") == "commodity" and text.lower() in terminal[
                "name"
            ].lower():
                self.terminal_combo.addItem(terminal["name"], terminal["id"])
        # Ensure the first item is selected if available
        if self.terminal_combo.count() > 0:
            self.terminal_combo.setCurrentIndex(0)
            self.update_commodities(self.terminal_combo)

    def update_commodities(self, terminal_combo):
        terminal_id = terminal_combo.currentData()
        self.logger.debug(f"Selected terminal ID: {terminal_id}")
        if terminal_id:
            asyncio.ensure_future(self.update_commodities_async(terminal_id, terminal_combo))

    async def update_commodities_async(self, terminal_id, terminal_combo):
        try:
            self.commodities = await self.api.fetch_data(
                "/commodities_prices", params={'id_terminal': terminal_id}
            )
            self.update_commodity_list()
        except Exception as e:
            self.log_api_output(f"Error loading commodities: {e}", level=logging.ERROR)

    def update_commodity_list(self):
        self.commodity_list.clear()
        for commodity in self.commodities.get("data", []):
            # Store commodity_id as user data, converting to QVariant
            item = QListWidgetItem(commodity["commodity_name"])
            item.setData(Qt.UserRole, QVariant(commodity["id_commodity"])) 
            self.commodity_list.addItem(item)
        self.logger.debug(f"Commodities updated: {self.commodities}")
        
        # Make sure update_price is awaited
        if self.commodity_list.count() > 0:
            asyncio.ensure_future(self.update_price(self.commodity_list, self.terminal_combo))

    async def update_price(self, commodity_list, terminal_combo):
        commodity_name = commodity_list.currentItem().text() if commodity_list.currentItem() else None
        terminal_id = terminal_combo.currentData()
        self.logger.debug(f"Selected commodity name: {commodity_name}, terminal ID: {terminal_id}")
        if commodity_name and terminal_id:
            try:
                prices = await self.api.fetch_data(
                    "/commodities_prices",
                    params={'commodity_name': commodity_name, 'id_terminal': terminal_id},
                )
                if prices and prices.get("data"):
                    buy_price = prices["data"][0]["price_buy"]
                    sell_price = prices["data"][0]["price_sell"]

                    # Update buy price and enable/disable input
                    self.buy_price_input.setText(str(buy_price) if buy_price else "0")
                    self.buy_price_input.setReadOnly(buy_price == 0)
                    self.buy_button.setEnabled(buy_price != 0)

                    # Update sell price and enable/disable input
                    self.sell_price_input.setText(str(sell_price) if sell_price else "0")
                    self.sell_price_input.setReadOnly(sell_price == 0)
                    self.sell_button.setEnabled(sell_price != 0)

            except Exception as e:
                self.log_api_output(f"Error loading prices: {e}", level=logging.ERROR)

    def save_configuration(self, event=None):
        self.api_key = self.api_key_input.text()
        self.config_manager.set_api_key(self.api_key)
        self.config_manager.set_secret_key(self.secret_key_input.text())
        self.is_production = self.is_production_input.currentText() == "True"
        self.config_manager.set_is_production(self.is_production)
        self.debug = self.debug_input.currentText() == "True"
        self.config_manager.set_debug(self.debug)
        self.appearance_mode = self.appearance_input.currentText()
        self.config_manager.set_appearance_mode(self.appearance_mode)

        # Reconfigure logging based on the new debug setting
        logging_level = logging.DEBUG if self.debug else logging.INFO
        self.logger.setLevel(logging_level)  # Update the logger's level
        self.logger.debug("Logging level set to: %s", logging_level)

        # Apply the new appearance mode
        self.apply_appearance_mode()

        # Update API instance with new settings
        self.api.is_production = self.is_production
        self.api.debug = self.debug
        self.api.update_credentials(self.api_key_input.text(), self.secret_key_input.text())

        QMessageBox.information(self, "Configuration", "Configuration saved successfully!")

    def apply_appearance_mode(self):
        if self.appearance_mode == "Dark":
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            dark_palette = self.create_dark_palette()
            QApplication.setPalette(dark_palette)
        else:
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            QApplication.setPalette(QApplication.style().standardPalette())

    def create_dark_palette(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        return dark_palette

    async def buy_commodity(self):
        await self.perform_trade("buy")

    async def sell_commodity(self):
        await self.perform_trade("sell")

    async def perform_trade(self, operation):
        logger = logging.getLogger(__name__)
        try:
            terminal_id = self.terminal_combo.currentData()
            commodity_name = self.commodity_list.currentItem().text() if self.commodity_list.currentItem() else None
            amount = self.amount_input.text()

            logger.debug(f"Attempting trade - Operation: {operation}, Terminal ID: {terminal_id}, Commodity: {commodity_name}, Amount: {amount}")

            if not all([terminal_id, commodity_name, amount]):
                raise ValueError("Please fill all fields.")

            if not re.match(r'^\d+$', amount):
                raise ValueError("Amount must be a valid integer.")

            # Validate terminal and commodity
            if not any(terminal["id"] == terminal_id for terminal in self.terminals.get("data", [])):
                raise ValueError("Selected terminal does not exist.")
            if not any(
                commodity["commodity_name"] == commodity_name for commodity in self.commodities.get("data", [])
            ):
                raise ValueError("Selected commodity does not exist on this terminal.")

            # Get the price from the input field, depending on buy/sell operation
            price = float(self.buy_price_input.text()) if operation == "buy" else float(self.sell_price_input.text())

            current_item = self.commodity_list.currentItem()
            if current_item:
                commodity_id = current_item.data(Qt.UserRole)
            else:
                raise ValueError("Please select a commodity.")

            data = {
                "id_terminal": terminal_id,
                "id_commodity": commodity_id,
                "operation": operation,
                "scu": int(amount),
                "price": price,
                "is_production": int(self.is_production),
            }

            # Serialize data to JSON with double quotes
            json_data = json.dumps(data)
            logger.info(f"API Request: POST {self.api.API_BASE_URL}/user_trades_add/ {json_data}")
            result = await self.api.perform_trade(json_data)

            if result and "data" in result and "id_user_trade" in result["data"]:
                trade_id = result["data"].get('id_user_trade')
                logger.info(f"Trade successful! Trade ID: {trade_id}")
                QMessageBox.information(self, "Success", f"Trade successful! Trade ID: {trade_id}")
            else:
                error_message = result.get('message', 'Unknown error')
                logger.error(f"Trade failed: {error_message}")
                QMessageBox.critical(self, "Error", f"Trade failed: {error_message}")

        except ValueError as e:
            logger.warning(f"Input Error: {e}")
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def log_api_output(self, message, level=logging.INFO):
        self.logger.log(level, message)
