# gui.py
import asyncio
import logging
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QTabWidget,
    QStyleFactory,
    QListWidget,
    QApplication,
    QListWidgetItem,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
import re
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QVariant
from api import API
from config_manager import ConfigManager
import json
import sys

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
        self.terminals = {}
        self.commodities = []

        self.initUI()
        self.apply_appearance_mode()

        # Load and set the window size
        width, height = self.config_manager.get_window_size()
        self.resize(width, height)

    def initUI(self):
        self.setWindowTitle("UEXcorp Trader")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint |
                            Qt.WindowCloseButtonHint)

        self.setWindowIcon(QIcon("resources/UEXTrader_icon_resized.png"))

        tabs = QTabWidget()
        tabs.addTab(self.create_config_tab(), "Configuration")
        tabs.addTab(self.create_trade_tab(), "Trade Commodity")
        tabs.addTab(self.create_trade_route_tab(), "Find Trade Route")  # Add the new tab

        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

        # Ensure the load_data function is awaited
        asyncio.ensure_future(self.load_data())
        
    def closeEvent(self, event):
        self.config_manager.set_window_size(self.width(), self.height())
        super().closeEvent(event)

    def create_config_tab(self):
        config_tab = QWidget()
        layout = QVBoxLayout()

        api_key_label = QLabel("UEXcorp API Key:")
        self.api_key_input = QLineEdit(self.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)  # Hide the api key

        # Create the eye button
        self.show_api_key_button = QPushButton("👁", self)
        self.show_api_key_button.setFixedSize(30, 30)  # Adjust size as needed# Connect button press and release events
        self.show_api_key_button.pressed.connect(self.show_api_key)
        self.show_api_key_button.released.connect(self.hide_api_key)

        secret_key_label = QLabel("UEXcorp Secret Key:")
        self.secret_key_input = QLineEdit(self.config_manager.get_secret_key())
        self.secret_key_input.setEchoMode(QLineEdit.Password)  # Hide the secret key

        # Create the eye button
        self.show_secret_key_button = QPushButton("👁", self)
        self.show_secret_key_button.setFixedSize(30, 30)  # Adjust size as needed# Connect button press and release events
        self.show_secret_key_button.pressed.connect(self.show_secret_key)
        self.show_secret_key_button.released.connect(self.hide_secret_key)

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

        config_tab.setLayout(layout)
        return config_tab

    def show_api_key(self):
        self.api_key_input.setEchoMode(QLineEdit.Normal)

    def hide_api_key(self):
        self.api_key_input.setEchoMode(QLineEdit.Password)

    def show_secret_key(self):
        self.secret_key_input.setEchoMode(QLineEdit.Normal)

    def hide_secret_key(self):
        self.secret_key_input.setEchoMode(QLineEdit.Password)

    def create_trade_tab(self):
        trade_tab = QWidget()
        main_layout = QVBoxLayout()

        system_label = QLabel("Select System:")
        self.system_combo = QComboBox()
        self.system_combo.setObjectName("trade_tab-system_combo")  # Set objectName
        self.system_combo.currentIndexChanged.connect(lambda: self.update_planets(self.system_combo, self.planet_combo))
        main_layout.addWidget(system_label)
        main_layout.addWidget(self.system_combo)

        planet_label = QLabel("Select Planet:")
        self.planet_combo = QComboBox()
        self.planet_combo.setObjectName("trade_tab-planet_combo")  # Set objectName
        self.planet_combo.currentIndexChanged.connect(lambda: self.update_terminals(self.planet_combo, self.terminal_combo))
        main_layout.addWidget(planet_label)
        main_layout.addWidget(self.planet_combo)

        terminal_label = QLabel("Select Terminal:")
        self.terminal_search_input = QLineEdit()
        self.terminal_search_input.setPlaceholderText("Type to search terminals...")
        self.terminal_search_input.textChanged.connect(lambda: self.filter_terminals(self.planet_combo, self.terminal_combo, self.terminal_search_input))
        self.terminal_combo = QComboBox()
        self.terminal_combo.setObjectName("trade_tab-terminal_combo")  # Set objectName
        self.terminal_combo.setEditable(False)
        self.terminal_combo.currentIndexChanged.connect(lambda: self.update_commodities(self.terminal_combo))
        main_layout.addWidget(terminal_label)
        main_layout.addWidget(self.terminal_search_input)
        main_layout.addWidget(self.terminal_combo)

        # Create a horizontal layout for the commodity lists
        commodity_layout = QHBoxLayout()

        # Buy list
        buy_layout = QVBoxLayout()
        commodity_buy_label = QLabel("Commodities to Buy:")
        self.commodity_buy_list = QListWidget()
        self.commodity_buy_list.currentItemChanged.connect(
            lambda: asyncio.ensure_future(self.update_price(self.commodity_buy_list, self.terminal_combo, is_buy=True))
        )
        buy_layout.addWidget(commodity_buy_label)
        buy_layout.addWidget(self.commodity_buy_list)
        commodity_layout.addLayout(buy_layout)

        # Sell list
        sell_layout = QVBoxLayout()
        commodity_sell_label = QLabel("Commodities to Sell:")
        self.commodity_sell_list = QListWidget()
        self.commodity_sell_list.currentItemChanged.connect(
            lambda: asyncio.ensure_future(self.update_price(self.commodity_sell_list, self.terminal_combo, is_buy=False))
        )
        sell_layout.addWidget(commodity_sell_label)
        sell_layout.addWidget(self.commodity_sell_list)
        commodity_layout.addLayout(sell_layout)

        main_layout.addLayout(commodity_layout)

        amount_label = QLabel("Amount (SCU):")
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QIntValidator(0, 1000000))
        main_layout.addWidget(amount_label)
        main_layout.addWidget(self.amount_input)

        # Buy Price
        self.buy_price_label = QLabel("Buy Price (UEC/SCU):")
        self.buy_price_input = QLineEdit()
        self.buy_price_input.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.buy_price_input.setReadOnly(True)  # Initially read-only
        main_layout.addWidget(self.buy_price_label)
        main_layout.addWidget(self.buy_price_input)

        # Sell Price
        self.sell_price_label = QLabel("Sell Price (UEC/SCU):")
        self.sell_price_input = QLineEdit()
        self.sell_price_input.setValidator(QDoubleValidator(0.0, 1000000.0, 2))
        self.sell_price_input.setReadOnly(True)  # Initially read-only
        main_layout.addWidget(self.sell_price_label)
        main_layout.addWidget(self.sell_price_input)

        # Buy Button
        self.buy_button = QPushButton("Buy Commodity")
        self.buy_button.clicked.connect(lambda: asyncio.ensure_future(self.buy_commodity()))
        self.buy_button.setEnabled(False)  # Initially disabled
        main_layout.addWidget(self.buy_button)

        # Sell Button
        self.sell_button = QPushButton("Sell Commodity")
        self.sell_button.clicked.connect(lambda: asyncio.ensure_future(self.sell_commodity()))
        self.sell_button.setEnabled(False)  # Initially disabled
        main_layout.addWidget(self.sell_button)

        trade_tab.setLayout(main_layout)
        return trade_tab

    def create_trade_route_tab(self):
        trade_route_tab = QWidget()
        layout = QVBoxLayout()

        # Input parameters
        self.max_scu_input = QLineEdit()
        self.max_scu_input.setPlaceholderText("Enter Max SCU")
        self.max_scu_input.setValidator(QIntValidator())

        self.restrict_system_checkbox = QCheckBox("Restrict to Current System")
        self.restrict_system_checkbox.setChecked(True)
        self.restrict_planet_checkbox = QCheckBox("Restrict to Current Planet")

        self.max_investment_input = QLineEdit()
        self.max_investment_input.setPlaceholderText("Enter Max Investment (UEC)")
        self.max_investment_input.setValidator(QDoubleValidator())

        self.departure_system_combo = QComboBox()
        self.departure_system_combo.setObjectName("trade_route_tab-departure_system_combo")  # Set objectName
        self.departure_system_combo.currentIndexChanged.connect(
            lambda: self.update_planets(self.departure_system_combo, self.departure_planet_combo)
        )
        self.departure_planet_combo = QComboBox()
        self.departure_planet_combo.setObjectName("trade_route_tab-departure_planet_combo")  # Set objectName
        self.departure_planet_combo.currentIndexChanged.connect(
            lambda: self.update_terminals(self.departure_planet_combo, self.departure_terminal_combo)
        )
        self.departure_terminal_search_input = QLineEdit()
        self.departure_terminal_search_input.setPlaceholderText("Type to search terminals...")
        self.departure_terminal_search_input.textChanged.connect(lambda: self.filter_terminals(self.departure_planet_combo, self.departure_terminal_combo, self.departure_terminal_search_input))
        self.departure_terminal_combo = QComboBox()
        self.departure_terminal_combo.setObjectName("trade_route_tab-departure_terminal_combo")  # Set objectName

        self.departure_min_scu_input = QLineEdit("0")
        self.departure_min_scu_input.setValidator(QIntValidator())

        find_route_button = QPushButton("Find Trade Route")
        find_route_button.clicked.connect(lambda: asyncio.ensure_future(self.find_trade_routes()))

        # Table to display results
        self.trade_route_table = QTableWidget()
        self.trade_route_table.setColumnCount(12)  # Adjusted column count
        self.trade_route_table.setHorizontalHeaderLabels(
            [
                "Destination",
                "Commodity",
                "Quantity",
                "Buy Price",
                "Sell Price",
                "Investment",
                "Unit Margin",
                "Total Margin",
                "Stocks",
                "Demand",
                "Profit Margin",
                "Max Crate Size"
            ]
        )
        self.trade_route_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Add input widgets to layout
        layout.addWidget(QLabel("Max SCU:"))
        layout.addWidget(self.max_scu_input)
        layout.addWidget(self.restrict_system_checkbox)
        layout.addWidget(self.restrict_planet_checkbox)
        layout.addWidget(QLabel("Max Investment (UEC):"))
        layout.addWidget(self.max_investment_input)
        layout.addWidget(QLabel("Departure System:"))
        layout.addWidget(self.departure_system_combo)
        layout.addWidget(QLabel("Departure Planet:"))
        layout.addWidget(self.departure_planet_combo)
        layout.addWidget(QLabel("Departure Terminal:"))
        layout.addWidget(self.departure_terminal_search_input)
        layout.addWidget(self.departure_terminal_combo)
        layout.addWidget(QLabel("Departure Min SCU Available:"))
        layout.addWidget(self.departure_min_scu_input)
        layout.addWidget(find_route_button)
        layout.addWidget(self.trade_route_table)

        trade_route_tab.setLayout(layout)
        return trade_route_tab

    async def find_trade_routes(self):
        self.logger.log(logging.INFO, "Searching for a new Trade Route")
        self.trade_route_table.setRowCount(0)  # Clear previous results

        try:
            max_scu = int(self.max_scu_input.text()) if self.max_scu_input.text() else sys.maxsize
            restrict_planet = self.restrict_planet_checkbox.isChecked()
            restrict_system = self.restrict_system_checkbox.isChecked()
            max_investment = float(self.max_investment_input.text()) if self.max_investment_input.text() else sys.maxsize
            departure_system_id = self.departure_system_combo.currentData()
            departure_planet_id = self.departure_planet_combo.currentData()
            departure_terminal_id = self.departure_terminal_combo.currentData()
            departure_min_scu = int(self.departure_min_scu_input.text()) if self.departure_min_scu_input.text() else 0

            # Basic input validation
            if not all([departure_system_id, departure_planet_id, departure_terminal_id]):
                QMessageBox.warning(self, "Input Error",
                                    "Please Select Departure System, Planet, and Terminal.")
                return

            trade_routes = []
            departure_commodities = await self.api.fetch_data("/commodities_prices",
                                                              params={'id_terminal': departure_terminal_id})
            self.logger.log(logging.INFO,
                             f"Iterating through {len(departure_commodities.get('data', []))} commodities at departure terminal")
            for departure_commodity in departure_commodities.get("data", []):
                # Only get arrival terminals for commodities that can be bought in departure
                if departure_commodity.get("price_buy") == 0:
                    continue

                arrival_commodities = await self.api.fetch_data("/commodities_prices",
                                                               params={'id_commodity': departure_commodity.get(
                                                                   "id_commodity")})
                self.logger.log(logging.INFO,
                                 f"Found {len(arrival_commodities.get('data', []))} terminals that might sell {departure_commodity.get('commodity_name')}")

                for arrival_commodity in arrival_commodities.get("data", []):
                    # Check if terminal is available
                    if arrival_commodity.get("is_available") == 0:
                        continue

                    # Check if terminal is the same as departure
                    if arrival_commodity.get("id_terminal") == departure_terminal_id:
                        continue

                    # Filter arrival terminals based on restrictions
                    if restrict_system and arrival_commodity.get("id_star_system") != departure_system_id:
                        continue

                    if restrict_planet and arrival_commodity.get("id_planet") != departure_planet_id:
                        continue

                    buy_price = departure_commodity.get("price_buy", 0)
                    available_scu = departure_commodity.get("scu_buy", 0)

                    # Calculate trade route details
                    sell_price = arrival_commodity.get("price_sell", 0)
                    demand_scu = arrival_commodity.get("scu_sell_stock", 0) - arrival_commodity.get(
                        "scu_sell_users", 0)

                    # Skip if buy or sell price is 0 or if SCU requirements aren't met
                    if not buy_price or not sell_price or available_scu < departure_min_scu or not demand_scu:
                        continue

                    max_buyable_scu = min(max_scu, available_scu, int(max_investment // buy_price),
                                          demand_scu)
                    if max_buyable_scu <= 0:
                        continue

                    investment = buy_price * max_buyable_scu
                    unit_margin = (sell_price - buy_price)
                    total_margin = unit_margin * max_buyable_scu
                    profit_margin = unit_margin / buy_price

                    # Fetch arrival terminal data
                    arrival_terminal = await self.api.fetch_data("/terminals",
                                                                params={'id': arrival_commodity.get("id_terminal")})
                    arrival_terminal_mcs = arrival_terminal.get("data")[0].get("mcs")

                    trade_routes.append({
                        "destination": next(
                            (system["name"] for system in self.star_systems.get("data", [])
                             if system["id"] == arrival_commodity.get("id_star_system")),
                            "Unknown System"
                        ) + " - " + next(
                            (planet["name"] for planet in self.planets.get("data", [])
                             if planet["id"] == arrival_commodity.get("id_planet")),
                            "Unknown Planet"
                        ) + " / " + arrival_commodity.get("terminal_name"),
                        "commodity": departure_commodity.get("commodity_name"),
                        "buy_scu": str(max_buyable_scu) + " SCU",
                        "buy_price": str(buy_price) + " UEC",
                        "sell_price": str(sell_price) + " UEC",
                        "investment": str(investment) + " UEC",
                        "unit_margin": str(unit_margin) + " UEC",
                        "total_margin": str(total_margin) + " UEC",
                        "departure_scu_available": str(available_scu) + " SCU",
                        "arrival_demand_scu": str(demand_scu) + " SCU",
                        "profit_margin": str(round(profit_margin * 100)) + "%",
                        "arrival_terminal_mcs": arrival_terminal_mcs
                    })
                    self.trade_route_table.insertRow(len(trade_routes) - 1)
                    for j, value in enumerate(trade_routes[len(trade_routes) - 1].values()):
                        i = len(trade_routes) - 1
                        item = QTableWidgetItem(str(value))
                        self.trade_route_table.setItem(i, j, item)

            # Sort trade routes by profit margin (descending)
            trade_routes.sort(key=lambda x: float(x["total_margin"].split()[0]), reverse=True)

            # Display up to the top 10 results
            self.trade_route_table.setRowCount(0)  # Clear the table before adding sorted results
            for i, route in enumerate(trade_routes[:10]):
                self.trade_route_table.insertRow(i)
                for j, value in enumerate(route.values()):
                    item = QTableWidgetItem(str(value))
                    self.trade_route_table.setItem(i, j, item)

            if len(trade_routes) == 0:
                self.trade_route_table.insertRow(0)
                item = QTableWidgetItem("No results found")
                self.trade_route_table.setItem(0, 0, item)

            self.logger.log(logging.INFO, "Finished calculating Trade routes")
        except Exception as e:
            self.logger.log(logging.ERROR, f"An error occured while finding trade routes: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    async def load_data(self):
        try:
            self.star_systems = await self.api.fetch_data("/star_systems")
            self.logger.log(logging.INFO, f"Star Systems Loaded: {len(self.star_systems)}")
            self.update_system_combos()
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error loading initial data: {e}")

    def update_system_combos(self):
        self.logger.log(logging.INFO, "Updating ALL system combos...")
        self.system_combo.clear()
        self.departure_system_combo.clear()  # Update the new system combo
        for star_system in self.star_systems.get("data", []):
            if star_system.get("is_available") == 1:
                self.system_combo.addItem(star_system["name"], star_system["id"])
                self.departure_system_combo.addItem(star_system["name"], star_system["id"])
        self.logger.log(logging.INFO, "System combos updated.")

    def update_planets(self, system_combo, planet_combo):
        system_id = system_combo.currentData()
        self.logger.debug(f"update_planets function - Selected system: {system_combo.currentText()}")
        if system_id:
            self.logger.debug(f"update_planets function - System ID is valid, calling update_planets_async")
            asyncio.ensure_future(self.update_planets_async(system_id, system_combo, planet_combo))
        else:
            self.logger.debug(f"update_planets function - System ID is invalid")

    async def update_planets_async(self, system_id, system_combo, planet_combo):
        self.logger.debug(f"update_planets_async function - Fetching planets for system ID: {system_id}")
        try:
            self.planets = await self.api.fetch_data("/planets", params={'id_star_system': system_id})
            self.logger.debug(f"update_planets_async function - Planets fetched: {len(self.planets)}")
            self.update_planet_combo(planet_combo)
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error loading planets: {e}")

    def update_planet_combo(self, planet_combo):
        combo_box_name = planet_combo.objectName()
        self.logger.debug(f"update_planet_combo function - Updating planet combo box: {combo_box_name}")
        planet_combo.clear()
        for planet in self.planets.get("data", []):
            planet_combo.addItem(planet["name"], planet["id"])
        self.logger.debug(f"update_planet_combo function - Planets updated: {len(self.planets)}")

    def update_terminals(self, planet_combo, terminal_combo):
        planet_id = planet_combo.currentData()
        self.logger.debug(f"Selected planet: {planet_combo.currentText()}")
        if planet_id:
            asyncio.ensure_future(self.update_terminals_async(planet_id, planet_combo, terminal_combo))

    async def update_terminals_async(self, planet_id, planet_combo, terminal_combo):
        try:
            self.terminals[str(planet_id)] = await self.api.fetch_data("/terminals", params={'id_planet': planet_id})
            self.update_terminal_combo(planet_id, terminal_combo)
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error loading terminals: {e}")

    def update_terminal_combo(self, planet_id, terminal_combo):
        terminal_combo.clear()
        for terminal in self.terminals[str(planet_id)].get("data", []):
            if terminal.get("is_available") == 1 and terminal.get("type") == "commodity":
                terminal_combo.addItem(terminal["name"], terminal["id"])
        self.logger.debug(f"Terminals updated: {len(self.terminals[str(planet_id)])}")

    def filter_terminals(self, planet_combo, terminal_combo, terminal_search_input):
        planet_id = planet_combo.currentData()
        text = terminal_search_input.text()
        terminal_combo.clear()
        for terminal in self.terminals[str(planet_id)].get("data", []):
            if terminal.get("is_available") == 1 and terminal.get("type") == "commodity" and text.lower() in terminal[
                "name"
            ].lower():
                terminal_combo.addItem(terminal["name"], terminal["id"])
        # Ensure the first item is selected if available
        if terminal_combo.count() > 0:
            terminal_combo.setCurrentIndex(0)
            self.update_commodities(terminal_combo)

    def update_commodities(self, terminal_combo):
        terminal_id = terminal_combo.currentData()
        self.logger.debug(f"Selected terminal ID: {terminal_id}")
        if terminal_id:
            # Reset buy and sell prices
            self.buy_price_input.setText("")
            self.sell_price_input.setText("")
            self.buy_price_input.setReadOnly(True)
            self.sell_price_input.setReadOnly(True)
            self.buy_button.setEnabled(False)
            self.sell_button.setEnabled(False)
            
            asyncio.ensure_future(self.update_commodities_async(terminal_id, terminal_combo))

    async def update_commodities_async(self, terminal_id, terminal_combo):
        try:
            self.commodities = await self.api.fetch_data(
                "/commodities_prices", params={'id_terminal': terminal_id}
            )
            self.update_commodity_list()
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error loading commodities: {e}")

    def update_commodity_list(self):
        self.commodity_buy_list.clear()
        self.commodity_sell_list.clear()
        for commodity in self.commodities.get("data", []):
            item = QListWidgetItem(commodity["commodity_name"])
            item.setData(Qt.UserRole, QVariant(commodity["id_commodity"]))
            
            if commodity["price_buy"] > 0:
                self.commodity_buy_list.addItem(item.clone())
            
            if commodity["price_sell"] > 0:
                self.commodity_sell_list.addItem(item.clone())
        
        self.logger.debug(f"Commodities updated: {len(self.commodities)}")
        
        # Update prices for the first item in each list if available
        if self.commodity_buy_list.count() > 0:
            asyncio.ensure_future(self.update_price(self.commodity_buy_list, self.terminal_combo, is_buy=True))
        if self.commodity_sell_list.count() > 0:
            asyncio.ensure_future(self.update_price(self.commodity_sell_list, self.terminal_combo, is_buy=False))

    async def update_price(self, commodity_list, terminal_combo, is_buy):
        id_commodity = commodity_list.currentItem().data(Qt.UserRole) if commodity_list.currentItem() else None
        terminal_id = terminal_combo.currentData()
        self.logger.debug(f"Selected commodity ID: {id_commodity}, terminal ID: {terminal_id}")
        if id_commodity and terminal_id:
            try:
                prices = await self.api.fetch_data(
                    "/commodities_prices",
                    params={'id_commodity': id_commodity, 'id_terminal': terminal_id},
                )
                if prices and prices.get("data"):
                    price = prices["data"][0]["price_buy"] if is_buy else prices["data"][0]["price_sell"]
                    
                    if is_buy:
                        self.buy_price_input.setText(str(price) if price else "0")
                        self.buy_price_input.setReadOnly(price == 0)
                        self.buy_button.setEnabled(price != 0)
                    else:
                        self.sell_price_input.setText(str(price) if price else "0")
                        self.sell_price_input.setReadOnly(price == 0)
                        self.sell_button.setEnabled(price != 0)

            except Exception as e:
                self.logger.log(logging.ERROR, f"Error loading prices: {e}")

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
        await self.perform_trade(self.commodity_buy_list, is_buy=True)

    async def sell_commodity(self):
        await self.perform_trade(self.commodity_sell_list, is_buy=False)

    async def perform_trade(self, commodity_list, is_buy):
        selected_item = commodity_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Error", "Please select a commodity.")
            return
        
        operation = "sell"
        if is_buy:
            operation = "buy"

        logger = logging.getLogger(__name__)
        try:
            terminal_id = self.terminal_combo.currentData()
            id_commodity = commodity_list.currentItem().data(Qt.UserRole) if commodity_list.currentItem() else None
            amount = self.amount_input.text()

            logger.debug(f"Attempting trade - Operation: {operation}, Terminal ID: {terminal_id}, Commodity ID: {id_commodity}, Amount: {amount}")

            if not all([terminal_id, id_commodity, amount]):
                raise ValueError("Please fill all fields.")

            if not re.match(r'^\d+$', amount):
                raise ValueError("Amount must be a valid integer.")

            # Validate terminal and commodity
            if not any(terminal["id"] == terminal_id for terminal in self.terminals):
                raise ValueError("Selected terminal does not exist.")
            if not any(
                commodity["id_commodity"] == id_commodity for commodity in self.commodities.get("data", [])
            ):
                raise ValueError("Selected commodity does not exist on this terminal.")

            # Get the price from the input field, depending on buy/sell operation
            price = float(self.buy_price_input.text()) if operation == "buy" else float(self.sell_price_input.text())

            current_item = commodity_list.currentItem()
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
