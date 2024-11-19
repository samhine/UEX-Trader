# main.py
import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from gui import UexcorpTrader

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    trader = UexcorpTrader(app, loop)
    trader.show()

    with loop:
        loop.run_forever()
    loop = None
