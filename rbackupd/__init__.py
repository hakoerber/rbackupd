# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
The rbackupd daemon package.
"""
import sys
import logging
import logging.handlers

from rbackupd import levelhandler
from rbackupd import constants as const


def change_console_logging_level(loglevel):
    logger.debug("Changing logging level for console to \"%s\".",
                 logging.getLevelName(loglevel))
    for handler in logging_console_handlers:
        handler.setLevel(loglevel)
logging.change_console_logging_level = change_console_logging_level


def change_file_logging_level(loglevel):
    logger.debug("Changing logging level for log file to \"%s\".",
                 logging.getLevelName(loglevel))
    for handler in logging_file_handlers:
        handler.setLevel(loglevel)
logging.change_file_logging_level = change_file_logging_level


def change_to_logfile_logging(logfile_path, loglevel):
    logger.debug("Switching from logging to memory to logging to file at "
                 "\"%s\" with level \"%s\".",
                 logfile_path,
                 logging.getLevelName(loglevel))
    global logging_memory_handler
    if logging_memory_handler is None:
        return

    logfile_handler = logging.handlers.RotatingFileHandler(
        logfile_path,
        mode='a',
        maxBytes=const.LOGFILE_MAX_BYTES,
        backupCount=const.LOGFILE_BACKUP_COUNT)

    logfile_handler.setLevel(loglevel)

    logfile_handler.setFormatter(logfile_formatter)

    logging_memory_handler.setTarget(logfile_handler)
    logging_memory_handler.flush()
    logging_memory_handler.close()

    logger.addHandler(logfile_handler)
    logging_file_handlers.append(logfile_handler)

    logger.removeHandler(logging_memory_handler)
    logging_file_handlers.remove(logging_memory_handler)
    logging_memory_handler = None
    logger.debug("Successfully switched to file logging.")

logging.change_to_logfile_logging = change_to_logfile_logging

logger = logging.getLogger(__name__)
logging_memory_handler = None
logging_console_handlers = []
logging_file_handlers = []

# custom log levels
logging.VERBOSE = 15
# necessary to get the name in log output instead of an integer
logging.addLevelName(logging.VERBOSE, "VERBOSE")
logging.Logger.verbose = \
    lambda obj, msg, *args, **kwargs: \
    obj.log(logging.VERBOSE, msg, *args, **kwargs)


# setting logleve to minimum level, as the handlers take care of the
# filtering by level
logger.setLevel(logging.DEBUG)

# console handlers
stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)

stdout_handler.addFilter(levelhandler.LevelFilter(
    minlvl=logging.NOTSET,
    maxlvl=logging.WARNING - 1))
stderr_handler.addFilter(levelhandler.LevelFilter(
    minlvl=logging.WARNING,
    maxlvl=logging.CRITICAL))

stdout_handler.setLevel(logging.INFO)
stderr_handler.setLevel(logging.INFO)

console_formatter = logging.Formatter(
    fmt="[{asctime}] {message}",
    datefmt="%H:%M:%S",
    style='{')

stdout_handler.setFormatter(console_formatter)
stderr_handler.setFormatter(console_formatter)

logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)

logging_console_handlers.append(stdout_handler)
logging_console_handlers.append(stderr_handler)

# logfile_handlers
logging_memory_handler = logging.handlers.MemoryHandler(
    capacity=1000000,
    flushLevel=logging.CRITICAL + 1,  # we do not want it to auto-flush
    target=None)  # we will set the target when a logfile is available

logging_memory_handler.setLevel(logging.DEBUG)

logfile_formatter = logging.Formatter(
    fmt="[{asctime}] [{levelname}] {filename}: {message}",
    datefmt="%Y-%m-%d %H:%M:%S",
    style='{')

logging_memory_handler.setFormatter(logfile_formatter)

logger.addHandler(logging_memory_handler)

logging_file_handlers.append(logging_memory_handler)
logger.debug("Logging setup completed.")
