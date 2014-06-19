# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
The backupmanager module.
"""

import datetime
import logging
import os
import sys
import time
import dbus.service
import dbus.mainloop.glib
import gi.repository.GObject
import multiprocessing

from rbackupd import configmapper
from rbackupd import constants as const
from rbackupd import task
from rbackupd.cmd import rsync
from rbackupd.schedule import cron
from rbackupd.schedule import interval

logger = logging.getLogger(__name__)

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


class BackupManager(dbus.service.Object):
    """
    This class is responsible for exposing the rbackupd configuration file,
    starting all tasks specified in it and provide methods to modify these
    tasks while keeping them in sync with the configuraiton file.

    All important methods for controlling the backup manager are exported via
    D-Bus for client software to use.
    """

    def __init__(self, config_path):
        try:
            dbus.service.Object.__init__(
                self,
                bus_name=dbus.service.BusName(const.DBUS_BUS_NAME,
                                              dbus.SystemBus()),
                object_path=const.DBUS_OBJECT_PATH_BACKUP_MANAGER)
        except dbus.exceptions.DBusException:
            logger.critical("DBus connection failed: access denied.")
            sys.exit(const.EXIT_DBUS_ACCESS_DENIED)

        if not os.path.exists(config_path):
            logger.critical("Config file not found. Aborting.")
            sys.exit(const.EXIT_CONFIG_FILE_NOT_FOUND)
        self.configmapper = configmapper.ConfigMapper(config_path)

        self.tasks = None

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='s')
    def GetLogfilePath(self):
        """
        Return the path to the logfile.

        :rtype: str
        """
        return self.configmapper.logfile_path

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def SetLogfilePath(self, path):
        """
        Set the path to the logfile.

        :param path: the new path
        :type path: str
        """
        self.configmapper.logfile_path = path

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='s')
    def GetLoglevel(self):
        """
        Return the loglevel in human readble form.

        :rtype: str
        """
        return self.configmapper.loglevel

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def SetLoglevel(self, loglevel):
        """
        Set the loglevel in human readable form. Valid values are:
            * debug
            * verbose
            * default
            * quiet

        :param loglevel: the new loglevel
        :type loglevel: str
        """
        self.configmapper.loglevel = loglevel

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='s')
    def GetRsyncCommand(self):
        """
        Return the rsync command used.

        :rtype: str
        """
        return self.configmapper.rsync_command

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def SetRsyncCommand(self, command):
        """
        Set the rsync command that should be used.

        :param command: the new command
        :type command: str
        """
        self.configmapper.rsync_command = command

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='b')
    def GetDefaultRsyncLogfile(self):
        """
        Return a bool specifying whether a rsync logfile shall be used.

        :rtype: bool
        """
        return self.configmapper.default_rsync_logfile

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='b')
    def SetDefaultRsyncLogfile(self, value):
        """
        Set the flag specifying whether a rsync logfile shall be used.

        :param value: the new value
        :type value: bool
        """
        self.configmapper.default_rsync_logfile = value

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='s')
    def GetDefaultRsyncLogfileName(self):
        """
        Return the name of the rsync logfile.

        .. note::
            Make sure to see whether the log will be created to begin with
            through :func:`GetDefaultRsyncLogfile` and
            :func:`GetTaskRsyncLogfile`.

        :rtype: str
        """
        return self.configmapper.default_rsync_logfile

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def SetDefaultRsyncLogfileName(self, name):
        """
        Set the name of the rsync logfile.

        .. note::
            Make sure to see whether the log will be created to begin with
            through :func:`GetDefaultRsyncLogfile` and
            :func:`GetTaskRsyncLogfile`.

        :param name: the new name
        :type name: str
        """
        self.configmapper.default_rsync_logfile = name

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='s')
    def GetDefaultRsyncLogfileFormat(self):
        """
        Return the format used for the rsync logfile.

        .. note::
            See `rsync(1)` for details about possible formatting.

        :rtype: str
        """
        return self.configmapper.default_rsync_logfile_format

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def SetDefaultRsyncLogfileFormat(self, format):
        """
        Set the format used in the rsync logfile.

        .. note::
            See `rsync(1)` for details about possible formatting.

        .. warning::
            Setting this to an invalid value might render the rsync logfile
            useless.

        :param format: the new format
        :type format: str
        """
        self.configmapper.default_rsync_logfile_format = format

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='as')
    def GetDefaultFilters(self):
        """
        Return the default rsync filters. This is a list of strings that will
        be passed separately to the `--filter` option of `rsync(1)`

        :rtype: list of str
        """
        return self.configmapper.default_filters

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='as')
    def SetDefaultFilters(self, filters):
        """
        Set the default rsync filters.

        .. warning::
            Setting the filter to certain values might exclude all files from
            being backed up.

        :param filters: the new filters
        :type filters: list or str
        """
        self.configmapper.default_filters = filters

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='as')
    def GetDefaultIncludes(self):
        """
        Get the default patterns passed to `rsync(1)` via the `--inlcude`
        option.

        :rtype: list of str
        """
        return self.configmapper.default_includes

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='as')
    def SetDefaultIncludes(self, includes):
        """
        Set the default patterns passed to `rsync(1)` via the `--include`
        option.

        :param includes: the new include patterns
        :type includes: list of str
        """
        self.configmapper.default_includes = includes

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='as')
    def GetDefaultIncludeFiles(self):
        """
        Return a list all file paths passed to `rsync(1)` via the
        `--include-file` option.

        :rtype: list of str
        """
        return self.configmapper.default_include_files

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='as')
    def SetDefaultIncludeFiles(self, files):
        """
        Set the list of file paths passed to `rsync(1)` via the `--include-file`
        option.

        :param files: the new list of files
        :type files: list of str
        """
        self.configmapper.default_include_files = files

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='as')
    def GetDefaultExcludes(self):
        """
        Get the default patterns passed to `rsync(1)` via the `--exclude`
        option.

        :rtype: list of str
        """
        return self.configmapper.default_excludes

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='as')
    def SetDefaultExcludes(self, excludes):
        """
        Set the default patterns passed to `rsync(1)` via the `--exclude`
        option.

        :param excludes: the new exclude patterns
        :type excludes: list of str
        """
        self.configmapper.default_includes = excludes

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='as')
    def GetDefaultExcludeFiles(self):
        """
        Return a list all file paths passed to `rsync(1)` via the
        `--exclude-file` option.

        :rtype: list of str
        """
        return self.configmapper.default_exclude_files

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='as')
    def SetDefaultExcludeFiles(self, files):
        """
        Set the list of file paths passed to `rsync(1)` via the `--exclude-file`
        option.

        :param files: the new list of files
        :type files: list of str
        """
        self.configmapper.default_exclude_files = files

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='b')
    def GetDefaultCreateDestination(self):
        """
        Return the switch that specifies whether the destination directory shall
        be created if it does not exist.

        :rtype: bool
        """
        return self.configmapper.default_create_destination

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='b')
    def SetDefaultCreateDestination(self, value):
        """
        Set the switch that specifies whether the destination directory shall be
        created if it does not exist.

        :param value: the new value
        :type value: bool
        """
        self.configmapper.default_create_destination = value

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='b')
    def GetDefaultOneFilesystem(self):
        """
        Return the switch that specifies whether rsync should cross filesystem
        boundaries.

        :rtype: bool
        """
        return self.configmapper.default_one_filesystem

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='b')
    def SetDefaultOneFilesystem(self, value):
        """
        Set the switch that specifies whether rsync should cross filesystem
        boundaries.

        :param value: the new value
        :type value: bool
        """
        self.configmapper.default_one_filesystem = value

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='s')
    def GetDefaultSSHArgs(self):
        """
        Get the arguments that will be passed to ssh when creating remote
        backups.

        :rtype: str
        """
        return self.configmapper.default_ssh_args

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='b')
    def SetDefaultSSHArgs(self, args):
        """
        Set the arguments that will be passed to ssh when creating remote
        backups.

        :param args: the new arguments
        :type args: str
        """
        self.configmapper.default_ssh_args = args

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='as')
    def GetTaskSources(self, task):
        """
        Return a list of the path of all sources of the given task.

        :param task. the name of the task to work on
        :type task: str
        """
        return self.configmapper.task(task).sources

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sas')
    def SetTaskSources(self, task, sources):
        """
        Set the sources of the given task.

        :param task: the name of the task to work on
        :type task: str

        :param sources: the new sources
        :type sources: list of str
        """
        self.configmapper.task(task).sources = sources

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='s')
    def GetTaskDestination(self, task):
        """
        Return the path of the destination of the given task.

        :param task. the name of the task to work on
        :type task: str
        """
        return self.configmapper.task(task).destination

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='ss')
    def SetTaskDestination(self, task, destination):
        """
        Set the desination of the given task.

        :param task: the name of the task to work on
        :type task: str

        :param destination: the new destination
        :type destination: str
        """
        self.configmapper.task(task).destination = destination

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='b')
    def GetTaskRsyncLogfile(self, task):
        """
        Return a bool specifying whether a rsync logfile shall be used, or
        None if the task has no such value and you have to fall back on the
        default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: bool or None
        """
        return self.configmapper.task(task).rsync_logfile

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sb')
    def SetTaskRsyncLogfile(self, task, value):
        """
        Set the flag specifying whether a rsync logfile shall be used.

        :param task: the name of the task to work on
        :type task: str

        :param value: the new value
        :type value: bool
        """
        self.configmapper.task(task).rsync_logfile = value

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='s')
    def GetTaskRsyncLogfileName(self, task):
        """
        Return the name of the rsync logfile or None if the task has no such
        value and you have to fall back on the default values.

        .. note::
            Make sure to see whether the log will be created to begin with
            through :func:`GetTaskRsyncLogfile` and
            :func:`GetTaskRsyncLogfile`.d.

        :param task: the name of the task to work on
        :type task: str

        :rtype: str or None
        """
        return self.configmapper.task(task).rsync_logfile

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='ss')
    def SetTaskRsyncLogfileName(self, task, name):
        """
        Set the name of the rsync logfile.

        .. note::
            Make sure to see whether the log will be created to begin with
            through :func:`GetTaskRsyncLogfile` and :func:`GetTaskRsyncLogfile`.

        :param task: the name of the task to work on
        :type task: str

        :param name: the new name
        :type name: str
        """
        self.configmapper.task(task).rsync_logfile = name

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='s')
    def GetTaskRsyncLogfileFormat(self, task):
        """
        Return the format used for the rsync logfile or None if the task has no
        such value and you have to fall back on the default values.


        .. note::
            See `rsync(1)` for details about possible formatting.

        :param task: the name of the task to work on
        :type task: str

        :rtype: str or None
        """
        return self.configmapper.task(task).rsync_logfile_format

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='ss')
    def SetTaskRsyncLogfileFormat(self, task, format):
        """
        Set the format used in the rsync logfile.

        .. note::
            See `rsync(1)` for details about possible formatting.

        .. warning::
            Setting this to an invalid value might render the rsync logfile
            useless.

        :param task: the name of the task to work on
        :type task: str

        :param format: the new format
        :type format: str
        """
        self.configmapper.task(task).rsync_logfile = format

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='as')
    def GetTaskFilters(self, task):
        """
        Return the default rsync filters
        and you have to fall back on the default values. This is a list of
        strings that will be passed separately to the `--filter` option of
        `rsync(1)`

        :param task: the name of the task to work on
        :type task: str

        :rtype: list of str or None
        """
        return self.configmapper.task(task).filter_patterns

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sas')
    def SetTaskFilters(self, task, filters):
        """
        Set the default rsync filters.

        .. warning::
            Setting the filter to certain values might exclude all files from
            being backed up.

        :param task: the name of the task to work on
        :type task: str

        :param filters: the new filters
        :type filters: list or str
        """
        self.configmapper.task(task).filter_patterns = filters

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='as')
    def GetTaskIncludes(self, task):
        """
        Get the default patterns passed to `rsync(1)` via the `--inlcude`
        option  and you have to fall back
        on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: list of str or None
        """
        return self.configmapper.task(task).include_patterns

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sas')
    def SetTaskIncludes(self, task, includes):
        """
        Set the default patterns passed to `rsync(1)` via the `--include`
        option.

        :param task: the name of the task to work on
        :type task: str

        :param includes: the new include patterns
        :type includes: list of str
        """
        self.configmapper.task(task).include_patterns = includes

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='as')
    def GetTaskIncludeFiles(self, task):
        """
        Return a list all file paths passed to `rsync(1)` via the
        `--include-file` option  and you
        have to fall back on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: list of str or None
        """
        return self.configmapper.task(task).include_files

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sas')
    def SetTaskIncludeFiles(self, task, files):
        """
        Set the list of file paths passed to `rsync(1)` via the `--include-file`
        option.

        :param task: the name of the task to work on
        :type task: str

        :param files: the new list of files
        :type files: list of str
        """
        self.configmapper.task(task).include_files = files

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='as')
    def GetTaskExcludes(self, task):
        """
        Get the default patterns passed to `rsync(1)` via the `--exclude`
        option  and you have to fall back
        on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: list of str or None
        """
        return self.configmapper.task(task).exclude_patterns

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sas')
    def SetTaskExcludes(self, task, excludes):
        """
        Set the default patterns passed to `rsync(1)` via the `--exclude`
        option.

        :param task: the name of the task to work on
        :type task: str

        :param excludes: the new exclude patterns
        :type excludes: list of str
        """
        self.configmapper.task(task).exclude_patterns = excludes

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='as')
    def GetTaskExcludeFiles(self, task):
        """
        Return a list all file paths passed to `rsync(1)` via the
        `--exclude-file` option  and you
        have to fall back on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: list of str or None
        """
        return self.configmapper.task(task).exclude_files

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sas')
    def SetTaskExcludeFiles(self, task, files):
        """
        Set the list of file paths passed to `rsync(1)` via the `--exclude-file`
        option.

        :param task: the name of the task to work on
        :type task: str

        :param files: the new list of files
        :type files: list of str
        """
        self.configmapper.task(task).exclude_files = files

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='b')
    def GetTaskCreateDestination(self, task):
        """
        Return the switch that specifies whether the destination directory shall
        be created if it does not exist
        and you have to fall back on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: bool or None
        """
        return self.configmapper.task(task).create_destination

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sb')
    def SetTaskCreateDestination(self, task, value):
        """
        Set the switch that specifies whether the destination directory shall be
        created if it does not exist.

        :param task: the name of the task to work on
        :type task: str

        :param value: the new value
        :type value: bool
        """
        self.configmapper.task(task).create_destination = value

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='b')
    def GetTaskOneFilesystem(self, task):
        """
        Return the switch that specifies whether rsync should cross filesystem
        boundaries  and you have to fall
        back on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: bool or None
        """
        return self.configmapper.task(task).one_filesystem

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='sb')
    def SetTaskOneFilesystem(self, task, value):
        """
        Set the switch that specifies whether rsync should cross filesystem
        boundaries.

        :param task: the name of the task to work on
        :type task: str

        :param value: the new value
        :type value: bool
        """
        self.configmapper.task(task).one_filesystem = value

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='s')
    def GetTaskSSHArgs(self, task):
        """
        Get the arguments that will be passed to ssh when creating remote
        backups  and you have to fall back
        on the default values.

        :param task: the name of the task to work on
        :type task: str

        :rtype: str or None
        """
        return self.configmapper.task(task).ssh_args

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='ss')
    def SetTaskSSHArgs(self, task, args):
        """
        Set the arguments that will be passed to ssh when creating remote
        backups.

        :param task: the name of the task to work on
        :type task: str
        """
        self.configmapper.task(task).ssh_args = args

    @dbus.service.method(const.DBUS_BUS_NAME, out_signature='as')
    def GetTaskNames(self):
        """
        Return a list with the names of all tasks.

        :rtype: str
        """
        return [task.name for task in self.tasks]

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s',
                         out_signature='s')
    def GetTaskStatus(self, task):
        """
        Return the status of the specified task
        """
        return self._get_task_by_name(task).status.name

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def PauseTask(self, task):
        """
        Pause the spcified task.

        :param task: the name of the task to pause
        :type task: str
        """
        self._get_task_by_name(task).pause(block=True)

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def ResumeTask(self, task):
        """
        Resume the spcified task.

        :param task: the name of the task to resume
        :type task: str
        """
        self._get_task_by_name(task).resume()

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def StopTask(self, task):
        """
        Stop the spcified task.

        :param task: the name of the task to stop
        :type task: str
        """
        self._get_task_by_name(task).stop()

    @dbus.service.method(const.DBUS_BUS_NAME, in_signature='s')
    def StartTask(self, task):
        """
        Start the spcified task.

        :param task: the name of the task to start
        :type task: str
        """
        self._get_task_by_name(task).start()

    def _load_tasks(self, reload=False):
        """
        Parses the tasks section of the configuration file and creates
        corresponding objects. By default, it will not re-read the tasks
        if they were already read before.

        :param task: the name of the task to work on
        :type task: str

        :param reload: If set to True, the tasks will be re-read even though
            they were already read before. Defaults to False.
        :type reload: bool
        """
        if not reload and self.tasks is not None:
            return
        self.tasks = []
        for task_name in self.configmapper.task_names:
            self.tasks.append(self._get_task(task_name))

    def _expand_env_vars(self, path):
        return os.path.expanduser(os.path.expandvars(path))

    def _expand_env_vars_in_list(self, paths):
        return [self._expand_env_vars(path) for path in paths]

    def _get_task_by_name(self, name):
        for task in self.tasks:
            if task.name == name:
                return task
        raise ValueError("task not found")

    def _get_task(self, name):
        """
        Reads the task with the specified name from the configuration file and
        returns a Task object as a representation.

        :param name: The name of the task to load.
        :type name: string

        :rtype: Task object.
        """

        task_section = self.configmapper.task(name, fallback_on_default=True)

        # these are overrideable values
        rsync_logfile = task_section.rsync_logfile
        rsync_logfile_name = task_section.rsync_logfile_name
        rsync_logfile_format = task_section.rsync_logfile_format

        filter_patterns = task_section.filter_patterns
        include_patterns = task_section.include_patterns
        exclude_patterns = task_section.exclude_patterns
        include_files = self._expand_env_vars_in_list(
            task_section.include_files)
        exclude_files = self._expand_env_vars_in_list(
            task_section.exclude_files)

        create_destination = task_section.create_destination
        one_filesystem = task_section.one_filesystem
        rsync_args = task_section.rsync_args
        ssh_args = task_section.ssh_args

        # these values are unique for every task_section
        destination = self._expand_env_vars(task_section.destination)
        sources = self._expand_env_vars_in_list(task_section.sources)

        for pattern in filter_patterns + include_patterns + exclude_patterns:
            if len(pattern) == 0:
                logger.critical("Empty pattern found. Aborting.")
                sys.exit(const.EXIT_INVALID_CONFIG_VALUE)

        # now we can validate the values we got
        if not os.path.exists(destination):
            if not create_destination:
                logger.critical("Destination folder \"%s\" does not exist and "
                                "shall not be created. Aborting.", destination)
                sys.exit(const.EXIT_NO_CREATE_DESTINATION)
            else:
                os.mkdir(destination)
        else:
            if not os.path.isdir(destination):
                logger.critical("Destination \"%s\" exists, but is not a valid "
                                "directory.", destination)
                sys.exit(const.EXIT_INVALID_DESTINATION)

        for filter_file in include_files + exclude_files:
            if not os.path.exists(filter_file):
                logger.critical("File \"%s\" not found. Aborting.", filter_file)
                sys.exit(const.FILE_NOT_FOUND)
            if not os.path.isfile(filter_file):
                logger.critical("File \"%s\" is not a valid file. Aborting",
                                filter_file)
                sys.exit(const.FILE_INVALID)

        task_scheduling_info = task.TaskSchedulingInfo()
        # these are the subsection of the task that contain scheduling
        # information we need to preserve order of the entries of the
        # interval subsection
        interval_names = task_section.interval_names
        for interval_name in interval_names:
            cron_pattern = task_section.get_subsection(
                const.CONF_SECTION_INTERVALS)[interval_name]
            cron_pattern = cron.Cronjob(cron_pattern)

            # converting is necessary as this key cannot be specified as int
            # in the configspec
            keep_count = int(task_section.get_subsection(
                const.CONF_SECTION_KEEP)[interval_name])

            if keep_count <= 0:
                logger.critical("Maximum value of key \"%s\" in section \"%s\" "
                                "of task \"%s\" must be greater that zero.",
                                interval_name,
                                const.CONF_SECTION_KEEP,
                                name)

            keep_age = task_section.get_subsection(const.CONF_SECTION_AGE)[
                interval_name]
            keep_age = interval.Interval(keep_age)

            interval_info = task.IntervalInfo(name=interval_name,
                                              cron_pattern=cron_pattern,
                                              keep_count=keep_count,
                                              keep_age=keep_age)

            task_scheduling_info.append(interval_info)

        rsync_logfile_options = None
        if rsync_logfile:
            rsync_logfile_options = rsync.LogfileOptions(
                log_name=rsync_logfile_name,
                log_format=rsync_logfile_format)

        rsync_filter = rsync.Filter(
            filters=filter_patterns,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            include_files=include_files,
            exclude_files=exclude_files)

        return task.Task(
            name=name,
            sources=sources,
            destination=destination,
            scheduling_info=task_scheduling_info,
            one_filesystem=one_filesystem,
            ssh_args=ssh_args,
            rsync_cmd=self.configmapper.rsync_command,
            rsync_args=rsync_args,
            rsync_logfile_options=rsync_logfile_options,
            rsync_filter=rsync_filter)

    def _validate_values(self):
        rsync_cmd = self.configmapper.rsync_command
        if not os.path.isabs(rsync_cmd):
            logger.critical("The rsync command must be an absolute path.")
            sys.exit(const.EXIT_INVALID_CONFIG_VALUE)
        if not os.path.isfile(rsync_cmd) and os.access(rsync_cmd, os.X_OK):
            logger.critical("\"%s\" is no a valid executable")
            sys.exit(const.EXIT_INVALID_CONFIG_VALUE)

    def start(self):
        """
        Start the backup manager. This means reading and parsing the
        configuration file and starting the monitoring of the backups.
        """
        self.configmapper.read_config(reload=False)
        self._validate_values()
        self._load_tasks(reload=False)

        logfile_dir = os.path.dirname(self.configmapper.logfile_path)
        if not os.path.exists(logfile_dir):
            logger.debug("Folder containing log file does not exist, will be "
                         "created.")
            os.mkdir(logfile_dir)

        # now we can change from logging into memory to logging to the logfile
        logging.change_to_logfile_logging(
            logfile_path=self.configmapper.logfile_path,
            loglevel=self.configmapper.loglevel_as_int)

        minutely_event = multiprocessing.Event()

        for task in self.tasks:
            task.start()

        self._run_mainloop()

    def _run_mainloop(self):
        """
        Start the main loop and handle dbus requests.
        """
        logger.debug("Starting the main loop")
        loop = gi.repository.GObject.MainLoop()
        loop.run()
