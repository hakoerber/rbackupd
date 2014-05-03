# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>
#
# This file is part of rbackupd.
#
# rbackupd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rbackupd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import sys
import logging

from rbackupd import backupmanager
from rbackupd import constants as const
from rbackupd import levelhandler

logger = logging.getLogger(__name__)


VERSION = "%(prog)s v0.5-dev"



def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("-c",
                        "--config",
                        metavar="PATH",
                        dest="path_config",
                        default=const.DEFAULT_PATH_CONFIG,
                        action="store",
                        help="alternative configuration file [default: %s]" %
                             const.DEFAULT_PATH_CONFIG
                        )

    parser.add_argument("-v",
                        "--verbose",
                        dest="verbose",
                        default=False,
                        action="store_true",
                        help="be more verbose"
                        )

    parser.add_argument("-q",
                        "--quiet",
                        dest="quiet",
                        default=False,
                        action="store_true",
                        help="only show warnings and errors"
                        )

    parser.add_argument("--debug",
                        dest="debug",
                        default=False,
                        action="store_true",
                        help="enable debug output"
                        )

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

    try:
        logging.change_console_logging_level(loglevel)
        manager = backupmanager.BackupManager(commandline.path_config)
        manager.start()
    except KeyboardInterrupt:
        logger.debug("Caught KeyboardInterrupt")
        logger.info("Keyboard interrupt.")
        sys.exit(const.EXIT_KEYBOARD_INTERRUPT)
    except SystemExit as err:
        logger.debug("Caught SystemExit")
        logger.info("Exiting with code %s.", err.code)
        sys.exit(err.code)
