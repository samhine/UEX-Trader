import logging
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QMessageBox, QTableWidgetItem,
    QHBoxLayout, QCheckBox, QApplication, QProgressBar
)
from PyQt5.QtCore import Qt
import asyncio
from api import API
from config_manager import ConfigManager
from functools import partial
from trade_tab import TradeTab


class BestTradeRouteTab(QWidget):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        # Initial the ConfigManager instance only once
        if ConfigManager._instance is None:
            self.config_manager = ConfigManager()
        else:
            self.config_manager = ConfigManager._instance
        # Initialize the API instance only once
        if API._instance is None:
            self.api = API(self.config_manager)
        else:
            self.api = API._instance
        self.logger = logging.getLogger(__name__)
        self.terminals = []
        self.initUI()
        asyncio.ensure_future(self.load_systems())
        self.columns = [
            "Departure", "Destination", "Commodity", "Buy SCU", "Buy Price",
            "Sell Price", "Investment", "Unit Margin", "Total Margin",
            "Departure SCU Available", "Arrival Demand SCU", "Profit Margin", "Actions"
        ]

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
        self.departure_system_combo.currentIndexChanged.connect(
            lambda: asyncio.ensure_future(self.update_departure_planets())
        )
        layout.addWidget(QLabel("Departure System:"))
        layout.addWidget(self.departure_system_combo)
        self.departure_planet_combo = QComboBox()
        self.departure_planet_combo.addItem("All Planets")
        self.departure_planet_combo.currentIndexChanged.connect(
            lambda: asyncio.ensure_future(self.update_departure_terminals())
        )
        layout.addWidget(QLabel("Departure Planet:"))
        layout.addWidget(self.departure_planet_combo)
        self.destination_system_combo = QComboBox()
        self.destination_system_combo.addItem("All Systems")
        self.destination_system_combo.currentIndexChanged.connect(
            lambda: asyncio.ensure_future(self.update_destination_planets())
        )
        layout.addWidget(QLabel("Destination System:"))
        layout.addWidget(self.destination_system_combo)
        self.destination_planet_combo = QComboBox()
        self.destination_planet_combo.addItem("All Planets")
        self.destination_planet_combo.currentIndexChanged.connect(
            lambda: asyncio.ensure_future(self.update_destination_terminals())
        )
        layout.addWidget(QLabel("Destination Planet:"))
        layout.addWidget(self.destination_planet_combo)
        self.ignore_stocks_checkbox = QCheckBox("Ignore Stocks")
        self.ignore_demand_checkbox = QCheckBox("Ignore Demand")
        layout.addWidget(self.ignore_stocks_checkbox)
        layout.addWidget(self.ignore_demand_checkbox)
        self.filter_public_hangars_checkbox = QCheckBox("No Public Hangars")
        layout.addWidget(self.filter_public_hangars_checkbox)

        self.find_route_button_rework = QPushButton("Find Best Trade Routes")
        self.find_route_button_rework.clicked.connect(lambda: asyncio.ensure_future(self.find_best_trade_routes_rework()))
        layout.addWidget(self.find_route_button_rework)

        self.find_route_button_users = QPushButton("Find Best Trade Routes (from User Trades)")
        self.find_route_button_users.clicked.connect(lambda: asyncio.ensure_future(self.find_best_trade_routes_users()))
        layout.addWidget(self.find_route_button_users)

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setVisible(False)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.main_progress_bar)
        layout.addWidget(self.progress_bar)

        self.trade_route_table = QTableWidget()
        layout.addWidget(self.trade_route_table)
        self.setLayout(layout)

    async def load_systems(self):
        try:
            systems = await self.api.fetch_data("/star_systems")
            for system in systems.get("data", []):
                if system.get("is_available") == 1:
                    self.departure_system_combo.addItem(system["name"], system["id"])
                    self.destination_system_combo.addItem(system["name"], system["id"])
            logging.info("Systems loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load systems: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load systems: {e}")

    async def update_departure_planets(self):
        self.departure_planet_combo.clear()
        self.departure_planet_combo.addItem("All Planets")
        self.terminals = []
        system_id = self.departure_system_combo.currentData()
        if not system_id:
            return
        try:
            planets = await self.api.fetch_data("/planets", params={'id_star_system': system_id})
            for planet in planets.get("data", []):
                self.departure_planet_combo.addItem(planet["name"], planet["id"])
            logging.info("Departure planets loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load departure planets: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load departure planets: {e}")

    async def update_departure_terminals(self):
        self.terminals = []
        planet_id = self.departure_planet_combo.currentData()
        if not planet_id and self.departure_planet_combo.currentText() != "All Planets":
            return
        try:
            params = {'id_star_system': self.departure_system_combo.currentData()}
            if self.departure_planet_combo.currentText() != "All Planets":
                params['id_planet'] = planet_id
            terminals = await self.api.fetch_data("/terminals", params=params)
            self.terminals = [terminal for terminal in terminals.get("data", [])
                              if terminal.get("type") == "commodity" and terminal.get("is_available") == 1]
            logging.info("Departure terminals loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load departure terminals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load departure terminals: {e}")

    async def update_destination_planets(self):
        self.destination_planet_combo.clear()
        self.destination_planet_combo.addItem("All Planets")
        system_id = self.destination_system_combo.currentData()
        if not system_id and self.destination_system_combo.currentText() != "All Systems":
            return
        try:
            params = {}
            if self.destination_system_combo.currentText() != "All Systems":
                params['id_star_system'] = system_id
            planets = await self.api.fetch_data("/planets", params=params)
            for planet in planets.get("data", []):
                self.destination_planet_combo.addItem(planet["name"], planet["id"])
            logging.info("Destination planets loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load destination planets: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load destination planets: {e}")

    async def update_destination_terminals(self):
        self.destination_terminals = []
        planet_id = self.destination_planet_combo.currentData()
        if not planet_id and self.destination_planet_combo.currentText() != "All Planets":
            return
        try:
            params = {}
            if self.destination_system_combo.currentText() != "All Systems":
                params['id_star_system'] = self.destination_system_combo.currentData()
            if self.destination_planet_combo.currentText() != "All Planets":
                params['id_planet'] = planet_id
            terminals = await self.api.fetch_data("/terminals", params=params)
            self.destination_terminals = [terminal for terminal in terminals.get("data", [])
                                          if terminal.get("type") == "commodity" and terminal.get("is_available") == 1]
            logging.info("Destination terminals loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load destination terminals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load destination terminals: {e}")

    async def find_best_trade_routes_users(self):
        self.logger.log(logging.INFO, "Searching for Best Trade Routes")
        self.trade_route_table.setRowCount(0)  # Clear previous results
        self.trade_route_table.setColumnCount(len(self.columns))
        self.trade_route_table.setHorizontalHeaderLabels(self.columns)
        self.main_widget.set_gui_enabled(False)
        self.main_progress_bar.setVisible(True)
        self.progress_bar.setVisible(True)
        currentProgress = 0
        self.progress_bar.setValue(currentProgress)
        self.main_progress_bar.setValue(currentProgress)
        self.main_progress_bar.setMaximum(5)

        try:
            max_scu, max_investment = self.get_input_values()
            departure_system_id, departure_planet_id, destination_system_id, destination_planet_id = self.get_selected_ids()

            if not departure_system_id:
                QMessageBox.warning(self, "Input Error", "Please Select a Departure System.")
                return

            departure_planets = []
            if not departure_planet_id:
                departure_planets = await self.api.fetch_planets(departure_system_id)
            else:
                departure_planets = await self.api.fetch_planets(departure_system_id, departure_planet_id)
            self.logger.log(logging.INFO, f"{len(departure_planets)} departure planets found")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            destination_systems = []
            if not destination_system_id:
                destination_systems = await self.api.fetch_systems_from_origin_system(departure_system_id, 2)
            else:
                destination_systems = await self.api.fetch_system(destination_system_id)
            self.logger.log(logging.INFO, f"{len(destination_systems)} destination systems found")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            destination_planets = []
            universe = len(destination_systems)
            self.progress_bar.setMaximum(universe)
            actionProgress = 0
            for destination_system in destination_systems:
                if not destination_planet_id:
                    destination_planets.extend(await self.api.fetch_planets(destination_system["id"]))
                else:
                    destination_planets.extend(await self.api.fetch_planets(destination_system["id"], destination_planet_id))
                actionProgress += 1
                self.progress_bar.setValue(actionProgress)
            self.logger.log(logging.INFO, f"{len(destination_planets)} destination planets found")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            commodities_routes = []
            universe = len(departure_planets) * len(destination_planets)
            self.progress_bar.setMaximum(universe)
            actionProgress = 0
            for departure_planet in departure_planets:
                for destination_planet in destination_planets:
                    commodities_routes.extend(await self.api.fetch_routes(departure_planet["id"], destination_planet["id"]))
                    actionProgress += 1
                    self.progress_bar.setValue(actionProgress)
            self.logger.log(logging.INFO, f"{len(commodities_routes)} commodities routes to parse")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            trade_routes = await self.calculate_trade_routes_users(commodities_routes, max_scu, max_investment)
            self.logger.log(logging.INFO, f"{len(trade_routes)} routes found")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)
            self.logger.log(logging.INFO, "Finished calculating Best Trade Routes")

        except Exception as e:
            self.logger.log(logging.ERROR, f"An error occurred while finding best trade routes: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        finally:
            self.main_widget.set_gui_enabled(True)
            self.main_progress_bar.setVisible(False)
            self.progress_bar.setVisible(False)

    async def find_best_trade_routes_rework(self):
        self.logger.log(logging.INFO, "Searching for Best Trade Routes")
        self.trade_route_table.setRowCount(0)  # Clear previous results
        self.trade_route_table.setColumnCount(len(self.columns))
        self.trade_route_table.setHorizontalHeaderLabels(self.columns)
        self.main_widget.set_gui_enabled(False)
        self.main_progress_bar.setVisible(True)
        self.progress_bar.setVisible(True)
        currentProgress = 0
        self.progress_bar.setValue(currentProgress)
        self.main_progress_bar.setValue(currentProgress)
        self.main_progress_bar.setMaximum(7)

        try:
            # [Recover entry parameters]
            max_scu, max_investment = self.get_input_values()
            departure_system_id, departure_planet_id, destination_system_id, destination_planet_id = self.get_selected_ids()
            ignore_stocks = self.ignore_stocks_checkbox.isChecked()
            ignore_demand = self.ignore_demand_checkbox.isChecked()
            filter_public_hangars = self.filter_public_hangars_checkbox.isChecked()

            if not departure_system_id:
                QMessageBox.warning(self, "Input Error", "Please Select a Departure System.")
                return

            # [Recover departure/destination planets]
            departure_planets = []
            if not departure_planet_id:
                departure_planets = await self.api.fetch_planets(departure_system_id)
                self.logger.log(logging.INFO, f"{len(departure_planets)} Departure Planets found.")
            else:
                departure_planets = await self.api.fetch_planets(departure_system_id, departure_planet_id)
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            destination_systems = []
            if not destination_system_id:
                destination_systems = await self.api.fetch_systems_from_origin_system(departure_system_id, max_bounce=2)
                self.logger.log(logging.INFO, f"{len(destination_systems)} Destination Systems found.")
            else:
                destination_systems = await self.api.fetch_system(destination_system_id)
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            destination_planets = []
            universe = len(destination_systems)
            self.progress_bar.setMaximum(universe)
            actionProgress = 0
            if not destination_planet_id:
                for destination_system in destination_systems:
                    destination_planets.extend(await self.api.fetch_planets(destination_system["id"]))
                    actionProgress += 1
                    self.progress_bar.setValue(actionProgress)
                self.logger.log(logging.INFO, f"{len(destination_planets)} Destination Planets found.")
            else:
                destination_planets = await self.api.fetch_planets(destination_system_id, destination_planet_id)
                actionProgress += 1
                self.progress_bar.setValue(actionProgress)
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            # [Recover departure/destination terminals and commodities]
            departure_terminals = await self.get_terminals_from_planets(departure_planets, filter_public_hangars)
            self.logger.log(logging.INFO, f"{len(departure_terminals)} Departure Terminals found.")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            buy_commodities = await self.get_buy_commodities_from_terminals(departure_terminals)
            self.logger.log(logging.INFO, f"{len(buy_commodities)} Buy Commodities found.")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            sell_commodities = await self.get_sell_commodities_from_commodities_prices(buy_commodities, filter_public_hangars)
            self.logger.log(logging.INFO, f"{len(sell_commodities)} Sell Commodities found.")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)

            trade_routes = await self.calculate_trade_routes_rework(buy_commodities, sell_commodities,
                                                                    max_scu, max_investment,
                                                                    ignore_stocks, ignore_demand)
            self.logger.log(logging.INFO, f"{len(trade_routes)} Trade routes found.")
            currentProgress += 1
            self.main_progress_bar.setValue(currentProgress)
            self.logger.log(logging.INFO, f"Finished calculating Best Trade Routes : {len(trade_routes)} found")
        except Exception as e:
            self.logger.log(logging.ERROR, f"An error occurred while finding best trade routes: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
        finally:
            self.main_widget.set_gui_enabled(True)
            self.progress_bar.setVisible(False)
            self.main_progress_bar.setVisible(False)

    def get_input_values(self):
        max_scu = int(self.max_scu_input.text()) if self.max_scu_input.text() else sys.maxsize
        max_investment = float(self.max_investment_input.text()) if self.max_investment_input.text() else sys.maxsize
        return max_scu, max_investment

    def get_selected_ids(self):
        departure_system_id = self.departure_system_combo.currentData()
        departure_planet_id = self.departure_planet_combo.currentData()
        if self.departure_planet_combo.currentText() == "All Planets":
            departure_planet_id = None
        destination_system_id = self.destination_system_combo.currentData()
        destination_planet_id = self.destination_planet_combo.currentData()
        if self.destination_planet_combo.currentText() == "All Planets":
            destination_planet_id = None
        return departure_system_id, departure_planet_id, destination_system_id, destination_planet_id

    async def calculate_trade_routes_users(self, commodities_routes, max_scu, max_investment):
        trade_routes = await self.process_trade_route_users(commodities_routes, max_scu, max_investment)
        self.display_trade_routes(trade_routes, self.columns)
        # Allow UI to update during the search
        QApplication.processEvents()
        return trade_routes

    async def get_terminals_from_planets(self, filtering_planets, filter_public_hangars=False):
        terminals = []
        universe = len(filtering_planets)
        self.progress_bar.setMaximum(universe)
        actionProgress = 0
        # Get all terminals (filter by system/planet) from /terminals
        for planet in filtering_planets:
            returned_terminals = await self.api.fetch_terminals(planet["id_star_system"],
                                                                planet["id"])
            for terminal in returned_terminals:
                if not filter_public_hangars or (terminal["city_name"]
                                                 or terminal["space_station_name"]):
                    terminals.append(terminal)
            actionProgress += 1
            self.progress_bar.setValue(actionProgress)
        return terminals

    async def get_buy_commodities_from_terminals(self, departure_terminals):
        buy_commodities = []
        universe = len(departure_terminals)
        self.progress_bar.setMaximum(universe)
        actionProgress = 0
        # Get all BUY commodities (for each departure terminals) from /commodities_prices
        for departure_terminal in departure_terminals:
            buy_commodities.extend([commodity for commodity in
                                    await self.api.fetch_commodities_from_terminal(departure_terminal["id"])
                                    if commodity.get("price_buy") > 0])
            actionProgress += 1
            self.progress_bar.setValue(actionProgress)
        self.logger.log(logging.INFO, f"{len(buy_commodities)} Buy Commodities found.")
        return buy_commodities

    async def get_sell_commodities_from_commodities_prices(self, buy_commodities, filter_public_hangars=False):
        grouped_buy_commodities_ids = []
        # Establish a GROUPED list of BUY commodities (by commodity_id)
        grouped_buy_commodities_ids = set(map(lambda x: x["id_commodity"], buy_commodities))
        self.logger.log(logging.INFO, f"{len(grouped_buy_commodities_ids)} Unique Buy Commodities found.")

        sell_commodities = []
        universe = len(grouped_buy_commodities_ids)
        self.progress_bar.setMaximum(universe)
        actionProgress = 0
        # Get all SELL commodities (for each unique BUY commodity) from /commodities_prices
        for grouped_buy_id in grouped_buy_commodities_ids:
            sell_commodities.extend([commodity for commodity in await self.api.fetch_commodities_by_id(grouped_buy_id)
                                    if commodity["price_sell"] > 0 and (not filter_public_hangars or
                                                                        (commodity["city_name"] or
                                                                         commodity["space_station_name"]))])
            actionProgress += 1
            self.progress_bar.setValue(actionProgress)
        self.logger.log(logging.INFO, f"{len(sell_commodities)} Sell Commodities found.")
        return sell_commodities

    async def calculate_trade_routes_rework(self, buy_commodities, sell_commodities,
                                            max_scu, max_investment, ignore_stocks,
                                            ignore_demand):
        # [Calculate trade routes]
        trade_routes = []
        universe = len(buy_commodities) * len(sell_commodities)
        self.progress_bar.setMaximum(universe)
        actionProgress = 0

        # For each BUY commodity / For each SELL commodity > Populate Trade routes (Display as it is populated)
        for buy_commodity in buy_commodities:
            for sell_commodity in sell_commodities:
                self.progress_bar.setValue(actionProgress)
                actionProgress += 1
                if buy_commodity["id_commodity"] != sell_commodity["id_commodity"]:
                    continue
                if buy_commodity["id_terminal"] == sell_commodity["id_terminal"]:
                    continue
                route = await self.process_single_trade_route(buy_commodity, sell_commodity, max_scu,
                                                              max_investment, ignore_stocks, ignore_demand)
                if route:
                    trade_routes.append(route)
                    self.display_trade_routes(trade_routes, self.columns)
                    QApplication.processEvents()
        self.progress_bar.setValue(actionProgress)
        return trade_routes

    async def process_trade_route_users(self, commodities_routes, max_scu, max_investment):
        sorted_routes = []
        universe = len(commodities_routes)
        self.progress_bar.setMaximum(universe)
        actionProgress = 0
        for commodity_route in commodities_routes:
            actionProgress += 1
            self.progress_bar.setValue(actionProgress)
            if self.filter_public_hangars_checkbox.isChecked():
                if not commodity_route.get("is_space_station_origin", 0)\
                   and not commodity_route.get("is_space_station_destination", 0):
                    continue
                terminal_origin = await self.api.fetch_terminals(commodity_route.get("id_star_system_origin"),
                                                                 commodity_route.get("id_planet_origin"),
                                                                 commodity_route.get("id_terminal_origin"))
                if (not terminal_origin[0].get("city_name")):
                    continue
                terminal_destination = await self.api.fetch_terminals(commodity_route.get("id_star_system_destination"),
                                                                      commodity_route.get("id_planet_destination"),
                                                                      commodity_route.get("id_terminal_destination"))
                if not terminal_destination[0].get("city_name"):
                    continue

            available_scu = max_scu if self.ignore_stocks_checkbox.isChecked() else commodity_route.get("scu_origin", 0)
            demand_scu = max_scu if self.ignore_demand_checkbox.isChecked() else commodity_route.get("scu_destination", 0)

            price_buy = commodity_route.get("price_origin")
            price_sell = commodity_route.get("price_destination")

            if not price_buy or not price_sell or available_scu <= 0 or not demand_scu:
                continue

            max_buyable_scu = min(max_scu, available_scu, int(max_investment // price_buy), demand_scu)
            if max_buyable_scu <= 0:
                continue

            investment = price_buy * max_buyable_scu
            unit_margin = (price_sell - price_buy)
            total_margin = unit_margin * max_buyable_scu
            profit_margin = unit_margin / price_buy

            sorted_routes.append({
                "departure": commodity_route["origin_terminal_name"],
                "destination": commodity_route["destination_terminal_name"],
                "commodity": commodity_route["commodity_name"],
                "buy_scu": f"{max_buyable_scu} SCU",
                "buy_price": f"{price_buy} UEC",
                "sell_price": f"{price_sell} UEC",
                "investment": f"{investment} UEC",
                "unit_margin": f"{unit_margin} UEC",
                "total_margin": f"{total_margin} UEC",
                "departure_scu_available": f"{commodity_route.get('scu_origin', 0)} SCU",
                "arrival_demand_scu": f"{commodity_route.get('scu_destination', 0)} SCU",
                "profit_margin": f"{round(profit_margin * 100)}%",
                "departure_terminal_id": commodity_route["id_terminal_origin"],
                "arrival_terminal_id": commodity_route["id_terminal_destination"],
                "departure_system_id": commodity_route["id_star_system_origin"],
                "arrival_system_id": commodity_route["id_star_system_destination"],
                "departure_planet_id": commodity_route["id_planet_origin"],
                "arrival_planet_id": commodity_route["id_planet_destination"],
                "commodity_id": commodity_route["id_commodity"],
                "max_buyable_scu": max_buyable_scu
            })
        return sorted_routes

    async def process_single_trade_route(self, buy_commodity, sell_commodity, max_scu=sys.maxsize,
                                         max_investment=sys.maxsize, ignore_stocks=False, ignore_demand=False):
        route = None
        if buy_commodity["id_commodity"] != sell_commodity["id_commodity"]:
            return route
        if buy_commodity["id_terminal"] == sell_commodity["id_terminal"]:
            return route
        if buy_commodity["id"] == sell_commodity["id"]:
            return route
        if max_scu < 0:
            # TODO - Send Exception instead
            return route
        if max_investment < 0:
            # TODO - Send Exception instead
            return route

        available_scu = max_scu if ignore_stocks else buy_commodity.get("scu_buy", 0)
        scu_sell_stock = sell_commodity.get("scu_sell_stock", 0)
        scu_sell_users = sell_commodity.get("scu_sell_users", 0)
        demand_scu = max_scu if ignore_demand else scu_sell_stock - scu_sell_users

        price_buy = buy_commodity.get("price_buy")
        price_sell = sell_commodity.get("price_sell")

        if not price_buy or not price_sell or available_scu <= 0 or not demand_scu:
            return route

        max_buyable_scu = min(max_scu, available_scu, int(max_investment // price_buy), demand_scu)
        if max_buyable_scu <= 0:
            return route

        investment = price_buy * max_buyable_scu
        unit_margin = (price_sell - price_buy)
        total_margin = unit_margin * max_buyable_scu
        profit_margin = unit_margin / price_buy

        route = {
            "departure": buy_commodity["terminal_name"],
            "destination": sell_commodity["terminal_name"],
            "commodity": buy_commodity.get("commodity_name"),
            "buy_scu": f"{max_buyable_scu} SCU",
            "buy_price": f"{price_buy} UEC",
            "sell_price": f"{price_sell} UEC",
            "investment": f"{investment} UEC",
            "unit_margin": f"{unit_margin} UEC",
            "total_margin": f"{total_margin} UEC",
            "departure_scu_available": f"{buy_commodity.get('scu_buy', 0)} SCU",
            "arrival_demand_scu": f"{scu_sell_stock - scu_sell_users} SCU",
            "profit_margin": f"{round(profit_margin * 100)}%",
            "departure_terminal_id": buy_commodity["id_terminal"],
            "arrival_terminal_id": sell_commodity.get("id_terminal"),
            "departure_system_id": buy_commodity.get("id_star_system"),
            "arrival_system_id": sell_commodity.get("id_star_system"),
            "departure_planet_id": buy_commodity.get("id_planet"),
            "arrival_planet_id": sell_commodity.get("id_planet"),
            "commodity_id": buy_commodity.get("id_commodity"),
            "max_buyable_scu": max_buyable_scu
        }
        return route

    def display_trade_routes(self, trade_routes, columns):
        self.trade_route_table.setRowCount(0)  # Clear the table before adding sorted results
        trade_routes.sort(key=lambda x: float(x["total_margin"].split()[0]), reverse=True)
        for i, route in enumerate(trade_routes[:10]):
            self.trade_route_table.insertRow(i)
            for j, value in enumerate(route.values()):
                if j < len(columns) - 1:
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the item non-editable
                    self.trade_route_table.setItem(i, j, item)
                else:
                    self.add_action_buttons(i, j, trade_routes[i])

        # Resize columns to fit contents
        self.trade_route_table.resizeColumnsToContents()

    def add_action_buttons(self, i, j, trade_route):
        action_layout = QHBoxLayout()
        buy_button = QPushButton("Select to Buy")
        buy_button.clicked.connect(partial(self.select_to_buy, trade_route))
        sell_button = QPushButton("Select to Sell")
        sell_button.clicked.connect(partial(self.select_to_sell, trade_route))
        action_layout.addWidget(buy_button)
        action_layout.addWidget(sell_button)
        action_widget = QWidget()
        action_widget.setLayout(action_layout)
        self.trade_route_table.setCellWidget(i, j, action_widget)

    def select_to_buy(self, trade_route):
        self.logger.log(logging.INFO, "Selected route to buy")
        trade_tab = self.main_widget.findChild(TradeTab)
        if trade_tab:
            self.main_widget.loop.create_task(trade_tab.select_trade_route(trade_route, is_buy=True))
        else:
            self.logger.log(logging.ERROR, "An error occurred while selecting trade route")
            QMessageBox.critical(self, "Error", "An error occurred")

    def select_to_sell(self, trade_route):
        self.logger.log(logging.INFO, "Selected route to sell")
        trade_tab = self.main_widget.findChild(TradeTab)
        if trade_tab:
            self.main_widget.loop.create_task(trade_tab.select_trade_route(trade_route, is_buy=False))
        else:
            self.logger.log(logging.ERROR, "An error occurred while selecting trade route")
            QMessageBox.critical(self, "Error", "An error occurred")

    def set_gui_enabled(self, enabled):
        for input in self.findChildren(QLineEdit):
            input.setEnabled(enabled)
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setEnabled(enabled)
        for combo in self.findChildren(QComboBox):
            combo.setEnabled(enabled)
        for button in self.findChildren(QPushButton):
            button.setEnabled(enabled)
