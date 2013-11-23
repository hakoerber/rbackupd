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
This module wraps the rsync(1) command. It provides classes for special
arguments of rsync for ease of use.
"""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def rsync(cmd, source, destination, link_ref, arguments, rsyncfilter,
          loggingOptions):
    """
    Runs the rsync command with specific parameters.
    :param cmd: The exact command to execute. Just use "rsync" to search for
    the rsync executable in PATH
    :type cmd: string
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
    args = [cmd]

    args.extend(rsyncfilter.get_args())

    args.extend(arguments)

    if link_ref is not None:
        args.append("--link-dest=%s" % link_ref)

    if loggingOptions is not None:
        args.append("--log-file=%s" % os.path.join(destination,
                                                   loggingOptions.log_name))
        if loggingOptions.log_format is not None:
            args.append("--log-file-format=%s" % loggingOptions.log_format)

    args.append(source)
    args.append(destination)

    logging.verbose("Executing \"%s\".", " ".join(args))

    # create the directory first, otherwise logging will fail
    os.mkdir(destination)

    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
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
            if rfilter == "" or rfilter is None:
                continue
            args.extend(["--filter", rfilter])

        for pattern in self.include_patterns:
            if pattern == "" or pattern is None:
                continue
            args.extend(["--include", pattern])

        for patternfile in self.include_files:
            if patternfile == "" or patternfile is None:
                continue
            args.extend(["--include-from", patternfile])

        for pattern in self.exclude_patterns:
            if pattern == "" or pattern is None:
                continue
            args.extend(["--exclude", pattern])

        for patternfile in self.exclude_files:
            if patternfile == "" or patternfile is None:
                continue
            args.extend(["--exclude-from", patternfile])

        return args
