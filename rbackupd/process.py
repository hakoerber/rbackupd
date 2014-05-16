# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

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
