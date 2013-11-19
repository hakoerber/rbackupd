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
Module to handle partitions and mountpoints.
"""

import os
import subprocess


class PartitionIdentifiers(object):
    UUID = 0
    LABEL = 1
    PATH = 2


class PartitionIdentifier(object):
    """
    A token that identifies a specific partition. This can either be a UUID,
    the label of the partition or a path representing the partition, usually
    some file in the /dev directory.
    """
    def __init__(self, uuid=None, label=None, path=None):
        if [uuid, label, path].count(None) != 2:
            raise ValueError("Ambiguous identifiers")
        if uuid is not None:
            self._identifier = (PartitionIdentifiers.UUID, uuid)
        elif label is not None:
            self._identifier = (PartitionIdentifiers.LABEL, label)
        else:
            self._identifier = (PartitionIdentifiers.PATH, path)

    @property
    def identifier(self):
        return self._identifier


class MountpointInUseError(Exception):
    """
    This exception is raised when a mountpoint is already active when a
    partition is mounted there.
    """
    def __init__(self, path):
        super(MountpointInUseError, self).__init__(path)
        self.path = path


class Partition(object):
    """
    Represents a partition.
    """
    def __init__(self, partition_identifier, filesystem):
        """
        :param partition_identifier: A PartitionIdentifier instance
        representing the partition.
        :type partition_identifier: PartitionIdentifier instance
        :param filesystem: The filesystem of the partition. If you are not
        sure, try "auto" and mount() will try to guess the filesystem.
        :type filesystem: string
        """
        self.partition_identifier = partition_identifier
        self.filesystem = filesystem

    def mount(self, mountpoint):
        """
        Mounts the partition on a mountpoint.
        :param mountpoint: The mountpoint where the partition will be mounted
        at.
        :type mountpoint: Mountpoint instance
        """
        if os.path.ismount(mountpoint.path):
            raise MountpointInUseError(mountpoint.path)

        identifier = self.partition_identifier.identifier
        if identifier[0] == PartitionIdentifiers.UUID:
            partition_args = ["-U", identifier[1]]
        elif identifier[0] == PartitionIdentifiers.LABEL:
            partition_args = ["-L", identifier[1]]
        elif identifier[0] == PartitionIdentifiers.PATH:
            partition_args = [identifier[1]]
        args = ["mount",
                "-o", ",".join(mountpoint.options).lstrip(','),
                "-t", self.filesystem]
        args.extend(partition_args)
        args.append(mountpoint.path)
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError:
            raise


class Mountpoint(object):
    """
    Represents a mountpoint and provices methods to mount and unmount devices
    on this mountpoint, among others.
    """
    def __init__(self, path, options):
        """
        :param path: The absolute path of the mountpoint.
        :type path: string
        :param options: A tuple containing all mount options.
        :type options: tuple of strings
        """
        self.path = path
        self.options = options

    def remount(self, new_options=None):
        """
        Remounts the partition on this mountpoint with different options if any
        are given.
        :param new_options: The options for the remount, if None is given the
        old options will be used.
        :type newOptions: tuple or None
        """
        if new_options is None:
            new_options = self.options
        args = ["mount",
                "-o",
                (','.join(new_options) + ",remount").lstrip(','),
                self.path]
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError as err:
            raise

    def bind(self, target):
        """
        Binds this mountpoint to another mountpoint.
        :param target: Path to the binding mountpoint.
        :type target: string
        :returns: A new mountpoint instance that represents the binding
        mountpoint
        """
        if os.path.ismount(target.path):
            raise MountpointInUseError(target.path)
        args = ["mount",
                "--bind",
                self.path,
                target.path]
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError as err:
            print(err.output)
            raise
