import os
import sys
import datetime
import re

from . import cron

BACKUP_REGEX = re.compile(r'^.*_.*_.*\.snapshot$')
BACKUP_SUFFIX = ".snapshot"


class Repository(object):

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

        self._oldfolders = os.listdir(self.destination)
        self._backups = self._parse_folders(self._oldfolders)

    @property
    def backups(self):
        folders = os.listdir(self.destination)
        if folders != self._oldfolders:
            self._backups = self._parse_folders(folders)
            self._oldfolders = folders
        return self._backups

    def _parse_folders(self, folders):
        return [BackupFolder(folder) for folder in folders
                if is_backup_folder(folder)]

    def get_necessary_backups(self):

        necessary_backups = []

        for (interval_name, interval) in self.intervals:
            latest_backup = self._get_latest_backup_of_interval(interval_name)

            # if there is no backup of that type present, we have to make one
            if latest_backup is None:
                necessary_backups.append((interval_name, interval))
                continue

            latest_backup_date = latest_backup.date
            # cron.has_occured_since INCLUDES all occurences of the cronjob in
            # the search. therefore if would match the last backup if it
            # occured EXACTLY at the given time in the cronjob. ugly fix here:
            # were just add 1 microsecond to the latest backup
            latest_backup_date += datetime.timedelta(microseconds=1)

            if interval.has_occured_since(latest_backup_date):
                necessary_backups.append((interval_name, interval))

        if len(necessary_backups) == 0:
            return None
        return necessary_backups

    def get_backup_params(self, new_backup_interval_name, timestamp=None):
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

    def get_expired_backups(self, current_time):
        # we will sort the folders and just loop from oldest to newest until we
        # have enough expired backups.
        result = []
        for interval in self.intervals:
            (interval_name, interval_cron) = interval

            if interval_name not in self.keep:
                print("No corresponding interval found for keep value %s" %
                      interval_name)
                sys.exit(9)

            if interval_name not in self.keep_age:
                print("No corresponding age interval found of keep value %s" %
                      interval_name)
                sys.exit(10)

            backups_of_that_interval = [backup for backup in self.backups if
                                        backup.interval_name == interval_name]

            count = len(backups_of_that_interval) - self.keep[interval_name]

            backups_of_that_interval.sort(key=lambda backup: backup.date,
                                          reverse=False)
            for i in range(0, count):
                result.append(backups_of_that_interval[i])

            for backup in backups_of_that_interval:
                if backup.date < self.keep_age[interval_name]:
                    if backup not in result:
                        result.append(backup)

        return result

    def _get_latest_backup(self):
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
    if BACKUP_REGEX.match(name):
        return True
    else:
        print("%s is not a backup folder" % name)
        return False
