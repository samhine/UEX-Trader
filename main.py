import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QTabWidget,
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
        self.terminals = []
        self.commodities = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle("UEXcorp Trader")

        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_config_tab(), "Configuration")
        tabs.addTab(self.create_buy_tab(), "Buy Commodity")
        tabs.addTab(self.create_sell_tab(), "Sell Commodity")

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

        # Load data
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.load_data())

    def create_config_tab(self):
        config_tab = QWidget()
        layout = QVBoxLayout()

        # API Key
        api_key_label = QLabel("UEXcorp API Key:")
        self.api_key_input = QLineEdit(self.api_key)
        save_api_key_button = QPushButton("Save API Key")
        save_api_key_button.clicked.connect(self.save_api_key)

        layout.addWidget(api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(save_api_key_button)

        config_tab.setLayout(layout)
        return config_tab

    def create_buy_tab(self):
        buy_tab = QWidget()
        layout = QVBoxLayout()

        # Terminal Selection
        terminal_label = QLabel("Select Terminal:")
        self.terminal_combo = QComboBox()
        layout.addWidget(terminal_label)
        layout.addWidget(self.terminal_combo)

        # Commodity Selection
        commodity_label = QLabel("Select Commodity:")
        self.commodity_combo = QComboBox()
        layout.addWidget(commodity_label)
        layout.addWidget(self.commodity_combo)

        # Amount and Price
        amount_label = QLabel("Amount (SCU):")
        self.amount_input = QLineEdit()
        price_label = QLabel("Price (UEC/SCU):")
        self.price_input = QLineEdit()
        layout.addWidget(amount_label)
        layout.addWidget(self.amount_input)
        layout.addWidget(price_label)
        layout.addWidget(self.price_input)

        # Buy Button
        buy_button = QPushButton("Buy Commodity")
        buy_button.clicked.connect(self.buy_commodity)
        layout.addWidget(buy_button)

        buy_tab.setLayout(layout)
        return buy_tab

    def create_sell_tab(self):
        # Similar structure to buy_tab, adjust labels and button connection
        sell_tab = QWidget()
        layout = QVBoxLayout()

        # Terminal Selection
        terminal_label = QLabel("Select Terminal:")
        self.sell_terminal_combo = QComboBox()
        layout.addWidget(terminal_label)
        layout.addWidget(self.sell_terminal_combo)

        # Commodity Selection
        commodity_label = QLabel("Select Commodity:")
        self.sell_commodity_combo = QComboBox()
        layout.addWidget(commodity_label)
        layout.addWidget(self.sell_commodity_combo)

        # Amount and Price
        amount_label = QLabel("Amount (SCU):")
        self.sell_amount_input = QLineEdit()
        price_label = QLabel("Price (UEC/SCU):")
        self.sell_price_input = QLineEdit()
        layout.addWidget(amount_label)
        layout.addWidget(self.sell_amount_input)
        layout.addWidget(price_label)
        layout.addWidget(self.sell_price_input)

        # Sell Button
        sell_button = QPushButton("Sell Commodity")
        sell_button.clicked.connect(self.sell_commodity)
        layout.addWidget(sell_button)

        sell_tab.setLayout(layout)
        return sell_tab

    async def load_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                self.terminals = await self.fetch_data(session, "/terminals")
                self.commodities = await self.fetch_data(session, "/commodities")

            self.update_terminal_combos()
            self.update_commodity_combos()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    async def fetch_data(self, session, endpoint):
        url = f"{API_BASE_URL}{endpoint}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API request failed with status {response.status}")

    def update_terminal_combos(self):
        self.terminal_combo.clear()
        self.sell_terminal_combo.clear()
        for terminal in self.terminals:
            self.terminal_combo.addItem(terminal["name"], terminal["id"])
            self.sell_terminal_combo.addItem(terminal["name"], terminal["id"])

    def update_commodity_combos(self):
        self.commodity_combo.clear()
        self.sell_commodity_combo.clear()
        for commodity in self.commodities:
            self.commodity_combo.addItem(commodity["name"], commodity["id"])
            self.sell_commodity_combo.addItem(commodity["name"], commodity["id"])

    def save_api_key(self):
        self.api_key = self.api_key_input.text()
        self.config_manager.set_api_key(self.api_key)
        QMessageBox.information(self, "API Key", "API key saved successfully!")

    async def buy_commodity(self):
        await self.perform_trade("buy")

    async def sell_commodity(self):
        await self.perform_trade("sell")

    async def perform_trade(self, operation):
        try:
            terminal_id = (
                self.terminal_combo.currentData()
                if operation == "buy"
                else self.sell_terminal_combo.currentData()
            )
            commodity_id = (
                self.commodity_combo.currentData()
                if operation == "buy"
                else self.sell_commodity_combo.currentData()
            )
            amount = (
                int(self.amount_input.text())
                if operation == "buy"
                else int(self.sell_amount_input.text())
            )
            price = (
                float(self.price_input.text())
                if operation == "buy"
                else float(self.sell_price_input.text())
            )

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

            async with aiohttp.ClientSession(
                headers={"secret_key": self.api_key}
            ) as session:
                async with session.post(
                    f"{API_BASE_URL}/user_trades_add/", json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        QMessageBox.information(
                            self,
                            "Success",
                            f"Trade successful! Trade ID: {result.get('id_user_trade')}",
                        )
                    else:
                        error_message = await response.text()
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Trade failed with status {response.status}: {error_message}",
                        )
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    trader = UexcorpTrader()
    trader.show()
    sys.exit(app.exec_())
