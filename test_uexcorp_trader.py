# test_uexcorp_trader.py
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtGui import QColor


def test_uexcorp_trader_init(trader, qtbot):
    assert trader.windowTitle() == "UEX-Trader"
    assert not trader.windowIcon().isNull()
    assert trader.config_manager is not None
    assert trader.layout().count() > 0


def test_uexcorp_trader_apply_appearance_mode(trader, app, qtbot):
    app, loop = app
    trader.apply_appearance_mode("Dark")
    assert app.palette().color(trader.create_dark_palette().Window) == QColor(53, 53, 53)
    trader.apply_appearance_mode("Light")
    assert app.palette().color(trader.create_dark_palette().Window) != QColor(53, 53, 53)


def test_tabs_exist(trader, qtbot):
    """Test that all tabs are present."""
    tabs = trader.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 4
    assert tabs.tabText(0) == "Configuration"
    assert tabs.tabText(1) == "Trade Commodity"
    assert tabs.tabText(2) == "Find Trade Route"
    assert tabs.tabText(3) == "Best Trade Routes"
