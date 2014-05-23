# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import logging


class LevelFilter(object):
    """
    This is a custom filter for the logging module that filters a range of
    loglevels. This might be useful if messages below a certain level should
    go to a different handler than "higher" messages, for example if you want
    to destinguish between stdout and stderr.

    :param minlvl: The lower loglevel boundary. If not set, there is no lower
                   boundary.
    :type minlvl: int

    :param maxlvl: The upper loglevel boundary. If not set, there is no upper
                   boundary.
    :type maxlvl: int
    """
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
