import sys
import asyncio
import logging
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
    QStyleFactory,
    QListWidget,
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette, QColor
from PyQt5.QtCore import Qt
import configparser
import aiohttp
import re
from qasync import QEventLoop, asyncSlot

API_BASE_URL = "https://uexcorp.space/api/2.0"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d')
logger = logging.getLogger(__name__)


def log_function_call(func):
    async def async_wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__} - {func.__code__.co_filename}:{func.__code__.co_firstlineno}")
        result = await func(*args, **kwargs)
        logger.debug(f"Exiting {func.__name__} - {func.__code__.co_filename}:{func.__code__.co_firstlineno}")
        return result

    def sync_wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__} - {func.__code__.co_filename}:{func.__code__.co_firstlineno}")
        result = func(*args, **kwargs)
        logger.debug(f"Exiting {func.__name__} - {func.__code__.co_filename}:{func.__code__.co_firstlineno}")
        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class ConfigManager:
    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    @log_function_call
    def load_config(self):
        self.config.read(self.config_file)

    @log_function_call
    def save_config(self):
        with open(self.config_file, "w") as f:
            self.config.write(f)

    @log_function_call
    def get_api_key(self):
        return self.config.get("API", "key", fallback="")

    @log_function_call
    def set_api_key(self, key):
        self.config["API"] = {"key": key}
        self.save_config()

    @log_function_call
    def get_is_production(self):
        return self.config.getboolean("SETTINGS", "is_production", fallback=False)

    @log_function_call
    def set_is_production(self, is_production):
        self.config["SETTINGS"] = {"is_production": str(is_production)}
        self.save_config()

    @log_function_call
    def get_debug(self):
        return self.config.getboolean("SETTINGS", "debug", fallback=False)

    @log_function_call
    def set_debug(self, debug):
        self.config["SETTINGS"]["debug"] = str(debug)
        self.save_config()

    @log_function_call
    def get_appearance_mode(self):
        return self.config.get("SETTINGS", "appearance_mode", fallback="Light")

    @log_function_call
    def set_appearance_mode(self, mode):
        self.config["SETTINGS"]["appearance_mode"] = mode
        self.save_config()


