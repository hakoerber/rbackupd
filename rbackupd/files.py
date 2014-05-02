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
This module wraps frequently needed operations on files and directories.
"""

import logging
import os

from rbackupd import cmd

logger = logging.getLogger(__name__)


def remove_symlink(path):
    """
    Removes a symlink.
    :param path: The path of the symlink.
    :type path: string
    """
    # to remove a symlink, we have to strip the trailing
    # slash from the path
    if not os.path.islink(path):
        raise ValueError("%s not a symlink" % path)
    args = ["rm", path.rstrip("/")]
    cmd.check_call(args)


def create_symlink(target, linkname):
    """
    Creates a symlink at <linkname> that points to <target>.
    :param target: The target the symlink points to.
    :type target: string
    :param linkname: The path of the symlink.
    :type linkname: string
    """
    if not os.path.exists(target):
        raise ValueError("%s does not exist" % target)
    if os.path.exists(linkname):
        raise ValueError("%s already exists" % linkname)
    args = ["ln", "-s", "-r", target, linkname]
    cmd.check_call(args)


def move(path, target):
    """
    Moves a file or directory.
    :param path: The path to the file/directory to move.
    :type path: string
    :param target: The path to move to.
    :type target: string
    """
    if not os.path.exists(path):
        raise ValueError("%s does not exist" % path)
    if os.path.exists(target):
        raise ValueError("%s does already exist" % target)
    args = ["mv", path, target]
    cmd.check_call(args)


def remove_recursive(path):
    """
    Removes a file or directory. If the target is a directory, it will be
    deleted recursively.
    :param path: The path to delete.
    :type path: string
    """
    if not os.path.exists(path):
        raise ValueError("%s does not exist" % path)
    args = ["rm", "-r", "-f", path]
    cmd.check_call(args)


def copy_hardlinks(path, target):
    """
    Makes a copy of a file or directory, the files or all files in the
    directory will be hardlinked together.
    :param path: The source of the operation.
    :type path: string
    :param taget: The path to copy to.
    :type target: string
    """
    if not os.path.exists(path):
        raise ValueError("%s does not exist" % path)
    if os.path.exists(target):
        raise ValueError("%s does already exist" % target)
    # we could alternatively use rsync with destination being the same as
    # link-dest, this would create only hardlinks, too
    args = ["cp", "-a", "-l", path, target]
    cmd.check_call(args)
