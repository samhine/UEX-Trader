import pytest
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
import pytest_asyncio
from gui import UexcorpTrader


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def qapp(event_loop):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    yield app
    app.quit()


@pytest_asyncio.fixture(scope="session")
async def config_manager():
    from config_manager import ConfigManager
    if ConfigManager._instance is None:
        config_manager = ConfigManager()
    else:
        config_manager = ConfigManager._instance
    yield config_manager


@pytest_asyncio.fixture(scope="session")
async def api(config_manager, qapp):
    from api import API
    api = API(config_manager)
    await api.initialize()
    yield api
    await api.cleanup()


@pytest_asyncio.fixture
async def trader(qapp, config_manager):
    loop = asyncio.get_event_loop()
    trader = UexcorpTrader(qapp, loop)
    await trader.initialize()
    yield trader
    await trader.cleanup()