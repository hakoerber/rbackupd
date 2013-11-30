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
This module provides methods to mount a directory on a remote machine into the
local file tree using sshfs.
"""

import getpass
import subprocess


class SSHFSConnection(object):
    """
    Represents a sshfs connection to a remote machine.
    """
    def __init__(self, local_mountpoint, remote_directory, remote_user=None):
        """
        :param local_mountpoint: The directory where the remote directory will
        be mounted at.
        :type local_mountpoint: string
        :param remote_directory: The remote directory that will be available
        locally.
        :type remote_directory: NetworkPath
        :param remote_user: The remote user that will be used on the remote
        host. If omitted, the current user will be used.
        :type remote_user: string
        """
        self._local_mountpoint = local_mountpoint
        self._remote_directory
        if remote_user is None:
            self._remote_user = getpass.getuser()
        else:
            self._remote_user = remote_user
        self._mounted = False

    def mount(self, options):
        """
        Mounts the remote directory into the local file hierarchy.
        :param options: Additional options that will be passed to sshfs.
        :type options: list
        :returns: A tuple containing the stdout and stderr output of the ssh
        process
        :rtype: tuple
        """
        source = "{user}@{host}:{directory}".format(
            user=self._remote_user,
            host=self._remote_direcotry.host.get_identifier(),
            directory=self._remote_direcotry.path)
        args = ["sshfs",
                source,
                self.local_mountpoint]
        args.extend(options)
        subprocess.check_call(args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        self._mounted = True
        return (stdout, stderr)

    def unmount(self):
        """
        Unmounts the remote directory.
        """
        if self._mounted:
            return
        args = ["fusermount", "-u", self._local_mountpoint]
        subprocess.check_call(args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        self._mounted = False
        return (stdout, stderr)
