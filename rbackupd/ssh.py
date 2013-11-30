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
This module provides methods to execute commands on a remote machine using
secure shell (ssh).
"""

import fcntl
import os
import random
import string
import subprocess

# in milliseconds
_CONNECT_POLL_INTERVAL = 100
_EXECUTE_POLL_INTERVAL = 100

_CONNECT_ID_LENGTH = 20
_EXECUTE_ID_LENGTH = 20


class SSHNetworkConnection(object):
    """
    Class that represents a secure shell connection to a remote machine and
    provides methods to execute remote commands.
    """
    def __init__(self, host, remote_user, port):
        """
        :param host: The host to connect to.
        :type host: NetworkHost instance
        :param remote_user: The user used to connect to the remote machine.
        :type remote_user: string
        :param port: The port to connect to on the remote host.
        :type port: int
        """
        self.host = host
        self.remote_user = remote_user
        self.port = port

        self._ssh_process = None

    def connect(self, timeout, remote_shell, ssh_args=None):
        """
        Connects to the host and starts a shell specified by remote_shell. If
        the connection is already established, does nothing.
        :param timeout: Timeout after which an error is raised in milliseconds.
        :type timeout: int
        :param remote_shell: Remote shell that is used to execute the commands.
        :type remote_shell: string
        :param ssh_args: Additional arguments passed to the ssh command.
        :type ssh_args: list
        :raises: TimeoutError if the connection times out.
        :raises: ConnectionRefusedError if an error occures during connecting.
        """
        if self._ssh_process:
            return

        connection_id = generate_id(_CONNECT_ID_LENGTH)

        args = ["ssh",
                "-o", "StrictHostKeyChecking=yes",
                "-p", str(self.port),
                "-q",
                "-x",
                "-l", self.remote_user]
        args.extend(ssh_args)
        args.extend([self.host.ip,
                     'echo {0} ; {1}'.format(connection_id, remote_shell)])

        self._ssh_process = subprocess.Popen(args, shell=False, bufsize=-1,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             stdin=subprocess.PIPE,
                                             preexec_fn=preexec)

        max_polls = timeout / _CONNECT_POLL_INTERVAL
        poll = 0

        # 0: stdout, 1: stderr
        stdpipes = (self._ssh_process.stdout, self._ssh_process.stderr)
        output = ([], [])

        # Unblock pipes so read() and readline() do not block
        for i in 0, 1:
            unblock_file_descriptor(stdpipes[i])

        # Now we will wait for a line in stdout starting with connection_id or
        # abort when timeout is exceeded
        while True:
            poll += 1
            if poll >= max_polls:
                self.disconnect()
                raise TimeoutError("connection timeout")

            # Read stdout and stderr linewise into output[] if not empty
            for i in 0, 1:
                for line in read_all(stdpipes[i]).split('\n'):
                    if line:
                        if i == 0 and line.startswith(connection_id):
                            # connected
                            break
                        output[i].append(line)
            time.sleep(_CONNECT_POLL_INTERVAL / 1000.0)

        # make output[] a nice string
        for i in 0, 1:
            output[i] = '\n'.join(output[i])

        if output[1]:
            raise ConnectionRefusedError(
                "error during connecting, host response:\n{0}".
                format(output[1]))

    def disconnect(self):
        """
        Disconnects the connection immediately. If not connection is
        established, does nothing.
        """
        if self._ssh_process:
            self._ssh_process.terminate()
            self._ssh_process = None

    def execute(self, command, timeout):
        """
        Executes a command on the remote host.
        :param command: The command to execute on the remote host.
        :type command: string
        :param timeout: Timeout after which an error is raised.
        :type timeout: int
        :returns: A tuple containing the exit code of the command and all data
        sent to stdout and stderr.
        :rtype: tuple of length 3
        :raises: TimeoutError if the command times out.
        """
        command_id = generate_id(_EXECUTE_ID_LENGTH)
        stdpipes = (self._ssh_process.stdout, self._ssh_process.stderr)

        # Flush streams as precaution
        for i in 0, 1:
            stdpipes[i].flush()

        # 0: stdout, 1: stderr
        output = ([], [])

        max_polls = timeout / _EXECUTE_POLL_INTERVAL
        polls = 0

        # Assemble command and write to the process
        # There has to be a newline before the id string, as the executed
        # command may not terminate its output with a newline. If it does, the
        # newline will be ignored anyway.
        # the line has the following format: <id>@<exit_code>
        command = '{0} ; echo \n@{1}@$?\n'.format(
            subprocess.list2cmdline(command),
            command_id)
        self._ssh_process.stdin.write(command)
        self._ssh_process.stdin.flush()

        while True:
            polls += 1
            if polls >= max_polls:
                raise TimeoutError("command timed out")
            for i in 0, 1:
                for line in read_all(stdpipes[i]).split('\n'):
                    if line:
                        output[i].append(line)
                        if i == 0 and line.startswith(command_id):
                            break
            time.sleep(_EXECUTE_POLL_INTERVAL / 1000.0)

        # now we have to retrieve the exit code out of the last line. Due to
        # the format of the last line, we can just split the line at the "@"
        # and take the second element
        last_line = output[0][-1]
        exit_code = last_line.split('@')[1]

        # delete the last line from output, as it does not belong to the
        # original command
        output[1].remove(last_line)

        # make output[] a nice string
        for i in 0, 1:
            output[i] = '\n'.join(output[i])

        return(exit_code, output[0], output[1])

    def is_connected(self):
        """
        Returns a bool that specifies whether the connection is established.
        :returns: True if a connection is established, False otherwise.
        :rtype: bool
        """
        return self._ssh_process is not None


def generate_id(length,
                chars=string.ascii_uppercase + string.ascii_lowercase +
                string.digits):
    """
    Generates a random string, usable as a more-or-less unique id.
    :param length: The length of the string.
    :type length: int
    :param chars: The pool of chars to choose from.
    :type chars: string
    """
    return ''.join(random.choice(chars) for _ in range(length))


def unblock_file_descriptor(path):
    """
    Unblocks a file descriptor, so reading it will not block.
    :param path: The path of the filedescriptor.
    :type path: string
    """
    file_descriptor = path.fileno()
    file_control = fcntl.fcntl(file_descriptor, fcntl.F_GETFL)
    fcntl.fcntl(file_descriptor, fcntl.F_SETFL, file_control | os.O_NONBLOCK)


def read_all(path):
    """
    Reads all lines of a file without blocking.
    :param path: The path to the file to read.
    :type path: string
    """
    output = []
    while True:
        line = non_blocking_read(path)
        if not line:
            break
        else:
            output.append(line)
    return "".join(output)


def non_blocking_readline(path):
    """
    What the name says, a readline() that does not block.
    :param path: The path of the file to read from.
    :type path: string
    """
    try:
        return path.readline()
    except IOError:
        return ""


def non_blocking_read(path):
    """
    What the name says, a read() that does not block.
    :param path: The path of the file to read from.
    :type path: string
    """
    try:
        return path.read()
    except IOError:
        return ""
