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

import datetime
import logging
import os
import sys
import time
import dbus.service
import dbus.mainloop.glib
import gi.repository.GObject
import multiprocessing


from rbackupd import task
from rbackupd import rsync
from rbackupd import constants as const
from rbackupd import configmanager
from rbackupd import interval

LOGLEVEL_MAPPING = {
    "quiet"   : logging.WARNING,
    "default" : logging.INFO,
    "verbose" : logging.VERBOSE,
    "debug"   : logging.DEBUG }

LOGLEVEL_VALUES = list(LOGLEVEL_MAPPING.keys())

LOGLEVEL_MAPPING_REVERSE = {v: k for k, v in LOGLEVEL_MAPPING.items()}

LOGLEVEL_VALUES_REVERSE = list(LOGLEVEL_MAPPING_REVERSE.keys())


logger = logging.getLogger(__name__)

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class BackupManager(dbus.service.Object):

    def __init__(self, config_path):
        dbus.service.Object.__init__(
            self,
            bus_name=dbus.service.BusName(const.BUS_NAME, dbus.SystemBus()),
            object_path=const.BUS_PATH)

        if not os.path.exists(config_path):
            logger.critical("Config file not found. Aborting.")
            sys.exit(const.EXIT_CONFIG_FILE_NOT_FOUND)

        self.config_path = config_path
        self.tasks = None

    def read_config(self):
        logger.debug("Starting configuration file parsing.")
        try:
            self.configmanager = configmanager.ConfigManager(
                path=self.config_path, configspec=const.DEFAULT_SCHEME_PATH)

        except configmanager.ConfigError as err:
            logger.critical("Invalid config file: error line %s (\"%s\"): %s",
                            err.line_number,
                            err.line,
                            err.msg)
            raise
            exit(const.EXIT_CONFIG_FILE_INVALID)
        logger.debug("Config file parsed successfully.")





    @dbus.service.method(const.BUS_NAME)
    def write_config(self):
        """
        Write the configuration file to disk.
        """
        self.configmanager.write()

    @dbus.service.method(const.BUS_NAME)
    def reload_config(self):
        """
        Reload the configuration file from the path given at startup.
        """
        self.configmanager.reload()

    @dbus.service.method(const.BUS_NAME)
    def get_config(self):
        """
        Return a dict containing the outline of the configuration file.
        """
        return dict(self.configmanager)

    @dbus.service.method(const.BUS_NAME)
    def get_logfile_path(self):
        """
        Return the path to the logfile.
        """
        logger.debug("get_logfile_path")
        return self.configmanager.get(
            const.CONF_SECTION_LOGGING).get(
            const.CONF_KEY_LOGFILE_PATH)

    @dbus.service.method(const.BUS_NAME)
    def set_logfile_path(self, path):
        """
        Set the path to the logfile.
        """
        logger.debug("set_logfile_path %s" % path)
        self.configmanager[const.CONF_SECTION_LOGGING][const.CONF_KEY_LOGFILE_PATH] = path
        self.write_config()

    @dbus.service.method(const.BUS_NAME)
    def get_loglevel_human_readable(self):
        """
        Return the loglevel in human readable format like in the configuration file.
        """
        level = self.configmanager[const.CONF_SECTION_LOGGING][const.CONF_KEY_LOGLEVEL]
        if level not in LOGLEVEL_VALUES:
            logger.critical("Invalid value \"%s\" for %s. Valid values: %s. "
                            "Aborting.",
                            level,
                            const.CONF_KEY_LOGLEVEL,
                            ",".join([str(v) for v in LOGLEVEL_VALUES]))
            sys.exit(const.EXIT_INVALID_CONFIG_FILE)
        return level


    @dbus.service.method(const.BUS_NAME)
    def get_loglevel(self):
        """
        Return the loglevel as used by the logging module.
        """
        level = self.get_loglevel_human_readable()
        return LOGLEVEL_MAPPING[level]

    @dbus.service.method(const.BUS_NAME)
    def set_loglevel_human_readable(self, loglevel):
        """
        Set the loglevel in human readable format like in the configuration file.
        """
        if loglevel not in LOGLEVEL_VALUES:
            logger.critical("Cannot set loglevel to invalid value \"%s\"", loglevel)
            sys.exit(const.EXIT_ERROR_GENERAL)

        logging.change_file_logging_level(loglevel)

        self.configmanager[const.CONF_SECTION_LOGGING][const.CONF_KEY_LOGLEVEL] = \
            LOGLEVEL_MAPPING_REVERSE[loglevel]
        self.write_config()

    @dbus.service.method(const.BUS_NAME)
    def set_loglevel(self, loglevel):
        """
        Set the loglevel as used by the logging module.
        """
        if loglevel not in LOGLEVEL_VALUES_REVERSE:
            logger.critical("Cannot set loglevel to invalid value \"%s\"", loglevel)
            sys.exit(const.EXIT_ERROR_GENERAL)
        self.set_loglevel(LOGLEVEL_MAPPING_REVERSE[loglevel])

    @dbus.service.method(const.BUS_NAME)
    def get_rsync_command(self):
        """
        Return the rsync command.
        """
        return self.configmanager[const.CONF_SECTION_RSYNC][const.CONF_KEY_RSYNC_CMD]

    @dbus.service.method(const.BUS_NAME)
    def set_rsync_command(self, command):
        """
        Set the rsync command.
        """
        self.configmanager[const.CONF_SECTION_RSYNC][const.CONF_KEY_RSYNC_CMD] = command
        self.write_config()

    @dbus.service.method(const.BUS_NAME)
    def get_task_default(self, key):
        """
        Get the default value "key" for all tasks.
        """
        return self[const.CONF_SECTION_TASKS][key]

    @dbus.service.method(const.BUS_NAME)
    def set_task_default(self, key, value):
        """
        Set the default value "key" for all tasks.
        """
        self[const.CONF_SECTION_TASKS][key] = value
        self._load_tasks(reload=False)

    @dbus.service.method(const.BUS_NAME)
    def get_task_option(self, task, option):
        """
        Get the option for a task.
        """
        return self[const.CONF_SECTION_TASKS][task][option]

    @dbus.service.method(const.BUS_NAME)
    def set_task_option(self, task, option, value):
        """
        Set the option for a task.
        """
        self[const.CONF_SECTION_TASKS][task][option] = value

    @dbus.service.method(const.BUS_NAME)
    def get_task_names(self):
        """
        Get all task names.
        """
        self._load_tasks(reload=False)
        return self.configmanager[const.CONF_SECTION_TASKS].section

    @dbus.service.method(const.BUS_NAME)
    def get_task(self, name):
        """
        Get the task with the given name.
        """
        self._load_tasks(reload=False)
        return self.tasks[name]

    @dbus.service.method(const.BUS_NAME)
    def rename_task(self, oldname, newname):
        """
        Rename the task with name "oldname" to "newname"
        """
        task_section = self.configmanager[const.CONF_SECTION_TASKS]
        task_section.rename(oldname, newname)
        self._load_tasks(reload=True)


    def _load_tasks(self, reload=False):
        if not reload and self.tasks is not None:
            return
        self.tasks = []
        tasks_section = self.configmanager[const.CONF_SECTION_TASKS]
        for task_section in tasks_section.sections:
            self.tasks.append(self._get_task(task_section))

    def _get_task(self, name):
        task_section = self.configmanager[const.CONF_SECTION_TASKS][name]

        def _get(key):
            return self._get_from_task(name, key)

        # these are overrideable values
        rsync_logfile =        _get(const.CONF_KEY_RSYNC_LOGFILE)
        rsync_logfile_name =   _get(const.CONF_KEY_RSYNC_LOGFILE_NAME)
        rsync_logfile_format = _get(const.CONF_KEY_RSYNC_LOGFILE_FORMAT)

        filter_patterns =      _get(const.CONF_KEY_FILTER_PATTERNS)
        include_patterns =     _get(const.CONF_KEY_INCLUDE_PATTERNS)
        include_files =        _get(const.CONF_KEY_INCLUDE_FILE)
        exclude_patterns =     _get(const.CONF_KEY_EXCLUDE_PATTERNS)
        exclude_files =        _get(const.CONF_KEY_EXCLUDE_FILE)

        create_destination =   _get(const.CONF_KEY_CREATE_DESTINATION)
        one_filesystem =       _get(const.CONF_KEY_ONE_FILESYSTEM)
        rsync_args =           _get(const.CONF_KEY_RSYNC_ARGS)
        ssh_args =             _get(const.CONF_KEY_SSH_ARGS)

        # these values are unique for every task
        destination =          task_section[const.CONF_KEY_DESTINATION]
        sources =              task_section[const.CONF_KEY_SOURCE]


        backup_scheduling_info = task.BackupSchedulingInfo()
        # these are the subsection of the task that contain scheduling information
        # we need to preserve order of the entries of the interval subsection
        interval_names = task_section[const.CONF_SECTION_INTERVALS].keys()
        for interval_name in interval_names:
            cron_pattern = task_section[const.CONF_SECTION_INTERVALS][interval_name]

            # converting is necessary as this key cannot be specified as int
            # in the configspec
            keep_count = int(task_section[const.CONF_SECTION_KEEP][interval_name])

            keep_age = task_section[const.CONF_SECTION_AGE][interval_name]
            keep_age = interval.Interval(keep_age)

            interval_info = task.IntervalInfo(name=interval_name,
                                              cron_pattern=cron_pattern,
                                              keep_count=keep_count,
                                              keep_age=keep_age)

            backup_scheduling_info.append(interval_info)




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
            scheduling_info=backup_scheduling_info,
            create_destination=create_destination,
            one_filesystem=one_filesystem,
            ssh_args=ssh_args,
            rsync_cmd=self.get_rsync_command(),
            rsync_args=rsync_args,
            rsync_logfile_options=rsync_logfile_options,
            rsync_filter=rsync_filter)

    def _get_from_task(self, name, key):
        task_section = self.configmanager[const.CONF_SECTION_TASKS][name]
        default_section = self.configmanager[const.CONF_SECTION_TASKS]
        if key in task_section:
            value = task_section[key]
        else:
            value = default_section[key]
        # this is a bit ugly but necessary. if there is not value specified for a list
        # in the configuration file (like this: "include ="), instead of returning an
        # empty list configobj returns [''], which we have to convert into an empty list
        # manually
        if isinstance(value, list) and len(value) == 1 and len(value[0]) == 0:
            value = []
        return value





    def start(self):
        self.read_config()
        self._load_tasks()

        logfile_dir = os.path.dirname(self.get_logfile_path())
        if not os.path.exists(logfile_dir):
            logger.debug("Folder containing log file does not exist, will be "
                         "created.")
            os.mkdir(logfile_dir)


        # now we can change from logging into memory to logging to the logfile
        logging.change_to_logfile_logging(logfile_path=self.get_logfile_path(),
                                          loglevel=self.get_loglevel())

        minutely_event = multiprocessing.Event()

        for task in self.tasks:
            process = multiprocessing.Process(target=self.monitor,
                                              args=(task, minutely_event))
            process.start()
        minutely_process = multiprocessing.Process(
            target=self.raise_event_minutely,
            args=(minutely_event,))
        minutely_process.start()


        self.run()

    def run(self):
        """
        Start the main loop and handle dbus requests.
        """
        logger.debug("Starting the main loop")
        loop = gi.repository.GObject.MainLoop()
        loop.run()


    def monitor(self, task, minutely_event):
        """
        Periodically check a task for new or expired backups.
        """
        logger.debug("start a thread for task %s", task.name)
        while True:
            start = datetime.datetime.now()
            logger.debug("checking task %s at %s", task.name, start)
            for task in self.tasks:
                task.create_backups_if_necessary(timestamp=start)
                task.handle_expired_backups(timestamp=start)
            minutely_event.wait()



    def raise_event_minutely(self, event):
        """
        Raise the event "event" at the beginning of every minute.
        """
        logger.debug("starting minutely event raiser process")
        while True:
            event.clear()
            now = datetime.datetime.now()
            if now.minute == 59:
                wait_seconds = 60 - now.second
            else:
                nextmin = now.replace(minute=now.minute+1,
                                      second=0,
                                      microsecond=0)
                wait_seconds = (nextmin - now).seconds + 1
            logger.debug("Sleeping %s seconds until next cycle.", wait_seconds)

            time.sleep(wait_seconds)
            event.set()






