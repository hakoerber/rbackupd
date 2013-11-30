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
This module is used to identify hosts in a network. Hosts can either be
specified by their ip or by their hostname.
"""


def get_localhost():
    """
    Always returns a NetworkHost instance that represents the localhost.
    """
    return NetworkHost(ip="127.0.0.1")


class NetworkHost(object):
    """
    Represents a host in a network.
    """
    def __init__(self, ip=None, hostname=None):
        """
        :param ip: The ip of the machine.
        :type ip: string
        :param hostname: The hostname of the machine.
        :type hostname: string
        :raise ValueError: if neither ip nor hostname are specified
        """
        if ip is None and hostname is None:
            raise ValueError("either ip or hostname must be specified")
        try:
            if ip is not None:
                self.ip = ip
                self.hostname = None
            else:
                self.ip = socket.gethostbyname(hostname)
                self.hostname = hostname
        except socket.gaierror:
            raise ValueError("unknown hostname")

    def get_identifier(self):
        """
        Returns the hostname if available, otherwise the ip.
        """
        if self.hostname is None:
            return self.ip
        else:
            return self.hostname

    def is_localhost(self):
        """
        Determines whether the host represents the localhost.
        """
        return self.ip.startswith("127.")

    def __eq__(self, other):
        if self.is_localhost() and other.is_localhost():
            return True
        return self.ip == other.ip

    def __ne__(self, other):
        return not self.__eq__(other)


class NetworkPath(object):
    """
    Represents a path in a network.
    """
    def __init__(self, host, path):
        """
        :param host: The machine the path is located at.
        :type host: NetworkHost instance
        :param path: The path locally on the network host.
        :type path: string
        """
        self.host = host
        self.path = path
