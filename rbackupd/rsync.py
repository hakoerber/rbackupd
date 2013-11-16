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

import os
import subprocess


def rsync(cmd, source, destination, link_ref, arguments, rsyncfilter,
          loggingOptions):
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

    print(" ".join(args))

    # create the directory first, otherwise logging will fail
    os.mkdir(destination)

    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (stdoutdata, stderrdata) = proc.communicate()
    return (proc.returncode, stdoutdata, stderrdata)


class LogfileOptions(object):

    def __init__(self, log_name, log_format):
        self.log_name = log_name
        self.log_format = log_format


class Filter(object):

    def __init__(self, include_patterns, exclude_patterns, include_files,
                 exclude_files, filters):
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.include_files = include_files
        self.exclude_files = exclude_files
        self.filters = filters

    def get_args(self):
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
