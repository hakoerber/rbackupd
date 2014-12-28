#!/usr/bin/env python

import yaml
import pprint
import time
import logging
import os

from rbackupd import backupmodules
from rbackupd import storagemodules
from rbackupd import timermodules
from rbackupd import task

logger = logging.getLogger(__name__)

def _load_config(path):
    logger.debug("Using config file \"%s\"", path)
    if not os.path.exists(path):
        logger.critical("Configuration file at %s not found. Aborting.",
                        path)
        raise Exception()
    conf = yaml.load(open(path))
    logger.debug("Parsed config like this:\n%s",
                 pprint.pformat(conf, indent=4, width=100))
    return conf

def _load_modules(moduletype):
    modules = {}
    for name, info in conf[moduletype.__name__.split('.')[-1]].items():
        logger.debug("Trying to load module \"%s\"." % name)
        module = moduletype.get_module(info["type"])
        modules[name] = module(name=name, **info)
        logger.debug("Successfully loaded module \"%s\"." % name)
    return modules

def _load_tasks(storagemanagers, backupcreators, timers):
    tasks = {}
    for name, info in conf["tasks"].items():
        newtask = task.Task(
            name=name,
            backupmodule=backupcreators[info["backupmodule"]["name"]],
            storagemodule=storagemanagers[info["storagemodule"]["name"]],
            sources=info["sources"],
            timers=[timer for timername, timer in timers.items()
                if timername in info["timers"]])
        tasks[name] = newtask
    return tasks

def _loglevel_to_int(level):
    mapping = {
        "quiet"   : logging.WARNING,
        "default" : logging.INFO,
        "verbose" : logging.VERBOSE,
        "debug"   : logging.DEBUG}
    return mapping[level]

def _setup_logfile():
    logging.change_to_logfile_logging(
        logfile_path=conf["logging"]["logfile"],
        loglevel=_loglevel_to_int(conf["logging"]["loglevel"]))

def start(config_path):
    global conf
    conf = _load_config(config_path)

    _setup_logfile()

    logger.debug("Loading storage modules.")
    storagemanagers = _load_modules(moduletype=storagemodules)
    logger.debug("Storage modules found: %s.", list(storagemanagers.keys()))
    logger.debug("Loading backup modules.")
    backupcreators = _load_modules(moduletype=backupmodules)
    logger.debug("Backup modules found: %s.", list(backupcreators.keys()))
    logger.debug("Loading timer modules.")
    timers = _load_modules(moduletype=timermodules)
    logger.debug("Timer modules found: %s.", list(timers.keys()))

    tasks = _load_tasks(storagemanagers, backupcreators, timers)

    logger.debug("Initialization completed.")
    while True:
        time.sleep(10)