#
#             # these are the options that are not given in the [default]
#             # section.
#             conf_destination = task[const.CONF_KEY_DESTINATION][0]
#             conf_sources = task[const.CONF_KEY_SOURCE]
#
#             # now we can check the values
#             if not os.path.exists(conf_destination):
#                 if not conf_create_destination:
#                     logger.error("Destination \"%s\" does not exists, will no "
#                                  "be created. Archive will be skipped.",
#                                  conf_destination)
#                     continue
#             if not os.path.isdir(conf_destination):
#                 logger.critical("Destination \"%s\" not a directory. "
#                                 "Aborting.", conf_destination)
#                 sys.exit(const.EXIT_INVALID_DESTINATION)
#
#             if conf_include_files is not None:
#                 for include_file in conf_include_files:
#                     if include_file is None:
#                         continue
#                     if not os.path.exists(include_file):
#                         logger.critical("Include file \"%s\" not found. "
#                                         "Aborting.", include_file)
#                         sys.exit(const.EXIT_INCLUDE_FILE_NOT_FOUND)
#                     elif not os.path.isfile(include_file):
#                         logger.critical("Include file \"%s\" is not a file. "
#                                         "Aborting.", include_file)
#                         sys.exit(const.EXIT_INCLUDE_FILE_INVALID)
#
#             if conf_exclude_files is not None:
#                 for exclude_file in conf_exclude_files:
#                     if exclude_file is None:
#                         continue
#                     if not os.path.exists(exclude_file):
#                         logger.critical("Exclude file \"%s\" not found. "
#                                         "Aborting.", exclude_file)
#                         sys.exit(const.EXIT_EXCULDE_FILE_NOT_FOUND)
#                     elif not os.path.isfile(exclude_file):
#                         logger.critical("Exclude file \"%s\" is not a file. "
#                                         "Aborting.", exclude_file)
#                         sys.exit(const.EXIT_EXCLUDE_FILE_INVALID)
#
#             if conf_rsync_logfile:
#                 conf_rsync_logfile_options = rsync.LogfileOptions(
#                     conf_rsync_logfile_name, conf_rsync_logfile_format)
#             else:
#                 conf_rsync_logfile_options = None
#
#             conf_rsyncfilter = rsync.Filter(conf_include_patterns,
#                                             conf_exclude_patterns,
#                                             conf_include_files,
#                                             conf_exclude_files,
#                                             conf_filter_patterns)
#
#             rsync_args = []
#             for arg in conf_rsync_args:
#                 rsync_args.extend(arg.split())
#             conf_rsync_args = rsync_args
#
#             if conf_one_filesystem:
#                 conf_rsync_args.append("-x")
#
#             ssh_args = []
#             if conf_ssh_args is not None:
#                 ssh_args = ["--rsh", conf_ssh_args]
#             conf_rsync_args.extend(ssh_args)
#
#             conf_taskname = task[const.CONF_KEY_TASKNAME][0]
#             conf_task_intervals = task[const.CONF_KEY_INTERVAL]
#             conf_task_keeps = task[const.CONF_KEY_KEEP]
#             conf_task_keep_age = task[const.CONF_KEY_KEEP_AGE]
#
#             for (interval_name, keep_count) in conf_task_keeps.items():
#                 if keep_count <= 0:
#                     logger.critical("Maximum backup count must be greater "
#                                     "than zero, %s found for interval \"%s\".",
#                                     keep_count,
#                                     interval_name)
#                     sys.exit(const.EXIT_INVALID_CONFIG_FILE)
#
#             task_keep_age = collections.OrderedDict()
#             for (backup_interval, max_age) in conf_task_keep_age.items():
#                 task_keep_age[backup_interval] = \
#                     interval.interval_to_oldest_datetime(max_age)
#
#             self.archives.append(
#                     archive.Archive(conf_sources,
#                                     conf_destination,
#                                     conf_taskname,
#                                     conf_task_intervals,
#                                     conf_task_keeps,
#                                     task_keep_age,
#                                     conf_rsyncfilter,
#                                     conf_rsync_logfile_options,
#                                     conf_rsync_args,
#                                     self.conf_rsync_cmd))



