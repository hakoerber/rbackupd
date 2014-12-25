# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
This module wraps frequently needed operations on files and directories. It works
host-agnostic, if a command is not executed locally, a SSH connection is started
to execute the command on the remote host. To reduce overhead, used SSH
connections will be kept open and reused when the same parameters (host, user,
port) are used.
"""

import logging
import os
import subprocess
import rbackupd.remote.ssh as ssh
import rbackupd.remote.path as rpath

logger = logging.getLogger(__name__)

def _exec(args, connection_parameters):
    if (connection_parameters is None or
            connection_parameters.host.is_localhost()):
        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        (output, _) = proc.communicate()
        retval = proc.returncode
    else:
        connection = _get_connection(connection_parameters)
        (retval, output) = connection.execute(args)
    return (retval, output)

def _new_connection(connection_parameters):
    connection = ssh.Connection(connection_parameters)
    connection.connect()

    _connection_cache[connection_parameters] = connection
    return connection

_connection_cache = {}
def _get_connection(connection_parameters):
    if connection_parameters in _connection_cache:
        return _connection_cache[connection_parameters]
    else:
        return _new_connection(connection_parameters)

def _check_path(path):
    if isinstance(path, str):
        fixed_path = rpath.Path(path=path)
    else:
        fixed_path = path
    return fixed_path


def exists(path):
    path = _check_path(path)
    (retval, output) = _exec(
        args=["test", "-e", path.path],
        connection_parameters=path.connection_parameters)
    return retval == 0


def remove_recursive(path):
    """
    Removes a file or directory. If the target is a directory, it will be
    deleted recursively.

    :param path: The path to delete.
    :type path: Path instance or str

    :returns: True if the removal succeeded, False otherwise.
    :rtype: bool
    """
    path = _check_path(path)
    if not exists(path):
        raise ValueError("%s does not exist" % path.path)
    args = ["rm", "-r", "-f", path]
    (retval, output) = _exec(
        args=["rm", "-r", "-f", path.path],
        connection_parameters=path.connection_parameters)
    return retval == 0

def listdir(path):
    """
    Lists all files and directories in the given directory. Only the names
    are returned.

    Note: If path is a symlink, it will be expanded.

    :param path: The path to the directory.
    :type path: Path instance or str

    :returns: All files and directories in the directory.
    :rtype: list of str

    :raises ValueError: if path is not a directory.
    """
    path = _check_path(path)
    if not is_directory(path):
        raise ValueError("%s is no a directory" % path.path)
    args = ['find', '-H',
            path.path,
            '-maxdepth', '1',
            '-mindepth', '1',
            # yeah, four backslahes
            '-printf', '%f\\\\0']
    (retval, output) = _exec(
        args=args,
        connection_parameters=path.connection_parameters)

    # last element of the result is empty because the string ends with a null
    # byte.
    return output.split('\0')[:-1]


def is_directory(path):
    """
    Determines whether the given path is a directory.

    :param path: The path to test.
    :type path: Path instance or str

    :returns: True if path is a directory, False otherwise.
    :rtype: bool
    """
    path = _check_path(path)
    args = ["test", "-d", path.path]
    (retval, output) = _exec(
        args=args,
        connection_parameters=path.connection_parameters)
    return retval == 0


def is_symlink(path):
    """
    Determines whether the given path is a symlink. Note that the validity of
    the symlink is not checked, only if it is a link at all.

    :param path: The path to test.
    :type path: Path instance or str

    :returns: True if path is a symlink, False otherwise.
    :rtype: bool
    """
    path = _check_path(path)
    args = ["test", "-L", path.path]
    (retval, output) = _exec(
        args=args,
        connection_parameters=path.connection_parameters)
    return retval == 0


def remove_symlink(path):
    """
    Removes a symlink.

    :param path: The path of the symlink.
    :type path: Path instance or str

    :returns: True if removal succeeded, False otherwise.
    :rtype: bool
    """
    # to remove a symlink, we have to strip the trailing
    # slash from the path
    path = _check_path(path)
    if not is_symlink(path):
        raise ValueError("%s is not a symlink" % path)
    args = ["rm", path.rstrip("/")]
    (retval, output) = _exec(
        args=args,
        connection_parameters=path.connection_parameters)
    return retval == 0


def samefile(file1, file2):
    """
    Determines whether the two files are the same by comparing their inodes.

    :param file1: The first file to compare.
    :type file1: Path instance or str.

    :param file2: The second file to compare.
    :type file2: str.

    :returns: True if both files have the same inode, False otherwise.
    :rtype: bool

    :raises ValueError: if either file does not exist.
    """
    if not exists(file1):
        raise ValueError("File %s does not exist." % file1.path)
    if not exists(rpath.Path(
            path=file2,
            connection_parameters=file1.connection_parameters)):
        raise ValueError("File %s does not exist." % file1)


    args = ["stat", "-c", "%i"]
    (retval, output) = _exec(
        args=args + [file1.path],
        connection_parameters=file1.connection_parameters)
    inode1 = output
    (retval, output) = _exec(
        args=args + [file2],
        connection_parameters=file1.connection_parameters)
    inode2 = output
    return inode1 == inode2



def create_symlink(target, linkname):
    """
    Creates a symlink at <linkname> that points to <target>. Note that the
    second parameter must be a simple string without host information and is
    interpreted as a path on the host of the first argument.

    :param target: The target the symlink points to.
    :type target: Path instance or str

    :param linkname: The path of the symlink.
    :type linkname: str

    :returns: True if the creation succeeded, False otherwise.
    :rtype: bool

    :raises ValueError: if target does not exist.
    :raises ValueError: if linkname already exists.
    """
    target = _check_path(target)
    if not exists(target):
        raise ValueError("%s does not exist" % target.path)
    if exists(linkname):
        raise ValueError("%s already exists" % linkname)
    args = ["ln", "-s", "-r", target.path, linkname]
    (retval, output) = _exec(
        args=args,
        connection_parameters=target.connection_parameters)
    return retval == 0


def move(path, target):
    """
    Moves a file or directory.

    :param path: The path to the file/directory to move.
    :type path: Path instance or str

    :param target: The path to move to.
    :type target: str

    :returns: True if the operation succeeded, False otherwise.
    :rtype: bool
    """
    path = _check_path(path)
    if not exists(path):
        raise ValueError("%s does not exist" % path.path)
    if exists(target):
        raise ValueError("%s does already exist" % target)
    args = ["mv", path, target]
    (retval, output) = _exec(
        args=args,
        connection_parameters=path.connection_parameters)
    return retval == 0

def mkdir(path, parent_directories=False):
    """
    Creates a directory.

    :param path: The path to the directory to create.
    :type path: Path instance or str


    :param parent_directories: If true, non-existent parent directories will be
    created.
    :type parent_directories: bool

    :returns: True if the operation succeeded. False otherwise.
    :rtype: bool

    :raises ValueError: if path already exists.
    """
    path = _check_path(path)
    if exists(path):
        raise ValueError("path already exists")
    args = ["mkdir"]
    if parent_directories:
        args.append("--parents")
    (retval, output) = _exec(
        args=args,
        connection_parameters=path.connection_parameters)
    return retval == 0
