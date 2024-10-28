import logging
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget, QMessageBox, QTableWidgetItem, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt
import asyncio
from api import API
from config_manager import ConfigManager
from functools import partial
from trade_tab import TradeTab

class TradeRouteTab(QWidget):
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
        self.logger = logging.getLogger(__name__)
        self.terminals = []
        self.initUI()
        asyncio.ensure_future(self.load_systems())

    def initUI(self):
        layout = QVBoxLayout()

        self.max_scu_input = QLineEdit()
        self.max_scu_input.setPlaceholderText("Enter Max SCU")
        layout.addWidget(QLabel("Max SCU:"))
        layout.addWidget(self.max_scu_input)

        self.max_investment_input = QLineEdit()
        self.max_investment_input.setPlaceholderText("Enter Max Investment (UEC)")
        layout.addWidget(QLabel("Max Investment (UEC):"))
        layout.addWidget(self.max_investment_input)

        self.departure_system_combo = QComboBox()
        self.departure_system_combo.currentIndexChanged.connect(lambda: asyncio.ensure_future(self.update_planets()))
        layout.addWidget(QLabel("Departure System:"))
        layout.addWidget(self.departure_system_combo)

        self.departure_planet_combo = QComboBox()
        self.departure_planet_combo.currentIndexChanged.connect(lambda: asyncio.ensure_future(self.update_terminals()))
        layout.addWidget(QLabel("Departure Planet:"))
        layout.addWidget(self.departure_planet_combo)

        terminal_label = QLabel("Select Terminal:")
        self.terminal_filter_input = QLineEdit()
        self.terminal_filter_input.setPlaceholderText("Filter Terminals")
        self.terminal_filter_input.textChanged.connect(self.filter_terminals)
        self.departure_terminal_combo = QComboBox()
        layout.addWidget(terminal_label)
        layout.addWidget(self.terminal_filter_input)
        layout.addWidget(self.departure_terminal_combo)

        # Add checkboxes for filtering
        self.filter_system_checkbox = QCheckBox("Filter for Current System")
        self.filter_system_checkbox.setChecked(True)  # Ensure this checkbox is checked by default
        self.filter_planet_checkbox = QCheckBox("Filter for Current Planet")
        layout.addWidget(self.filter_system_checkbox)
        layout.addWidget(self.filter_planet_checkbox)

        # Add checkboxes for ignoring stocks and demand
        self.ignore_stocks_checkbox = QCheckBox("Ignore Stocks")
        self.ignore_demand_checkbox = QCheckBox("Ignore Demand")
        layout.addWidget(self.ignore_stocks_checkbox)
        layout.addWidget(self.ignore_demand_checkbox)

        find_route_button = QPushButton("Find Trade Route")
        find_route_button.clicked.connect(lambda: asyncio.ensure_future(self.find_trade_routes()))
        layout.addWidget(find_route_button)

        self.trade_route_table = QTableWidget()
        layout.addWidget(self.trade_route_table)

        self.setLayout(layout)

    async def load_systems(self):
        try:
            systems = await self.api.fetch_data("/star_systems")
            for system in systems.get("data", []):
                if system.get("is_available") == 1:
                    self.departure_system_combo.addItem(system["name"], system["id"])
            logging.info("Systems loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load systems: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load systems: {e}")

    async def update_planets(self):
        self.departure_planet_combo.clear()
        self.departure_terminal_combo.clear()
        self.terminal_filter_input.clear()  # Clear the filter input here
        self.terminals = []
        system_id = self.departure_system_combo.currentData()
        if not system_id:
            return
        try:
            planets = await self.api.fetch_data("/planets", params={'id_star_system': system_id})
            for planet in planets.get("data", []):
                self.departure_planet_combo.addItem(planet["name"], planet["id"])
            logging.info("Planets loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load planets: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load planets: {e}")

    async def update_terminals(self):
        self.departure_terminal_combo.clear()
        self.terminal_filter_input.clear()  # Ensure the filter input is cleared when updating terminals
        self.terminals = []
        planet_id = self.departure_planet_combo.currentData()
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
        self.departure_terminal_combo.clear()
        for terminal in self.terminals:
            if filter_text in terminal["name"].lower():
                self.departure_terminal_combo.addItem(terminal["name"], terminal["id"])

    async def find_trade_routes(self):
        self.logger.log(logging.INFO, "Searching for a new Trade Route")
        self.trade_route_table.setRowCount(0)  # Clear previous results

        # Define the columns
        columns = [
            "Destination", "Commodity", "Buy SCU", "Buy Price", "Sell Price",
            "Investment", "Unit Margin", "Total Margin", "Departure SCU Available",
            "Arrival Demand SCU", "Profit Margin", "Arrival Terminal MCS", "Actions"
        ]
        self.trade_route_table.setColumnCount(len(columns))
        self.trade_route_table.setHorizontalHeaderLabels(columns)

        try:
            max_scu = int(self.max_scu_input.text()) if self.max_scu_input.text() else sys.maxsize
            max_investment = float(self.max_investment_input.text()) if self.max_investment_input.text() else sys.maxsize
            departure_system_id = self.departure_system_combo.currentData()
            departure_planet_id = self.departure_planet_combo.currentData()
            departure_terminal_id = self.departure_terminal_combo.currentData()

            # Basic input validation
            if not all([departure_system_id, departure_planet_id, departure_terminal_id]):
                QMessageBox.warning(self, "Input Error", "Please Select Departure System, Planet, and Terminal.")
                return

            trade_routes = []
            departure_commodities = await self.api.fetch_data("/commodities_prices", params={'id_terminal': departure_terminal_id})
            self.logger.log(logging.INFO, f"Iterating through {len(departure_commodities.get('data', []))} commodities at departure terminal")
            for departure_commodity in departure_commodities.get("data", []):
                # Only get arrival terminals for commodities that can be bought in departure
                if departure_commodity.get("price_buy") == 0:
                    continue

                arrival_commodities = await self.api.fetch_data("/commodities_prices", params={'id_commodity': departure_commodity.get("id_commodity")})
                self.logger.log(logging.INFO, f"Found {len(arrival_commodities.get('data', []))} terminals that might sell {departure_commodity.get('commodity_name')}")

                for arrival_commodity in arrival_commodities.get("data", []):
                    # Check if terminal is available
                    if arrival_commodity.get("is_available") == 0:
                        continue

                    # Check if terminal is the same as departure
                    if arrival_commodity.get("id_terminal") == departure_terminal_id:
                        continue

                    # Apply filters if checkboxes are checked
                    if self.filter_system_checkbox.isChecked() and arrival_commodity.get("id_star_system") != departure_system_id:
                        continue
                    if self.filter_planet_checkbox.isChecked() and arrival_commodity.get("id_planet") != departure_planet_id:
                        continue

                    buy_price = departure_commodity.get("price_buy", 0)
                    available_scu = departure_commodity.get("scu_buy", 0)
                    original_available_scu = available_scu  # Store original available SCU

                    # Calculate trade route details
                    sell_price = arrival_commodity.get("price_sell", 0)
                    demand_scu = arrival_commodity.get("scu_sell_stock", 0) - arrival_commodity.get("scu_sell_users", 0)
                    original_demand_scu = demand_scu  # Store original demand SCU

                    # Adjust calculations based on checkboxes
                    if self.ignore_stocks_checkbox.isChecked():
                        available_scu = max_scu
                    if self.ignore_demand_checkbox.isChecked():
                        demand_scu = max_scu

                    # Skip if buy or sell price is 0 or if SCU requirements aren't met
                    if not buy_price or not sell_price or available_scu <= 0 or not demand_scu:
                        continue

                    max_buyable_scu = min(max_scu, available_scu, int(max_investment // buy_price), demand_scu)
                    if max_buyable_scu <= 0:
                        continue

                    investment = buy_price * max_buyable_scu
                    unit_margin = (sell_price - buy_price)
                    total_margin = unit_margin * max_buyable_scu
                    profit_margin = unit_margin / buy_price

                    # Fetch arrival terminal data
                    arrival_terminal = await self.api.fetch_data("/terminals", params={'id': arrival_commodity.get("id_terminal")})
                    arrival_terminal_mcs = arrival_terminal.get("data")[0].get("mcs")

                    trade_routes.append({
                        "destination": next(
                            (system["name"] for system in (await self.api.fetch_data("/star_systems")).get("data", [])
                             if system["id"] == arrival_commodity.get("id_star_system")),
                            "Unknown System"
                        ) + " - " + next(
                            (planet["name"] for planet in (await self.api.fetch_data("/planets", params={'id_star_system': arrival_commodity.get("id_star_system")})).get("data", [])
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
                        "departure_scu_available": str(original_available_scu) + " SCU",  # Show original available SCU
                        "arrival_demand_scu": str(original_demand_scu) + " SCU",  # Show original demand SCU
                        "profit_margin": str(round(profit_margin * 100)) + "%",
                        "arrival_terminal_mcs": arrival_terminal_mcs,
                        "departure_system_id": departure_system_id,
                        "departure_planet_id": departure_planet_id,
                        "departure_terminal_id": departure_terminal_id,
                        "arrival_system_id": arrival_commodity.get("id_star_system"),
                        "arrival_planet_id": arrival_commodity.get("id_planet"),
                        "arrival_terminal_id": arrival_commodity.get("id_terminal"),
                        "commodity_id": departure_commodity.get("id_commodity"),
                        "max_buyable_scu": max_buyable_scu
                    })
                    self.trade_route_table.insertRow(len(trade_routes) - 1)
                    for j, value in enumerate(trade_routes[len(trade_routes) - 1].values()):
                        i = len(trade_routes) - 1
                        if j < len(columns) - 1:
                            item = QTableWidgetItem(str(value))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the item non-editable
                            self.trade_route_table.setItem(i, j, item)
                        else:
                            # Add action buttons
                            action_layout = QHBoxLayout()
                            buy_button = QPushButton("Select to Buy")
                            buy_button.clicked.connect(partial(self.select_to_buy, trade_routes[i]))
                            sell_button = QPushButton("Select to Sell")
                            sell_button.clicked.connect(partial(self.select_to_sell, trade_routes[i]))
                            action_layout.addWidget(buy_button)
                            action_layout.addWidget(sell_button)
                            action_widget = QWidget()
                            action_widget.setLayout(action_layout)
                            self.trade_route_table.setCellWidget(i, j, action_widget)

            # Sort trade routes by profit margin (descending)
            trade_routes.sort(key=lambda x: float(x["total_margin"].split()[0]), reverse=True)

            # Display up to the top 10 results
            self.trade_route_table.setRowCount(0)  # Clear the table before adding sorted results
            for i, route in enumerate(trade_routes[:10]):
                self.trade_route_table.insertRow(i)
                for j, value in enumerate(route.values()):
                    if j < len(columns) - 1:
                        item = QTableWidgetItem(str(value))
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the item non-editable
                        self.trade_route_table.setItem(i, j, item)
                    else:
                        # Add action buttons
                        action_layout = QHBoxLayout()
                        buy_button = QPushButton("Select to Buy")
                        buy_button.clicked.connect(partial(self.select_to_buy, trade_routes[i]))
                        sell_button = QPushButton("Select to Sell")
                        sell_button.clicked.connect(partial(self.select_to_sell, trade_routes[i]))
                        action_layout.addWidget(buy_button)
                        action_layout.addWidget(sell_button)
                        action_widget = QWidget()
                        action_widget.setLayout(action_layout)
                        self.trade_route_table.setCellWidget(i, j, action_widget)

            if len(trade_routes) == 0:
                self.trade_route_table.insertRow(0)
                item = QTableWidgetItem("No results found")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the item non-editable
                self.trade_route_table.setItem(0, 0, item)

            # Resize columns to fit contents
            self.trade_route_table.resizeColumnsToContents()

            self.logger.log(logging.INFO, "Finished calculating Trade routes")
        except Exception as e:
            self.logger.log(logging.ERROR, f"An error occurred while finding trade routes: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def select_to_buy(self, trade_route):
        self.logger.log(logging.INFO, "Selected route to buy")
        trade_tab = self.main_widget.findChild(TradeTab)
        if trade_tab:
            self.main_widget.loop.create_task(trade_tab.select_trade_route(trade_route, is_buy=True))
        else:
            self.logger.log(logging.ERROR, f"An error occurred while selecting trade route")
            QMessageBox.critical(self, "Error", f"An error occurred")

    def select_to_sell(self, trade_route):
        self.logger.log(logging.INFO, "Selected route to sell")
        trade_tab = self.main_widget.findChild(TradeTab)
        if trade_tab:
            self.main_widget.loop.create_task(trade_tab.select_trade_route(trade_route, is_buy=False))
        else:
            self.logger.log(logging.ERROR, f"An error occurred while selecting trade route")
            QMessageBox.critical(self, "Error", f"An error occurred")
