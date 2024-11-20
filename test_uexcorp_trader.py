# test_uexcorp_trader.py
import pytest
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtGui import QColor


@pytest.mark.asyncio
async def test_uexcorp_trader_init(trader, qtbot):
    trader_instance = await trader
    assert trader_instance.windowTitle() == "UEX-Trader"
    assert not trader_instance.windowIcon().isNull()
    assert trader_instance.config_manager is not None
    assert trader_instance.layout().count() > 0


@pytest.mark.asyncio
async def test_uexcorp_trader_apply_appearance_mode(trader, app, qtbot):
    trader_instance = await trader
    app, loop = app
    trader_instance.apply_appearance_mode("Dark")
    assert app.palette().color(trader_instance.create_dark_palette().Window) == QColor(53, 53, 53)
    trader_instance.apply_appearance_mode("Light")
    assert app.palette().color(trader_instance.create_dark_palette().Window) != QColor(53, 53, 53)


@pytest.mark.asyncio
async def test_tabs_exist(trader, qtbot):
    """Test that all tabs are present."""
    tabs = trader.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 4
    assert tabs.tabText(0) == "Configuration"
    assert tabs.tabText(1) == "Trade Commodity"
    assert tabs.tabText(2) == "Find Trade Route"
    assert tabs.tabText(3) == "Best Trade Routes"
