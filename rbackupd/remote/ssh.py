# -*- encoding: utf-8 -*-
# Copyright (c) 2014 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import subprocess
import logging
import paramiko
import socket
import os
import sys
import getpass
import binascii

logger = logging.getLogger(__name__)

class ConnectionParameters(object):

    def __init__(self, host, port=None, user=None, identity_file=None,
                 auto_add_host_key=False):
        self.host = host
        if not host.is_localhost():
            if port is None:
                self.port=22
            else:
                self.port=port

            if identity_file is None:
                self.use_ssh_agent=True
            else:
                self.use_ssh_agent=False
            self.identity_file=identity_file

            if user is None:
                self.user = getpass.getuser()
            else:
                self.user = user

            self.auto_add_host_key = auto_add_host_key
        else:
            if port is not None:
                logger.warning("port is ignored for local execution")
            if user is not None:
                logger.warning("user is ignored for local execution.")
            if identity_file is not None:
                logger.warning("identity_file is ignored for local execution.")


class Connection(object):

    def __init__(self, connection_parameters):
        self.connection_parameters = connection_parameters
        self._transport = None

    def _get_fingerprint(self, key):
        fp = binascii.hexlify(key.get_fingerprint()).decode("ascii")
        ret = ""
        for i in range(len(fp)):
            if (i % 2) == 0 and not i == 0:
                ret += ':'
            ret += fp[i]
        return ret

    def connect(self):
        print("connecting")
        host = self.connection_parameters.host
        port = self.connection_parameters.port
        user = self.connection_parameters.user
        identity = self.connection_parameters.identity_file
        auto_add_host_key = self.connection_parameters.auto_add_host_key

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        try:
            sock.connect((host.ip, int(port)))
        except OSError as e:
            logger.critical("Connection failed: %s", e.strerror)
            sys.exit(1)

        t = paramiko.Transport(sock)

        try:
            t.start_client()
        except paramiko.SSHException:
            logger.critical("SSH negotiation failed.")
            sys.exit(1)

        known_hosts_file = os.path.expanduser('~/.ssh/known_hosts')
        try:
            keys = paramiko.util.load_host_keys(known_hosts_file)
        except IOError:
            logger.error("Known hosts file not found at \"%s\".",
                         known_hosts_file)
            keys = {}

        key = t.get_remote_server_key()
        if host.ip not in keys or key.get_name() not in keys[host.ip]:
            logger.warning("Unknown host key.")
            if auto_add_host_key:
                logger.info(
                    "Adding host key with fingerprint %s %s from host %s to "
                    "the known_hosts file at %s.",
                    key.get_name(),
                    self._get_fingerprint(key),
                    host.ip,
                    known_hosts_file)
                keys.add(hostname=host.ip,
                         keytype=key.get_name(),
                         key=key)
                #keys.save(known_hosts_file)
            else:
                raise Exception("Unknown host key will not be added.")
        elif keys[host.ip][key.get_name()] != key:
            logger.warning("Host key has changed.")
            raise paramiko.BadHostKeyException(
                hostname=host.ip,
                got_key=key,
                expected_key=keys[host.ip][key.get_name()])
        else:
            logger.verbose("Host key ok.")

        try:
            key = paramiko.RSAKey.from_private_key_file(identity)
        except paramiko.PasswordRequiredException:
            logger.critical("Key file \"%s\" is password protected. SSH agent "
                            "support is not implemented yet.",
                            identity)
            sys.exit(1)

        try:
            t.auth_publickey(user, key)
        except paramiko.BadAuthenticationType:
            logger.critical("Pubkey authentication is not allowed on the "
                            "server at \"%s\".", host.ip)
            sys.exit(1)
        except paramiko.AuthenticationException:
            logger.critical("Pubkey authentication failed.")
            sys.exit(1)

        self._transport = t

    def execute(self, args, join_output=True):
        if self._transport is None:
            self.connect()

        channel = self._transport.open_channel(kind="session")

        cmdline = " ".join(args)
        print(args)
        channel.exec_command(cmdline)
        stdout = channel.makefile('r', -1)
        stderr = channel.makefile_stderr('r', -1)
        retval = channel.recv_exit_status()

        stdout = stdout.readlines()
        if join_output:
            stdout.extend(stderr.readlines())
        stdout = "\n".join(stdout)
        return (retval, stdout)
