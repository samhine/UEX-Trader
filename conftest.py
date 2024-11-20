# conftest.py
import pytest
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from gui import UexcorpTrader
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def app(event_loop):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    yield app, loop
    loop.close()
    app.quit()


@pytest_asyncio.fixture
async def trader(app, event_loop, config_manager):
    app, loop = app
    trader = UexcorpTrader(app, loop)
    await trader.initialize()
    yield trader
    await trader.cleanup()


# Add this fixture to handle API initialization and cleanup
@pytest_asyncio.fixture(scope="session")
async def api(config_manager, app):
    from api import API  # Import your API class
    api = API(config_manager)
    await api.initialize()
    yield api
    await api.cleanup()  # Add a cleanup method to your API class


@pytest_asyncio.fixture(scope="session")
async def config_manager():
    from config_manager import ConfigManager
    if ConfigManager._instance is None:
        config_manager = ConfigManager()
    else:
        config_manager = ConfigManager._instance
    yield config_manager
