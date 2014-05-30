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

    @dbus.service.method(const.DBUS_BUS_NAME)
    def get_logfile_path(self):
        """
        Return the path to the logfile.
        """
        return self.configmapper.logfile_path

    @dbus.service.method(const.DBUS_BUS_NAME)
    def set_logfile_path(self, path):
        """
        Set the path to the logfile.
        """
        self.configmapper.logfile_path = path

    def _load_tasks(self, reload=False):
        """
        Parses the tasks section of the configuration file and creates
        corresponding objects. By default, it will not re-read the tasks
        if they were already read before.

        :param reload: If set to True, the tasks will be re-read even though
        they were already read before. Defaults to False.
        :type reload: bool
        """
        if not reload and self.tasks is not None:
            return
        self.tasks = []
        for task_name in self.configmapper.task_names:
            self.tasks.append(self._get_task(task_name))

    def _get_task(self, name):
        """
        Reads the task with the specified name from the configuration file and
        returns a Task object as a representation.

        :param name: The name of the task to load.
        :type name: string

        :rtype: Task object.
        """

        task_section = self.configmapper.task(name)

        # these are overrideable values
        rsync_logfile = task_section.rsync_logfile
        rsync_logfile_name = task_section.rsync_logfile_name
        rsync_logfile_format = task_section.rsync_logfile_format

        filter_patterns = task_section.filter_patterns
        include_patterns = task_section.include_patterns
        include_files = task_section.include_files
        exclude_patterns = task_section.exclude_patterns
        exclude_files = task_section.exclude_files

        create_destination = task_section.create_destination
        one_filesystem = task_section.one_filesystem
        rsync_args = task_section.rsync_args
        ssh_args = task_section.ssh_args

        # these values are unique for every task_section
        destination = task_section.destination
        sources = task_section.sources

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
            create_destination=create_destination,
            one_filesystem=one_filesystem,
            ssh_args=ssh_args,
            rsync_cmd=self.configmapper.rsync_command,
            rsync_args=rsync_args,
            rsync_logfile_options=rsync_logfile_options,
            rsync_filter=rsync_filter)

    def start(self):
        """
        Start the backup manager. This means reading and parsing the
        configuration file and starting the monitoring of the backups.
        """
        self.configmapper.read_config(reload=False)
        self._load_tasks(reload=False)

        logfile_dir = os.path.dirname(self.get_logfile_path())
        if not os.path.exists(logfile_dir):
            logger.debug("Folder containing log file does not exist, will be "
                         "created.")
            os.mkdir(logfile_dir)

        # now we can change from logging into memory to logging to the logfile
        logging.change_to_logfile_logging(
            logfile_path=self.get_logfile_path(),
            loglevel=self.configmapper.loglevel_as_int)

        minutely_event = multiprocessing.Event()

        for task in self.tasks:
            process = multiprocessing.Process(target=self._start_monitor,
                                              args=(task, minutely_event))
            process.start()
        minutely_process = multiprocessing.Process(
            target=self._raise_event_minutely,
            args=(minutely_event,))
        minutely_process.start()

        self._run_mainloop()

    def _run_mainloop(self):
        """
        Start the main loop and handle dbus requests.
        """
        logger.debug("Starting the main loop")
        loop = gi.repository.GObject.MainLoop()
        loop.run()

    def _start_monitor(self, task, on_event):
        """
        Periodically check a task for new or expired backups. Checks are
        triggerred by an event. When started, a check will be started before
        waiting for the event.

        :param task: The task to monitor.
        :type task: Task instance

        :param on_event: The event that triggers a check of the task.
        :type on_event: multiprocessing.Event instance
        """
        logger.debug("start a thread for task %s", task.name)
        while True:
            start = datetime.datetime.now()
            logger.debug("checking task %s at %s", task.name, start)
            task.create_backups_if_necessary(timestamp=start)
            task.handle_expired_backups(timestamp=start)
            on_event.wait()

    def _raise_event_minutely(self, event):
        """
        Raise an event at the beginning of every minute.

        :param event: The event to raise.
        :type event: multiprocessing.Event instance
        """
        logger.debug("starting minutely event raiser process")
        while True:
            event.clear()
            wait_seconds = 60 - datetime.datetime.now().second
            logger.debug("Sleeping %s seconds until next cycle.", wait_seconds)
            time.sleep(wait_seconds)
            event.set()
