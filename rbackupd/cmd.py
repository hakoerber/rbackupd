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

"""
This module wraps the subprocess module and adds logging funcionality.
"""

import logging
import subprocess

logger = logging.getLogger(__name__)

PIPE = subprocess.PIPE


def check_call(*args, **kwargs):
    """
    Wraps subprocess.check_call().
    """
    logger.debug("Calling subprocess.check_call() with args \"%s\".", args)
    subprocess.check_call(*args, **kwargs)


def check_output(*args, **kwargs):
    """
    Wraps subprocess.check_output().
    """
    logger.debug("Calling subprocess.check_output() with args \"%s\".", args)
    subprocess.check_output(*args, **kwargs)


class Popen(subprocess.Popen):
    pass


class CalledProcessError(subprocess.CalledProcessError):
    pass
