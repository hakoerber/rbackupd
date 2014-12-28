import time
import multiprocessing
import logging

logger = logging.getLogger(__name__)

class Timer(object):
    def __init__(self, name, **kwargs):
        assert(kwargs["type"] == "cron")
        self._interval = kwargs["interval"]
        self._name = name
        self._callbacks = []
        self._process = None

    def get_name(self):
        return self._name

    def start(self):
        logger.debug("Starting new timing process.")
        self._process = multiprocessing.Process(
            target=self._sideprocess,
            args=())
        self._process.start()
        logger.debug("Process startup successful.")

    def _sideprocess(self):
        logger.debug("Timing process here.")
        while True:
            if self._name == "daily":
                time.sleep(16)
            else:
                time.sleep(1)
            self._trigger()
            time.sleep(4)

    def subscribe(self, func):
        self._callbacks.append(func)

    def _trigger(self):
        logger.debug("Timing process triggered.")
        for func in self._callbacks:
            func(self)
