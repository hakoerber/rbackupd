"""Module to handle devices and mountpoints."""

import os
import subprocess


class DeviceIdentifiers(object):
    UUID = 0
    LABEL = 1
    PATH = 2


class DeviceIdentifier(object):
    def __init__(self, uuid=None, label=None, path=None):
        if [uuid, label, path].count(None) != 2:
            raise ValueError("Ambiguous identifiers")
        if uuid is not None:
            self._identifier = (DeviceIdentifiers.UUID, uuid)
        elif label is not None:
            self._identifier = (DeviceIdentifiers.LABEL, label)
        else:
            self._identifier = (DeviceIdentifiers.PATH, path)

    def get(self):
        return self._identifier


class Device(object):
    """
    Represents a hardware storage device on a specific host, identified by its
    UUID.
    """
    def __init__(self, device_identifier, filesystem):
        """
        :param device_identifier: A DeviceIdentifier instance representing the
        device.
        :type device_identifier: DeviceIdentifier
        :param filesystem: The filesystem of the device. If you are not sure,
        try "auto" and mount() will try to guess the filesystem.
        :type filesystem: string
        """
        self.device_identifier = device_identifier
        self.filesystem = filesystem

    def mount(self, mountpoint):
        """
        Mounts the device on a mountpoint.
        :param mountpoint: The mountpoint where the device will be mounted
        at.
        :type mountpoint: Mountpoint instance
        """
        if os.path.ismount(mountpoint.path):
            print("%s is already a mountpoint" % mountpoint.path)
            return
        identifier = self.device_identifier.get()
        if identifier[0] == DeviceIdentifiers.UUID:
            device_args = ["-U", identifier[1]]
        elif identifier[0] == DeviceIdentifiers.LABEL:
            device_args = ["-L", identifier[1]]
        elif identifier[0] == DeviceIdentifiers.PATH:
            device_args = [identifier[1]]
        args = ["mount",
                "-o", ",".join(mountpoint.options).lstrip(','),
                "-t", self.filesystem]
        args.extend(device_args)
        args.append(mountpoint.path)
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError as err:
            raise


class Mountpoint(object):
    """
    Represents a mountpoint on a specific host and provices methods to mount
    and unmount devices on this mountpoint, among others.
    """
    def __init__(self, path, options):
        """
        :param path: The absolute path on the specified host.
        :type path: string
        :param options: A tuple containing all mount options.
        :type options: tuple
        """
        self.path = path
        self.options = options

    def remount(self, new_options=None):
        """
        Remounts the device on this mountpoint with different options if any
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
            print(err.output)
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
            print("%s is an active mountpoint, no binding" % target.path)
            return
        args = ["mount",
                "--bind",
                self.path,
                target.path]
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError as err:
            print(err.output)
            raise
