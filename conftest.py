# conftest.py
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
import pytest_asyncio
from gui import UexcorpTrader


@pytest_asyncio.fixture(scope="session")
async def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def qapp(event_loop):
    app = QApplication.instance() or QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    yield app
    app.quit()


@pytest_asyncio.fixture(scope="session")
async def config_manager():
    from config_manager import ConfigManager
    config_manager = ConfigManager()
    await config_manager.initialize()
    yield config_manager


@pytest_asyncio.fixture
async def trader(qapp, config_manager):
    trader = UexcorpTrader(qapp, asyncio.get_event_loop())
    await trader.initialize()
    yield trader
    await trader.cleanup()
