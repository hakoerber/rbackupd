import logging


class LevelFilter(object):
    def __init__(self, minlvl=logging.NOTSET, maxlvl=logging.NOTSET):
        self._minlvl = minlvl
        self._maxlvl = maxlvl

    def filter(self, record):
        if (self.get_min_level() != logging.NOTSET and
                record.levelno < self.get_min_level()):
            return False
        if (self.get_max_level() != logging.NOTSET and
                record.levelno > self.get_max_level()):
            return False
        return True

    def get_min_level(self):
        return self._minlvl

    def get_max_level(self):
        return self._maxlvl

    def __set_min_level(self, minlvl):
        self._minlvl = minlvl

    def __set_max_level(self, maxlvl):
        self._maxlvl = maxlvl
