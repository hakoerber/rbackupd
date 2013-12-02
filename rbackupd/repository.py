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
import re
import sys

from . import cron

BACKUP_REGEX = re.compile(r'^.*_.*_.*\.snapshot$')
BACKUP_SUFFIX = ".snapshot"

logger = logging.getLogger(__name__)


class Repository(object):
    """
    Represents a repository of backups, which means a collection of backups
    that are managed together. Provides methods to determine whether new
    backups are necessary and get expired backups.
    """

    def __init__(self, sources, destination, name, intervals, keep, keep_age,
                 rsyncfilter, rsync_logfile_options, rsync_args):
        self.sources = sources
        self.destination = destination
        self.name = name
        self.intervals = [(interval_name, cron.Cronjob(interval)) for
                          (interval_name, interval) in intervals.items()]
        self.keep = keep
        self.keep_age = keep_age
        self.rsyncfilter = rsyncfilter
        self.rsync_logfile_options = rsync_logfile_options
        self.rsync_args = rsync_args

    @property
    def backups(self):
        return [BackupFolder(folder) for folder in os.listdir(self.destination)
                if is_backup_folder(folder)]

    def get_necessary_backups(self):
        """
        Returns all backups deemed necessary.
        :returns: A list of tuples containing all necessary backups, each tuple
        consisting of the interval name as first and the interval cron object
        as second element.
        :returns: All backups deemed necessary.
        :rtype: list of tuples.
        """
        necessary_backups = []
        for (interval_name, interval) in self.intervals:
            latest_backup = self._get_latest_backup_of_interval(interval_name)
            if latest_backup is None:
                necessary_backups.append((interval_name, interval))
                continue
            if interval.has_occured_since(latest_backup.date,
                                          include_start=False):
                necessary_backups.append((interval_name, interval))
        return necessary_backups

    def get_backup_params(self, new_backup_interval_name, timestamp=None):
        """
        Gets the parameters for a backup of the specific interval with a given
        timestamp.
        :param new_backup_interval_name: The interval name of the new backup.
        :type new_backup_interval_name: string
        :param timestamp: The timestamp of the new backup or the current time
        of omitted.
        :type timestamp: datetime.datetime instance
        :returns: A BackupParameters instance with information about the new
        backup.
        :rtype: BackupParameters instance
        """
        if timestamp is None:
            timestamp = datetime.datetime.now()
        new_link_ref = self._get_latest_backup()
        new_link_ref = new_link_ref.name if new_link_ref is not None else None
        new_folder = "%s_%s_%s%s" % (self.name,
                                     timestamp.strftime(
                                         "%Y-%m-%dT%H:%M:%S"),
                                     new_backup_interval_name,
                                     BACKUP_SUFFIX)

        backup_params = BackupParameters(self.sources,
                                         self.destination,
                                         new_folder,
                                         new_link_ref,
                                         self.rsyncfilter,
                                         self.rsync_logfile_options,
                                         self.rsync_args)
        return backup_params

    def get_expired_backups(self):
        """
        Returns all backups that are expired in the repository.
        :param current_time: The current time to check against.
        :type current_time: datetime.datetime instance
        :returns: All expired backups.
        :rtype: list of Backup instances
        """
        # we will sort the folders and just loop from oldest to newest until we
        # have enough expired backups.
        expired_backups = []
        for interval in self.intervals:

            (interval_name, interval_cron) = interval

            if interval_name not in self.keep:
                logger.critical("No corresponding interval found for keep "
                                "value \"%s\"", interval_name)
                sys.exit(9)

            if interval_name not in self.keep_age:
                logger.critical("No corresponding age interval found of keep "
                                "value \"%s\"", interval_name)
                sys.exit(10)

            backups_of_that_interval = [backup for backup in self.backups if
                                        backup.interval_name == interval_name]

            expired_backups.extend(
                self._get_expired_backups_by_count(backups_of_that_interval,
                                                   self.keep[interval_name]))
            expired_backups.extend(
                self._get_expired_backups_by_age(backups_of_that_interval,
                                                 self.keep_age[interval_name]))

        return expired_backups

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
                logger.debug("Backup \"%s\" older than \"%s\" which is the "
                             "oldest possible time",
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
            if latest is None and backup.interval_name == interval:
                latest = backup
            elif latest is not None:
                if (backup.interval_name == interval and
                        backup.date > latest.date):
                    latest = backup
        return latest


class BackupParameters(object):

    def __init__(self, sources, destination, folder, link_ref,
                 rsyncfilter, rsync_logfile_options, rsync_args):
        self.sources = sources
        self.destination = destination
        self.folder = folder
        self.link_ref = link_ref
        self.rsyncfilter = rsyncfilter
        self.rsync_logfile_options = rsync_logfile_options
        self.rsync_args = rsync_args


class BackupFolder(object):

    def __init__(self, name):
        self._name = name

        datestring = self.name.split("_")[1]
        self._date = datetime.datetime.strptime(datestring,
                                                "%Y-%m-%dT%H:%M:%S")
        intervalstring = self.name.split("_")[2]
        self._interval = intervalstring[:intervalstring.find(BACKUP_SUFFIX)]

    @property
    def date(self):
        return self._date

    @property
    def interval_name(self):
        return self._interval

    @property
    def name(self):
        return self._name


def is_backup_folder(name):
    return BACKUP_REGEX.match(name)
