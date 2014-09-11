# -*- encoding: utf-8 -*-
# Copyright (c) 2014 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import subprocess


class SSHInfo(object):

    def __init__(self, host, user, port, identity_file):
        self.host = host
        self.user = user
        self.port = port
        self.identity_file = identity_file


class RemoteLocation(object):

    def __init__(self, ssh_info, path):
        self.ssh_info = ssh_info
        self.path = path

    def mount(self, mountpoint):
        self._mountpoint = mountpoint
        args = ["sshfs",
                "-o", "IdentityFile=\"{idfile}\"".format(
                    idfile=self.ssh_info.identity_file),
                "{user}@{host}:{folder}".format(user=self.ssh_info.user,
                                                host=self.ssh_info.host,
                                                folder=self.path),
                mountpoint]
        try:
            subprocess.check_output(args,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True)
        except subprocess.CalledProcessError:
            raise

    def remount(self):
        pass
