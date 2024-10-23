import logging
import json
import re
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QListWidget, QLineEdit, QPushButton, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
import asyncio
from api import API
from config_manager import ConfigManager

class TradeTab(QWidget):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self.config_manager = ConfigManager()
        self.api = API(
            self.config_manager.get_api_key(),
            self.config_manager.get_secret_key(),
            self.config_manager.get_is_production(),
            self.config_manager.get_debug()
        )
        self.commodities = []
        self.terminals = []
        self.initUI()
        asyncio.ensure_future(self.load_systems())

    def initUI(self):
        main_layout = QVBoxLayout()

        system_label = QLabel("Select System:")
        self.system_combo = QComboBox()
        self.system_combo.currentIndexChanged.connect(lambda: asyncio.ensure_future(self.update_planets()))
        main_layout.addWidget(system_label)
        main_layout.addWidget(self.system_combo)

        planet_label = QLabel("Select Planet:")
        self.planet_combo = QComboBox()
        self.planet_combo.currentIndexChanged.connect(lambda: asyncio.ensure_future(self.update_terminals()))
        main_layout.addWidget(planet_label)
        main_layout.addWidget(self.planet_combo)

        terminal_label = QLabel("Select Terminal:")
        self.terminal_filter_input = QLineEdit()
        self.terminal_filter_input.setPlaceholderText("Filter Terminals")
        self.terminal_filter_input.textChanged.connect(self.filter_terminals)
        self.terminal_combo = QComboBox()
        self.terminal_combo.currentIndexChanged.connect(lambda: asyncio.ensure_future(self.update_commodities()))
        main_layout.addWidget(terminal_label)
        main_layout.addWidget(self.terminal_filter_input)
        main_layout.addWidget(self.terminal_combo)

        commodity_buy_label = QLabel("Commodities to Buy:")
        self.commodity_buy_list = QListWidget()
        self.commodity_buy_list.currentItemChanged.connect(self.update_buy_price)
        main_layout.addWidget(commodity_buy_label)
        main_layout.addWidget(self.commodity_buy_list)

        commodity_sell_label = QLabel("Commodities to Sell:")
        self.commodity_sell_list = QListWidget()
        self.commodity_sell_list.currentItemChanged.connect(self.update_sell_price)
        main_layout.addWidget(commodity_sell_label)
        main_layout.addWidget(self.commodity_sell_list)

        amount_label = QLabel("Amount (SCU):")
        self.amount_input = QLineEdit()
        main_layout.addWidget(amount_label)
        main_layout.addWidget(self.amount_input)

        buy_price_label = QLabel("Buy Price:")
        self.buy_price_input = QLineEdit()
        main_layout.addWidget(buy_price_label)
        main_layout.addWidget(self.buy_price_input)

        sell_price_label = QLabel("Sell Price:")
        self.sell_price_input = QLineEdit()
        main_layout.addWidget(sell_price_label)
        main_layout.addWidget(self.sell_price_input)

        self.buy_button = QPushButton("Buy Commodity")
        self.buy_button.setEnabled(False)
        self.buy_button.clicked.connect(lambda: asyncio.ensure_future(self.buy_commodity()))
        main_layout.addWidget(self.buy_button)

        self.sell_button = QPushButton("Sell Commodity")
        self.sell_button.setEnabled(False)
        self.sell_button.clicked.connect(lambda: asyncio.ensure_future(self.sell_commodity()))
        main_layout.addWidget(self.sell_button)

        self.setLayout(main_layout)

    async def load_systems(self):
        try:
            systems = await self.api.fetch_data("/star_systems")
            for system in systems.get("data", []):
                if system.get("is_available") == 1:
                    self.system_combo.addItem(system["name"], system["id"])
            logging.info("Systems loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load systems: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load systems: {e}")

    async def update_planets(self):
        self.planet_combo.clear()
        system_id = self.system_combo.currentData()
        if not system_id:
            return
        try:
            planets = await self.api.fetch_data("/planets", params={'id_star_system': system_id})
            for planet in planets.get("data", []):
                self.planet_combo.addItem(planet["name"], planet["id"])
            logging.info("Planets loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load planets: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load planets: {e}")

    async def update_terminals(self):
        self.terminal_combo.clear()
        self.terminal_filter_input.clear()
        self.terminals = []
        planet_id = self.planet_combo.currentData()
        if not planet_id:
            return
        try:
            terminals = await self.api.fetch_data("/terminals", params={'id_planet': planet_id})
            self.terminals = [terminal for terminal in terminals.get("data", []) if terminal.get("type") == "commodity" and terminal.get("is_available") == 1]
            self.filter_terminals()
            logging.info("Terminals loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load terminals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load terminals: {e}")

    def filter_terminals(self):
        filter_text = self.terminal_filter_input.text().lower()
        self.terminal_combo.clear()
        for terminal in self.terminals:
            if filter_text in terminal["name"].lower():
                self.terminal_combo.addItem(terminal["name"], terminal["id"])

    async def update_commodities(self):
        self.commodity_buy_list.clear()
        self.commodity_sell_list.clear()
        self.buy_price_input.clear()
        self.sell_price_input.clear()
        self.buy_button.setEnabled(False)
        self.sell_button.setEnabled(False)
        terminal_id = self.terminal_combo.currentData()
        if not terminal_id:
            return
        try:
            commodities = await self.api.fetch_data("/commodities_prices", params={'id_terminal': terminal_id})
            self.commodities = commodities.get("data", [])
            for commodity in self.commodities:
                item = QListWidgetItem(commodity["commodity_name"])
                item.setData(Qt.UserRole, commodity["id_commodity"])
                if commodity["price_buy"] > 0:
                    self.commodity_buy_list.addItem(item)
                if commodity["price_sell"] > 0:
                    self.commodity_sell_list.addItem(item)
            logging.info("Commodities loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load commodities: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load commodities: {e}")

    def update_buy_price(self, current, previous):
        if current:
            commodity_id = current.data(Qt.UserRole)
            commodity = next((c for c in self.commodities if c["id_commodity"] == commodity_id), None)
            if commodity:
                self.buy_price_input.setText(str(commodity["price_buy"]))
            self.buy_button.setEnabled(True)
        else:
            self.buy_price_input.clear()
            self.buy_button.setEnabled(False)

    def update_sell_price(self, current, previous):
        if current:
            commodity_id = current.data(Qt.UserRole)
            commodity = next((c for c in self.commodities if c["id_commodity"] == commodity_id), None)
            if commodity:
                self.sell_price_input.setText(str(commodity["price_sell"]))
            self.sell_button.setEnabled(True)
        else:
            self.sell_price_input.clear()
            self.sell_button.setEnabled(False)

    async def buy_commodity(self):
        await self.perform_trade(self.commodity_buy_list, is_buy=True)

    async def sell_commodity(self):
        await self.perform_trade(self.commodity_sell_list, is_buy=False)

    async def perform_trade(self, commodity_list, is_buy):
        selected_item = commodity_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Error", "Please select a commodity.")
            return
        
        operation = "sell"
        price_input = self.sell_price_input
        if is_buy:
            operation = "buy"
            price_input = self.buy_price_input

        logger = logging.getLogger(__name__)
        try:
            planet_id = self.planet_combo.currentData()
            terminal_id = self.terminal_combo.currentData()
            id_commodity = selected_item.data(Qt.UserRole)
            amount = self.amount_input.text()
            price = price_input.text()

            logger.debug(f"Attempting trade - Operation: {operation}, Terminal ID: {terminal_id}, Commodity ID: {id_commodity}, Amount: {amount}, Price: {price}")

            if not all([terminal_id, id_commodity, amount, price]):
                raise ValueError("Please fill all fields.")

            if not re.match(r'^\d+$', amount):
                raise ValueError("Amount must be a valid integer.")

            if not re.match(r'^\d+(\.\d+)?$', price):
                raise ValueError("Price must be a valid number.")

            # Validate terminal and commodity
            terminals = await self.api.fetch_data("/terminals", params={'id_planet': planet_id})
            if not any(terminal.get('id') == terminal_id for terminal in terminals.get("data", [])):
                raise ValueError("Selected terminal does not exist.")
            if not any(
                commodity["id_commodity"] == id_commodity for commodity in self.commodities
            ):
                raise ValueError("Selected commodity does not exist on this terminal.")

            data = {
                "id_terminal": terminal_id,
                "id_commodity": id_commodity,
                "operation": operation,
                "scu": int(amount),
                "price": float(price),
                "is_production": int(self.config_manager.get_is_production()),
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
