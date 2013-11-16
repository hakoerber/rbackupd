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

import subprocess


def remove_symlink(path):
    # to remove a symlink, we have to strip the trailing
    # slash from the path
    args = ["rm", path.rstrip("/")]
    subprocess.check_call(args)


def create_symlink(target, linkname):
    args = ["ln", "-s", "-r", target, linkname]
    subprocess.check_call(args)


def move(path, target):
    args = ["mv", path, target]
    subprocess.check_call(args)


def remove_recursive(path):
    args = ["rm", "-r", "-f", path]
    subprocess.check_call(args)


def copy_hardlinks(path, target):
    # we could alternatively use rsync with destination
    # being the same as link-dest, this would create
    # only hardlinks, too
    args = ["cp", "-a", "-l", path, target]
    subprocess.check_call(args)
