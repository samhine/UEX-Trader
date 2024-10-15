import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QTabWidget,
    QTextEdit,
)
from PyQt5.QtCore import Qt
import configparser
import aiohttp

API_BASE_URL = "https://uexcorp.space/api/2.0"


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


class UexcorpTrader(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.api_key = self.config_manager.get_api_key()
        self.star_systems = []
        self.planets = []
        self.terminals = []
        self.commodities = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle("UEXcorp Trader")
        self.showFullScreen()

        tabs = QTabWidget()
        tabs.addTab(self.create_config_tab(), "Configuration")
        tabs.addTab(self.create_trade_tab("Buy Commodity", self.buy_commodity), "Buy Commodity")
        tabs.addTab(self.create_trade_tab("Sell Commodity", self.sell_commodity), "Sell Commodity")

        self.api_output = QTextEdit()
        self.api_output.setReadOnly(True)

        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        main_layout.addWidget(self.api_output)
        self.setLayout(main_layout)

        asyncio.ensure_future(self.load_data())

    def create_config_tab(self):
        config_tab = QWidget()
        layout = QVBoxLayout()

        api_key_label = QLabel("UEXcorp API Key:")
        self.api_key_input = QLineEdit(self.api_key)
        save_api_key_button = QPushButton("Save API Key")
        save_api_key_button.clicked.connect(self.save_api_key)

        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(save_api_key_button)

        config_tab.setLayout(layout)
        return config_tab

    def create_trade_tab(self, title, trade_function):
        trade_tab = QWidget()
        layout = QVBoxLayout()

        system_label = QLabel("Select System:")
        system_combo = QComboBox()
        system_combo.currentIndexChanged.connect(lambda: self.update_planets(system_combo))
        layout.addWidget(system_label)
        layout.addWidget(system_combo)

        planet_label = QLabel("Select Planet:")
        planet_combo = QComboBox()
        planet_combo.currentIndexChanged.connect(lambda: self.update_terminals(planet_combo))
        layout.addWidget(planet_label)
        layout.addWidget(planet_combo)

        terminal_label = QLabel("Select Terminal:")
        terminal_combo = QComboBox()
        terminal_combo.currentIndexChanged.connect(lambda: self.update_commodities(terminal_combo))
        layout.addWidget(terminal_label)
        layout.addWidget(terminal_combo)

        commodity_label = QLabel("Select Commodity:")
        commodity_combo = QComboBox()
        layout.addWidget(commodity_label)
        layout.addWidget(commodity_combo)

        amount_label = QLabel("Amount (SCU):")
        amount_input = QLineEdit()
        price_label = QLabel("Price (UEC/SCU):")
        price_input = QLineEdit()
        layout.addWidget(amount_label)
        layout.addWidget(amount_input)
        layout.addWidget(price_label)
        layout.addWidget(price_input)

        trade_button = QPushButton(title)
        trade_button.clicked.connect(lambda: asyncio.ensure_future(trade_function(system_combo, planet_combo, terminal_combo, commodity_combo, amount_input, price_input)))
        layout.addWidget(trade_button)

        trade_tab.setLayout(layout)
        return trade_tab

    async def load_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                self.star_systems = await self.fetch_data(session, "/star_systems")
                self.update_system_combos()

        except Exception as e:
            self.log_api_output(f"Error loading initial data: {e}")

    async def fetch_data(self, session, endpoint, params=None):
        url = f"{API_BASE_URL}{endpoint}"
        self.log_api_output(f"API Request: GET {url} {params if params else ''}")
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_message = await response.text()
                    self.log_api_output(f"API request failed with status {response.status}: {error_message}")
                    return []
        except Exception as e:
            self.log_api_output(f"Error during API request to {url}: {e}")
            return []

    def update_system_combos(self):
        for combo in [self.findChild(QComboBox, "system_combo"), self.findChild(QComboBox, "sell_system_combo")]:
            if combo:
                combo.clear()
                for star_system in self.star_systems["data"]:
                    if star_system["is_available"] == 1:
                        combo.addItem(star_system["name"], star_system["id"])

    def update_planets(self, system_combo):
        system_id = system_combo.currentData()
        if system_id:
            asyncio.ensure_future(self.update_planets_async(system_id, system_combo))

    async def update_planets_async(self, system_id, system_combo):
        try:
            async with aiohttp.ClientSession() as session:
                self.planets = await self.fetch_data(session, "/planets", params={'id_star_system': system_id})
                self.update_planet_combo(system_combo)
        except Exception as e:
            self.log_api_output(f"Error loading planets: {e}")

    def update_planet_combo(self, system_combo):
        planet_combo = system_combo.parent().findChild(QComboBox, "planet_combo")
        if planet_combo:
            planet_combo.clear()
            for planet in self.planets:
                planet_combo.addItem(planet["name"], planet["id"])

    def update_terminals(self, planet_combo):
        planet_id = planet_combo.currentData()
        if planet_id:
            asyncio.ensure_future(self.update_terminals_async(planet_id, planet_combo))

    async def update_terminals_async(self, planet_id, planet_combo):
        try:
            async with aiohttp.ClientSession() as session:
                self.terminals = await self.fetch_data(session, "/terminals", params={'id_planet': planet_id})
                self.update_terminal_combo(planet_combo)
        except Exception as e:
            self.log_api_output(f"Error loading terminals: {e}")

    def update_terminal_combo(self, planet_combo):
        terminal_combo = planet_combo.parent().findChild(QComboBox, "terminal_combo")
        if terminal_combo:
            terminal_combo.clear()
            for terminal in self.terminals:
                terminal_combo.addItem(terminal["name"], terminal["id"])

    def update_commodities(self, terminal_combo):
        terminal_id = terminal_combo.currentData()
        if terminal_id:
            asyncio.ensure_future(self.update_commodities_async(terminal_id, terminal_combo))

    async def update_commodities_async(self, terminal_id, terminal_combo):
        try:
            async with aiohttp.ClientSession() as session:
                self.commodities = await self.fetch_data(session, "/commodities_prices", params={'id_terminal': terminal_id})
                self.update_commodity_combo(terminal_combo)
        except Exception as e:
            self.log_api_output(f"Error loading commodities: {e}")

    def update_commodity_combo(self, terminal_combo):
        commodity_combo = terminal_combo.parent().findChild(QComboBox, "commodity_combo")
        if commodity_combo:
            commodity_combo.clear()
            for commodity in self.commodities:
                commodity_combo.addItem(commodity["commodity_name"], commodity["id_commodity"])

    def save_api_key(self):
        self.api_key = self.api_key_input.text()
        self.config_manager.set_api_key(self.api_key)
        QMessageBox.information(self, "API Key", "API key saved successfully!")

    async def buy_commodity(self, system_combo, planet_combo, terminal_combo, commodity_combo, amount_input, price_input):
        await self.perform_trade("buy", system_combo, planet_combo, terminal_combo, commodity_combo, amount_input, price_input)

    async def sell_commodity(self, system_combo, planet_combo, terminal_combo, commodity_combo, amount_input, price_input):
        await self.perform_trade("sell", system_combo, planet_combo, terminal_combo, commodity_combo, amount_input, price_input)

    async def perform_trade(self, operation, system_combo, planet_combo, terminal_combo, commodity_combo, amount_input, price_input):
        try:
            terminal_id = terminal_combo.currentData()
            commodity_id = commodity_combo.currentData()
            amount = int(amount_input.text())
            price = float(price_input.text())

            if not all([terminal_id, commodity_id, amount, price]):
                raise ValueError("Please fill all fields.")

            data = {
                "id_terminal": terminal_id,
                "id_commodity": commodity_id,
                "operation": operation,
                "scu": amount,
                "price": price,
                "is_production": 0,  # Assuming not production
            }

            self.log_api_output(f"API Request: POST {API_BASE_URL}/user_trades_add/ {data}")
            async with aiohttp.ClientSession(headers={"secret_key": self.api_key}) as session:
                async with session.post(f"{API_BASE_URL}/user_trades_add/", json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        QMessageBox.information(self, "Success", f"Trade successful! Trade ID: {result.get('id_user_trade')}")
                    else:
                        error_message = await response.text()
                        self.log_api_output(f"API request failed with status {response.status}: {error_message}")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def log_api_output(self, message):
        self.api_output.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    trader = UexcorpTrader()
    trader.show()
    sys.exit(app.exec_())
