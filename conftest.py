# conftest.py
import asyncio
from PyQt5.QtWidgets import QApplication
import pytest_asyncio
from gui import UexcorpTrader


@pytest_asyncio.fixture(scope="session")
async def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    app.quit()


@pytest_asyncio.fixture(scope="session")
async def config_manager():
    from config_manager import ConfigManager
    config_manager = ConfigManager()
    await config_manager.initialize()  # Ensure this is asynchronous
    yield config_manager


@pytest_asyncio.fixture
async def trader(qapp, config_manager):
    trader = UexcorpTrader(qapp, asyncio.get_event_loop())
    await trader.initialize()
    yield trader
    await trader.cleanup()
