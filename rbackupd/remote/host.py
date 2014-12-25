# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

class Host(object):
    """
    Represents a host in a network.
    """

    def __init__(self, ip):
        self.ip = ip

    def is_localhost(self):
        return self.ip.startswith("127.")

def get_localhost():
    return Host(ip="127.0.0.1")