class UexcorpTrader(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.api_key = self.config_manager.get_api_key()
        self.is_production = self.config_manager.get_is_production()
        self.debug = self.config_manager.get_debug()
        self.appearance_mode = self.config_manager.get_appearance_mode()

        # Configure logging based on the debug setting
        logging_level = logging.DEBUG if self.debug else logging.INFO
        logging.getLogger().setLevel(logging_level)

        # Set logger as an instance attribute
        self.logger = logging.getLogger(__name__)

        self.star_systems = []
        self.planets = []
        self.terminals = []
        self.commodities = []

        self.initUI()
        self.apply_appearance_mode()

    @log_function_call
    def initUI(self):
        self.setWindowTitle("UEXcorp Trader")
        self.resize(800, 600)  # Set initial window size
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

    @log_function_call
    def create_config_tab(self):
        config_tab = QWidget()
        layout = QVBoxLayout()

        api_key_label = QLabel("UEXcorp API Key:")
        self.api_key_input = QLineEdit(self.api_key)

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
        layout.addWidget(is_production_label)
        layout.addWidget(self.is_production_input)
        layout.addWidget(debug_label)
        layout.addWidget(self.debug_input)
        layout.addWidget(appearance_label)
        layout.addWidget(self.appearance_input)
        layout.addWidget(save_config_button)

        config_tab.setLayout(layout)
        return config_tab

    @log_function_call
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
        self.commodity_list = QListWidget()  # Use QListWidget for scrolling
        self.commodity_list.currentItemChanged.connect(
            lambda: self.update_price(self.commodity_list, self.terminal_combo)
        )
        layout.addWidget(commodity_label)
        layout.addWidget(self.commodity_list)

        amount_label = QLabel("Amount (SCU):")
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QIntValidator(0, 1000000))  # Allow only integers
        self.buy_price_label = QLabel("Buy Price (UEC/SCU):")  # Label for buy price
        self.buy_price_label.setText("Buy Price (UEC/SCU):")
        self.sell_price_label = QLabel("Sell Price (UEC/SCU):")  # Label for sell price
        self.sell_price_label.setText("Sell Price (UEC/SCU):")
        layout.addWidget(amount_label)
        layout.addWidget(self.amount_input)
        layout.addWidget(self.buy_price_label)  # Add buy price label to layout
        layout.addWidget(self.sell_price_label)  # Add sell price label to layout

        buy_button = QPushButton("Buy Commodity")
        buy_button.clicked.connect(lambda: asyncio.ensure_future(self.buy_commodity()))
        layout.addWidget(buy_button)

        sell_button = QPushButton("Sell Commodity")
        sell_button.clicked.connect(lambda: asyncio.ensure_future(self.sell_commodity()))
        layout.addWidget(sell_button)

        trade_tab.setLayout(layout)
        return trade_tab

    @log_function_call
    async def load_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                self.star_systems = await self.fetch_data(session, "/star_systems")
                self.log_api_output(f"Star Systems Loaded: {self.star_systems}", level=logging.INFO)
                self.update_system_combos()

        except Exception as e:
            self.log_api_output(f"Error loading initial data: {e}", level=logging.ERROR)

    @log_function_call
    async def fetch_data(self, session, endpoint, params=None):
        url = f"{API_BASE_URL}{endpoint}"
        self.log_api_output(f"API Request: GET {url} {params if params else ''}", level=logging.DEBUG)
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_api_output(f"API Response: {data}", level=logging.DEBUG)
                    return data
                else:
                    error_message = await response.text()
                    self.log_api_output(
                        f"API request failed with status {response.status}: {error_message}", level=logging.ERROR
                    )
                    return []
        except Exception as e:
            self.log_api_output(f"Error during API request to {url}: {e}", level=logging.ERROR)
            return []

    @log_function_call
    def update_system_combos(self):
        self.log_api_output("Updating system combos...", level=logging.INFO)
        self.system_combo.clear()
        for star_system in self.star_systems.get("data", []):
            if star_system.get("is_available") == 1:
                self.system_combo.addItem(star_system["name"], star_system["id"])
        self.log_api_output("System combos updated.", level=logging.INFO)

    @log_function_call
    def update_planets(self, system_combo):
        system_id = system_combo.currentData()
        self.logger.debug(f"Selected system ID: {system_id}")
        if system_id:
            asyncio.ensure_future(self.update_planets_async(system_id, system_combo))

    @log_function_call
    async def update_planets_async(self, system_id, system_combo):
        try:
            async with aiohttp.ClientSession() as session:
                self.planets = await self.fetch_data(session, "/planets", params={'id_star_system': system_id})
                self.update_planet_combo()
        except Exception as e:
            self.log_api_output(f"Error loading planets: {e}", level=logging.ERROR)

    @log_function_call
    def update_planet_combo(self):
        self.planet_combo.clear()
        for planet in self.planets.get("data", []):
            self.planet_combo.addItem(planet["name"], planet["id"])
        self.logger.debug(f"Planets updated: {self.planets}")

    @log_function_call
    def update_terminals(self, planet_combo):
        planet_id = planet_combo.currentData()
        self.logger.debug(f"Selected planet ID: {planet_id}")
        if planet_id:
            asyncio.ensure_future(self.update_terminals_async(planet_id, planet_combo))

    @log_function_call
    async def update_terminals_async(self, planet_id, planet_combo):
        try:
            async with aiohttp.ClientSession() as session:
                self.terminals = await self.fetch_data(session, "/terminals", params={'id_planet': planet_id})
                self.update_terminal_combo()
        except Exception as e:
            self.log_api_output(f"Error loading terminals: {e}", level=logging.ERROR)

    @log_function_call
    def update_terminal_combo(self):
        self.terminal_combo.clear()
        for terminal in self.terminals.get("data", []):
            if terminal.get("is_available") == 1 and terminal.get("type") == "commodity":
                self.terminal_combo.addItem(terminal["name"], terminal["id"])
        self.logger.debug(f"Terminals updated: {self.terminals}")

    @log_function_call
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

    @log_function_call
    def update_commodities(self, terminal_combo):
        terminal_id = terminal_combo.currentData()
        self.logger.debug(f"Selected terminal ID: {terminal_id}")
        if terminal_id:
            asyncio.ensure_future(self.update_commodities_async(terminal_id, terminal_combo))

    @log_function_call
    async def update_commodities_async(self, terminal_id, terminal_combo):
        try:
            async with aiohttp.ClientSession() as session:
                self.commodities = await self.fetch_data(
                    session, "/commodities_prices", params={'id_terminal': terminal_id}
                )
                self.update_commodity_list()
        except Exception as e:
            self.log_api_output(f"Error loading commodities: {e}", level=logging.ERROR)

    @log_function_call
    def update_commodity_list(self):
        self.commodity_list.clear()
        for commodity in self.commodities.get("data", []):
            self.commodity_list.addItem(commodity["commodity_name"])
        self.logger.debug(f"Commodities updated: {self.commodities}")

    @log_function_call
    def update_price(self, commodity_list, terminal_combo):
        commodity_name = commodity_list.currentItem().text() if commodity_list.currentItem() else None
        terminal_id = terminal_combo.currentData()
        self.logger.debug(f"Selected commodity name: {commodity_name}, terminal ID: {terminal_id}")
        if commodity_name and terminal_id:
            asyncio.ensure_future(
                self.update_price_async(commodity_name, terminal_id, commodity_list)
            )

    @log_function_call
    async def update_price_async(self, commodity_name, terminal_id, commodity_list):
        try:
            async with aiohttp.ClientSession() as session:
                prices = await self.fetch_data(
                    session,
                    "/commodities_prices",
                    params={'commodity_name': commodity_name, 'id_terminal': terminal_id},
                )
                if prices and prices.get("data"):
                    buy_price = prices["data"][0]["price_buy"]
                    sell_price = prices["data"][0]["price_sell"]
                    self.buy_price_label.setText(f"Buy Price (UEC/SCU): {buy_price if buy_price else 'N/A'}")
                    self.sell_price_label.setText(f"Sell Price (UEC/SCU): {sell_price if sell_price else 'N/A'}")
        except Exception as e:
            self.log_api_output(f"Error loading prices: {e}", level=logging.ERROR)

    @log_function_call
    def save_configuration(self, event=None):
        self.api_key = self.api_key_input.text()
        self.config_manager.set_api_key(self.api_key)
        self.is_production = self.is_production_input.currentText() == "True"
        self.config_manager.set_is_production(self.is_production)
        self.debug = self.debug_input.currentText() == "True"
        self.config_manager.set_debug(self.debug)
        self.appearance_mode = self.appearance_input.currentText()
        self.config_manager.set_appearance_mode(self.appearance_mode)

        # Reconfigure logging based on the new debug setting
        logging_level = logging.DEBUG if self.debug else logging.INFO
        logging.getLogger().setLevel(logging_level)

        # Apply the new appearance mode
        self.apply_appearance_mode()

        QMessageBox.information(self, "Configuration", "Configuration saved successfully!")

    @log_function_call
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

    @log_function_call
    async def buy_commodity(self):
        await self.perform_trade("buy")

    @log_function_call
    async def sell_commodity(self):
        await self.perform_trade("sell")

    @log_function_call
    async def perform_trade(self, operation):
        try:
            terminal_id = self.terminal_combo.currentData()
            commodity_name = self.commodity_list.currentItem().text() if self.commodity_list.currentItem() else None
            amount = self.amount_input.text()

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

            # Get the correct price based on the operation
            price_key = "price_buy" if operation == "buy" else "price_sell"
            price = next(
                (
                    commodity[price_key]
                    for commodity in self.commodities.get("data", [])
                    if commodity["commodity_name"] == commodity_name
                ),
                None,
            )
            if price is None:
                raise ValueError(f"No {operation} price found for this commodity.")

            data = {
                "id_terminal": terminal_id,
                "commodity_name": commodity_name,
                "operation": operation,
                "scu": int(amount),
                "price": float(price),
                "is_production": int(self.is_production),  # Use the loaded configuration boolean
            }

            self.log_api_output(f"API Request: POST {API_BASE_URL}/user_trades_add/ {data}", level=logging.INFO)
            async with aiohttp.ClientSession(headers={"secret_key": self.api_key}) as session:
                async with session.post(f"{API_BASE_URL}/user_trades_add/", json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        QMessageBox.information(self, "Success", f"Trade successful! Trade ID: {result.get('id_user_trade')}")
                    else:
                        error_message = await response.text()
                        self.log_api_output(
                            f"API request failed with status {response.status}: {error_message}", level=logging.ERROR
                        )
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    @log_function_call
    def log_api_output(self, message, level=logging.INFO):
        self.logger.log(level, message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    trader = UexcorpTrader()
    trader.show()

    with loop:
        loop.run_forever()
