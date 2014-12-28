# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import argparse
import sys
import logging

from rbackupd import constants as const
from rbackupd import manager
from rbackupd.version import __version__

logger = logging.getLogger(__name__)

VERSION = "%(prog)s {version}".format(version=__version__)


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("-c",
                        "--config",
                        metavar="PATH",
                        dest="path_config",
                        default=const.DEFAULT_PATH_CONFIG,
                        action="store",
                        help="alternative configuration file [default: %s]" %
                        const.DEFAULT_PATH_CONFIG)

    parser.add_argument("-v",
                        "--verbose",
                        dest="verbose",
                        default=False,
                        action="store_true",
                        help="be more verbose")

    parser.add_argument("-q",
                        "--quiet",
                        dest="quiet",
                        default=False,
                        action="store_true",
                        help="only show warnings and errors")

    parser.add_argument("--debug",
                        dest="debug",
                        default=False,
                        action="store_true",
                        help="enable debug output")

    parser.add_argument("--version",
                        action="version",
                        version=VERSION)

    commandline = parser.parse_args(argv)

    if commandline.debug:
        loglevel = logging.DEBUG
    elif commandline.verbose:
        loglevel = logging.VERBOSE
    elif commandline.quiet:
        loglevel = logging.WARNING
    else:
        loglevel = logging.INFO

    logging.change_console_logging_level(loglevel)
    logger.debug("Starting with argv=%s" % argv)
    manager.start(commandline.path_config)
