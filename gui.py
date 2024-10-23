import sys
import logging
from PyQt5.QtWidgets import QApplication, QTabWidget, QVBoxLayout, QWidget, QStyleFactory
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt
from config_tab import ConfigTab
from trade_tab import TradeTab
from trade_route_tab import TradeRouteTab
from logger_setup import setup_logger
from config_manager import ConfigManager

class UexcorpTrader(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.config_manager = ConfigManager()
        self.setup_logger()
        self.initUI()
        self.apply_appearance_mode()

    def setup_logger(self):
        debug = self.config_manager.get_debug()
        logging_level = logging.DEBUG if debug else logging.INFO
        setup_logger(logging_level)

    def initUI(self):
        self.setWindowTitle("UEXcorp Trader")
        self.setWindowIcon(QIcon("resources/UEXTrader_icon_resized.png"))

        tabs = QTabWidget()
        tabs.addTab(ConfigTab(self), "Configuration")
        tabs.addTab(TradeTab(self), "Trade Commodity")
        tabs.addTab(TradeRouteTab(self), "Find Trade Route")

        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

    def apply_appearance_mode(self, appearance_mode=None):
        if not appearance_mode:
            appearance_mode = self.config_manager.get_appearance_mode()
        if appearance_mode == "Dark":
            self.app.setStyle(QStyleFactory.create("Fusion"))
            dark_palette = self.create_dark_palette()
            self.app.setPalette(dark_palette)
        else:
            self.app.setStyle(QStyleFactory.create("Fusion"))
            self.app.setPalette(QApplication.style().standardPalette())

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    trader = UexcorpTrader()
    trader.show()
    sys.exit(app.exec_())
