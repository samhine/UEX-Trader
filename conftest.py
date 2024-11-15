# conftest.py
import pytest
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from gui import UexcorpTrader


@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    yield app, loop
    loop.close()
    app.quit()


@pytest.fixture
def trader(app, qtbot):
    app, loop = app
    trader = UexcorpTrader(app, loop)
    qtbot.addWidget(trader)
    yield trader

