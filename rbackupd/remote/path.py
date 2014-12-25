# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>


import os.path

class Path(object):
    """
    Represents a path on a specific host.
    """

    def __init__(self, path, connection_parameters=None):
        self.path = path
        self.connection_parameters = connection_parameters


def join(path1, path2):
    """
    :type path1: Path instance
    :type path2: str
    """
    path1.path = os.path.join(path1.path, path2)
    return path1
