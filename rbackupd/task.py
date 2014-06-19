# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
The task module.
"""

import datetime
import enum
import logging
import multiprocessing
import os
import sys
import time

from rbackupd import backupstorage
from rbackupd import constants as const
from rbackupd.cmd import files
from rbackupd.cmd import rsync

logger = logging.getLogger(__name__)


class Task(object):
    """
    Represents a task of backups, which means a collection of backups
    that are managed together. Provides methods to determine whether new
    backups are necessary and get expired backups.
    """

    def __init__(self,
                 name,
                 sources,
                 destination,
                 scheduling_info,
                 one_filesystem,
                 ssh_args,
                 rsync_cmd,
                 rsync_args,
                 rsync_logfile_options,
                 rsync_filter):
        self.name = name
        self.sources = sources
        self.destination = destination
        self.scheduling_info = scheduling_info
        self.one_filesystem = one_filesystem
        self.ssh_args = ssh_args

        self.rsync_cmd = rsync_cmd
        self.rsync_args = rsync_args
        self.rsync_logfile_options = rsync_logfile_options
        self.rsync_filter = rsync_filter

        self._backups = self._read_backups()

        self._status = TaskStatus.stopped

        self._pausing_event = multiprocessing.Event()
        self._event_exit = multiprocessing.Event()
        self._paused_event = multiprocessing.Event()

    def _is_latest_symlink(self, folder):
        return folder == const.SYMLINK_LATEST_NAME

    @property
    def backups(self):
        assert(self._backups is not None)
        return self._backups

    def _read_backups(self):
        """
        Parse the backups that already exist at the destination into objects and
        return them in a list.

        :rtype: list of Backup instances
        """
        logger.debug("Task \"%s\": Reading backups.", self.name)
        backups = []
        for folder in os.listdir(self.destination):
            if self._is_latest_symlink(folder):
                logger.debug("Task \"%s\": Ignoring latest symlink "
                             "\"%s\".", self.name, folder)
                continue

            backup = backupstorage.BackupFolder(
                os.path.join(self.destination, folder))

            if not backup.is_finished():
                logger.warning("Backup \"%s\" is not recognized as a valid "
                               "backup, will be skipped.",
                               backup.folder)
                continue

            try:
                backup.load_metadata()
            except backupstorage.InvalidBackupError as error:
                logger.critical(
                    "Backup at \"%s\" is invalid, the metadata could not be "
                    "read: \"%s\"",
                    error.path,
                    error.message)
                sys.exit(const.EXIT_ERROR_GENERAL)

            backups.append(backup)
        logger.debug("Task \"%s\": Found the following folders: %s.",
                     self.name,
                     ",".join([backup.path for backup in backups]))

        return backups

    def _register_backup(self, backup):
        """
        Add a new backup to the already existing backups.

        :param backup: The backup to register.
        :type backup: Backup instance
        """
        assert(self._backups is not None)
        logger.debug("Task \"%s\": Registering backup \"%s\".",
                     self.name, backup.name)
        self._backups.append(backup)

    def _unregister_backup(self, backup):
        """
        Removes a backup from the backups known to this task.

        :param backup: The backup to unregister.
        :type backup: Backup instance
        """
        assert(self._backups is not None)
        if backup not in self._backups:
            raise ValueError("backup not found")
        logger.debug("Task \"%s\": Unregistering backup \"%s\".",
                     self.name, backup.name)
        self._backups.remove(backup)

    def _get_necessary_interval_infos(self):
        """
        Return all intervals that require a new backup.

        :rtype: list of IntervalInfos instances
        """
        necessary_backups = []
        for interval_info in self.scheduling_info.interval_infos:
            logger.debug("Task \"%s\": Checking interval \"%s\" for "
                         "necessary backups.",
                         self.name,
                         interval_info.name)
            latest_backup = self._get_latest_backup_of_interval(interval_info)
            if latest_backup is None:
                logger.debug("Task \"%s\": Backup necessary as no other "
                             "backups of that interval are present.",
                             self.name)
                necessary_backups.append(interval_info)
                continue
            if interval_info.cronjob.has_occured_since(latest_backup.date,
                                                       include_start=False):
                logger.debug("Task \"%s\": Backup necessary as interval "
                             "occurred since latest backup.",
                             self.name)
                necessary_backups.append(interval_info)
        return necessary_backups

    def create_backups_if_necessary(self, timestamp):
        """
        Check whether a backups are necessary and create them.

        :param timestamp: The timestamp all potentially created backups will be
                          assigned.
        :type timestamp: datetime.datetime instance
        """
        necessary_interval_infos = self._get_necessary_interval_infos()
        if len(necessary_interval_infos) == 0:
            logger.verbose("No backup necessary.")
            return

        interval_info = necessary_interval_infos[0]

        new_folder_name = self._get_folder_name(
            name=self.name,
            date=timestamp.strftime(const.DATE_FORMAT),
            interval_name=interval_info.name)

        new_backup = backupstorage.BackupFolder(os.path.join(
            self.destination, new_folder_name))

        params = self.get_backup_params()
        new_backup.set_metadata(name=new_folder_name,
                                date=timestamp,
                                interval_name=interval_info.name)
        new_backup.prepare()
        self.create_backup(new_backup, params)
        new_backup.finish()
        self._register_backup(new_backup)

        # all other necessary backups will just be symlinked to the one just
        # created
        for interval_info in necessary_interval_infos[1:]:
            self._create_symlink_backup(timestamp=timestamp,
                                        target=new_backup,
                                        interval_info=interval_info)

    def _create_symlink_backup(self, timestamp, target, interval_info):
            symlink_name = self._get_folder_name(
                name=self.name,
                date=timestamp.strftime(const.DATE_FORMAT),
                interval_name=interval_info.name)
            symlink_backup = backupstorage.BackupFolder(os.path.join(
                self.destination, symlink_name))
            symlink_backup.set_metadata(name=symlink_name,
                                        date=timestamp,
                                        interval_name=interval_info.name)
            symlink_backup.prepare()
            symlink_backup.link_data_from(target)
            symlink_backup.finish()
            self._register_backup(symlink_backup)

    def _get_folder_name(self, name, date, interval_name):
        return const.PATTERN_BACKUP_FOLDER.format(
            name=name,
            date=date,
            interval_name=interval_name)

    def get_backup_params(self):
        """
        Gets the parameters for a backup.

        :returns: Information about the new backup.
        :rtype: BackupParameters instance
        """
        logger.debug("Task \"%s\": Getting parameters of new backup.",
                     self.name)
        new_link_ref = self._get_latest_backup()
        if new_link_ref is not None:
            logger.debug("Link-ref of new backup: \"%s\"",
                         new_link_ref.data_path)
        else:
            logger.debug("No link ref as no old backup found.")
        backup_params = BackupParameters(
            link_ref=new_link_ref,
            rsync_cmd=self.rsync_cmd,
            rsync_args=self.rsync_args,
            rsync_filter=self.rsync_filter,
            rsync_logfile_options=self.rsync_logfile_options)
        return backup_params

    def create_backup(self, new_backup, params):
        destination = new_backup.data_path
        if params.link_ref is None:
            link_dest = None
        else:
            link_dest = params.link_ref.data_path
        logger.info("Creating backup \"%s\".", new_backup.name)
        (returncode, stdoutdata, stderrdata) = rsync.rsync(
            command=params.rsync_cmd,
            sources=self.sources,
            destination=destination,
            link_ref=link_dest,
            arguments=params.rsync_args,
            rsyncfilter=params.rsync_filter,
            loggingOptions=params.rsync_logfile_options)
        if returncode != 0:
            logger.critical("Rsync failed. Aborting. Stderr:\n%s",
                            stderrdata)
            sys.exit(const.EXIT_RSYNC_FAILED)
        else:
            logger.debug("Rsync finished successfully.")
        logger.info("Backup finished successfully.")
        self._relink_latest_symlink(new_backup)

    def get_expired_backups(self, timestamp):
        """
        Returns all backups that are expired in the task.

        :rtype: list of Backup instances
        """
        # we will sort the folders and just loop from oldest to newest until we
        # have enough expired backups.
        expired_backups = []
        for interval_info in self.scheduling_info.interval_infos:
            logger.debug("Task \"%s\": Checking interval \"%s\" for "
                         "expired backups.",
                         self.name,
                         interval_info.name)

            backups_of_that_interval = [backup for
                                        backup in self.backups if
                                        backup.interval_name ==
                                        interval_info.name]

            expired_backups.extend(
                self._get_expired_backups_by_count(
                    backups_of_that_interval,
                    self.scheduling_info.get_info_by_name(interval_info.name).
                    keep_count))

            for expired_backup in self._get_expired_backups_by_age(
                    backups_of_that_interval,
                    self.scheduling_info.get_info_by_name(interval_info.name).
                    keep_age):
                if expired_backup not in expired_backups:
                    expired_backups.append(expired_backup)

        return expired_backups

    def _get_all_links_to(self, target):
        return [backup for backup in self.backups if
                backup.data_is_link_to(target)]

    def handle_expired_backups(self, timestamp):
        """
        Gets and handles all expired backups. Removes expired backups and takes
        care about all pending symlinks.

        """
        expired_backups = self.get_expired_backups(timestamp=timestamp)
        if len(expired_backups) == 0:
            logger.verbose("No expired backups.")
            return

        for expired_backup in expired_backups:
            logger.info("Expired backup: \"%s\".",
                        expired_backup.name)

            if not expired_backup.data_is_link():

                symlinks = self._get_all_links_to(expired_backup)

                if len(symlinks) != 0:
                    new_real_backup = symlinks[0]
                    logger.debug("Linked folder at \"%s\" points to the "
                                 "expired backup \"%s\", data will be moved "
                                 "over.",
                                 new_real_backup.path,
                                 expired_backup.path)

                    # move the data from the expired backup to the new "real"
                    # backup
                    new_real_backup.remove_data_link()
                    expired_backup.move_data_to(new_real_backup)

                    # update all remaining symlinks to point to the new backup
                    # instead of the expired one
                    for remaining_symlink in symlinks[1:]:
                        logger.debug("Fixing folder at \"%s\" so it points to "
                                     "\"%s\"..",
                                     remaining_symlink.path,
                                     new_real_backup.path)

                        remaining_symlink.remove_data_link()
                        remaining_symlink.link_data_from(new_real_backup)

            expired_backup.remove()
            self._unregister_backup(expired_backup)

            logger.info("Backup removed successfully.")

    def _relink_latest_symlink(self, backup):
        """
        Updates the "latest" symlink to make it point to a new backup.
        """
        destination = backup.path
        logger.debug("Fixing latest symlink, new target is \"%s\".",
                     destination)
        symlink_latest = os.path.join(self.destination,
                                      const.SYMLINK_LATEST_NAME)
        if os.path.islink(symlink_latest):
            files.remove_symlink(symlink_latest)
        files.create_symlink(destination, symlink_latest)
        logger.debug("Latest symlink fixed.")

    def _get_expired_backups_by_count(self, backups, max_count):
        """
        Returns all backups that are expired relative to the maximum count of
        kept backups. Practically, just returns all backups except the
        "max_count" oldest.
        """
        expired_backups = []
        count = len(backups) - max_count
        backups.sort(key=lambda backup: backup.date, reverse=False)
        for i in range(0, count):
            logger.debug("Backup \"%s\" is expired because count %s is "
                         "exceeded.",
                         backups[i].name,
                         max_count)
            expired_backups.append(backups[i])
        return expired_backups

    def _get_expired_backups_by_age(self, backups, max_age):
        """
        Returns all backups that are expired relative to the maximum age of
        kept backups. It pracically just returns all backups older than
        max_age.
        """
        expired_backups = []
        for backup in backups:
            if backup.date < max_age:
                logger.debug("Backup \"%s\" expired because it is older than "
                             "\"%s\" which is the oldest possible time",
                             backup.name,
                             max_age.isoformat())
                expired_backups.append(backup)
        return expired_backups

    def _get_latest_backup(self):
        """
        Returns the latest/youngest backup, or None if there is none.
        """
        if len(self.backups) == 0:
            return None
        if len(self.backups) == 1:
            return self.backups[0]
        latest = self.backups[0]
        for backup in self.backups:
            if backup.date > latest.date:
                latest = backup
        return latest

    def _get_latest_backup_of_interval(self, interval):
        """
        Returns the latest/youngest backup of the given interval, or None if
        there is none.
        :param interval: The name of the interval to search for.
        :type interval: string
        """
        if len(self.backups) == 0:
            return None
        latest = None
        for backup in self.backups:
            if latest is None and backup.interval_name == interval.name:
                latest = backup
            elif latest is not None:
                if (backup.interval_name == interval.name and
                        backup.date > latest.date):
                    latest = backup
        return latest

    @property
    def status(self):
        return self._status

    def start(self):
        """
        Start the monitoring of the task in a new process.
        """
        logger.debug("Starting task \"%s\".", self.name)
        self._process = multiprocessing.Process(target=self._monitor,
                                                args=())
        self._process.start()
        self._status = TaskStatus.active

    def stop(self, block=True):
        """
        Stops the monitoring of the task gracefully. You can restart the
        monitoring with the :func:`start()` method.

        :param block: Specifies that the method call should block until the task
            is actually paused and has finished an already running operation. If
            set to `False`, the task might still do work after the function
            returns, but will not start another operation.

            .. note:: If you plan on restarting the task, you must not set this
                to `False` or you will get undefinied behaviour.
        :type block: bool
        """
        logger.debug("Stopping task \"%s\".", self.name)
        self._pause_monitoring(block=block)
        self._kill_process()
        self._status = TaskStatus.stopped

    def abort(self):
        """
        Stops the monitoring of the task brutally, i.e. it just kills the
        monitoring process.

        .. warning:: This method might leave an invalid backup behind and should
            be avoided.
        """
        logger.debug("Aborting task \"%s\".", self.name)
        self._kill_process()
        self._status = TaskStatus.stopped

    def pause(self, block=True):
        """
        Pauses the monitoring of the task gracefully.

        You can resume the monitoring with the :func:`resume()` method. Using
        `resume()` after pausing with `block=False` is safe.

        :param block: Specifies that the method call should block until the task
            is actually paused and has finished an already running operation. If
            set to `False`, the task might still do work after the function
            returns, but will not start another operation.
        :type block: bool
        """
        logger.debug("Pausing task \"%s\".", self.name)
        self._pause_monitoring(block=block)
        self._status = TaskStatus.paused

    def resume(self):
        """
        Resumes the monitoring of the task if it was paused. If the task is
        not paused, an error is raised.

        :raise ValueError: if the task is not paused
        """
        logger.debug("Resuming task \"%s\".", self.name)
        if not self.status == TaskStatus.paused:
            raise ValueError("task is not paused, cannot be resumed")
        self._resume_monitoring()
        self._status = TaskStatus.active

    def _kill_process(self):
        self._process.terminate()
        self._process.join()

    def _pause_monitoring(self, block=True):
        self._pausing_event.clear()
        if block:
            self._paused_event.wait()

    def _resume_monitoring(self):
        self._pausing_event.set()

    def _monitor(self):
        """
        This is the method that runs in a separate task and checks for new and
        expired backups whenever `event` is raised.

        :param event: The event that triggers the monitoring.
        :type event: multiprocessing.event instance
        """

        self._event_exit.clear()
        self._pausing_event.set()

        while True:
            self._paused_event.set()
            self._pausing_event.wait()
            self._paused_event.clear()

            self._status = TaskStatus.working
            start = datetime.datetime.now()
            logger.debug("checking task %s at %s", self.name, start)
            self.create_backups_if_necessary(timestamp=start)
            self.handle_expired_backups(timestamp=start)
            self._status = TaskStatus.active

            wait_seconds = 60 - datetime.datetime.now().second
            logger.debug("Sleeping %s seconds.", wait_seconds)
            while wait_seconds > 0:
                if not self._pausing_event.is_set():
                    self._paused_event.set()
                    self._pausing_event.wait()
                    self._paused_event.clear()
                    break
                time.sleep(1)
                wait_seconds -= 1


class TaskStatus(enum.Enum):
    stopped = 1
    active = 2
    working = 3
    paused = 4


class IntervalInfo(object):
    """
    Contains information about a backup interval. This means:
        - information about when to create a new backup
        - information about when to delete an existing backup

    :param name: The name of the interval.
    :type name: str

    :param cron_pattern: A cronjob to specify the interval
    :type cron_pattern: Cronjob instance

    :param keep_count: The amount of backups to keep.
    :type keep_count: int

    :param keep_age: The maximum age allowed for a backup.
    :type keep_age: Interval instance
    """

    def __init__(self, name, cron_pattern, keep_count, keep_age):
        self.name = name
        self.cronjob = cron_pattern
        self.keep_count = keep_count
        self._keep_age = keep_age

    @property
    def keep_age(self):
        return self._keep_age.get_oldest_datetime()


class TaskSchedulingInfo(object):
    """
    Contains information about when a tasks requires a new backup or a backup
    expires. This is generally just a list of IntervalInfo objects.
    """

    def __init__(self, interval_infos=None):
        self.interval_infos = [] if interval_infos is None else interval_infos

    def append(self, interval_info):
        """
        Append a new interval info to the schedule.

        :type interval_info: IntervalInfo instance
        """
        if interval_info in self.interval_infos:
            raise ValueError("interval info already in scheduling info")
        self.interval_infos.append(interval_info)

    def get_info_by_name(self, name):
        """
        Return the interval info with the given name.

        :type name: str
        """
        for interval_info in self.interval_infos:
            if interval_info.name == name:
                return interval_info
        raise ValueError("no interval_info with name \"%s\" found.")


class BackupParameters(object):

    def __init__(self, link_ref, rsync_cmd, rsync_args, rsync_filter,
                 rsync_logfile_options):
        self.link_ref = link_ref
        self.rsync_cmd = rsync_cmd
        self.rsync_args = rsync_args
        self.rsync_filter = rsync_filter
        self.rsync_logfile_options = rsync_logfile_options
