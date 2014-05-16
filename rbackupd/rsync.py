# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
This module wraps the rsync(1) command. It provides classes for special
arguments of rsync for ease of use.
"""

import logging
import os
import shlex

from rbackupd import process

logger = logging.getLogger(__name__)


def rsync(command, sources, destination, link_ref, arguments, rsyncfilter,
          loggingOptions):
    """
    Runs the rsync command with specific parameters.
    :param command: The exact command to execute. Just use "rsync" to search
    for the rsync executable in PATH
    :type command: string
    :param source: The path to the source of the transfer.
    :type source: string
    :param destination: The path to the destination of the transfer.
    :type destination: string
    :param link_ref: The path used for the --link-dest paramter of rsync. All
    files found there will not be copied from source, but hardlinked into
    destination.
    :type link_ref: string
    :param arguments: An tuple containing additional arguments that will be
    passed to rsync.
    :type arguments: tuple
    :param rsyncfilter: A Filter instance that contains information about
    filters applied to the files in the rsync transfer.
    :type rsyncfilter: Filter instance
    :param loggingOptions: A LogfileOptions instance containing information
    about the logging rsync will do.
    """
    args = [command]

    args.extend(rsyncfilter.get_args())

    args.extend(shlex.split(arguments))

    if link_ref is not None:
        args.append("--link-dest=%s" % link_ref)

    if loggingOptions is not None:
        log_path = os.path.join(destination, "..", loggingOptions.log_name)
        args.append("--log-file=%s" % log_path)
        if len(loggingOptions.log_format) != 0:
            args.append("--log-file-format=%s" % loggingOptions.log_format)

    args.extend(sources)
    args.append(destination)

    logger.verbose("Executing \"%s\".", " ".join(args))

    proc = process.Popen(args,
                         stdout=process.PIPE,
                         stderr=process.PIPE)
    (stdoutdata, stderrdata) = proc.communicate()
    return (proc.returncode, stdoutdata, stderrdata)


class LogfileOptions(object):
    """
    This class holds information about the logfile rsync will create.
    """

    def __init__(self, log_name, log_format):
        """
        :param log_name: The name of the logfile.
        :type log_name: string
        :log_format: The format of the log.
        :type log_format: string
        """
        self.log_name = log_name
        self.log_format = log_format


class Filter(object):
    """
    This class represents filters applied to the rsync file transfer.
    """

    def __init__(self, include_patterns, exclude_patterns, include_files,
                 exclude_files, filters):
        """
        :param include_patterns: A list of patterns passed to --include
        separately.
        :type include_patterns: list
        :param exclude_patterns: A list of patterns passed to --exclude
        separately.
        :type exclude_patterns: list
        :param include_files: A list of files passed to --include-file
        separately.
        :type include_files: list
        :param exclude_files: A list of files passed to --exclude-file
        separately.
        :type exclude_files: list
        :param filters: A list of filter statements passed to --filter
        separately.
        :type filters: list
        """
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.include_files = include_files
        self.exclude_files = exclude_files
        self.filters = filters

    def get_args(self):
        """
        Constructs a list of arguments containing all desired filters ready
        to be passed to to subprocess.Popen().
        """
        args = []
        for rfilter in self.filters:
            args.extend(["--filter", rfilter])

        for pattern in self.include_patterns:
            args.extend(["--include", pattern])

        for patternfile in self.include_files:
            args.extend(["--include-from", patternfile])

        for pattern in self.exclude_patterns:
            args.extend(["--exclude", pattern])

        for patternfile in self.exclude_files:
            args.extend(["--exclude-from", patternfile])

        return args
