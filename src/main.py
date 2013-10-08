import sys
import os
import time
import datetime

import config
import cron
import rsync

BACKUP_SUFFIX = ".snapshot"

def main():
    if len(sys.argv) != 2:
        print("invalid arguments")
        sys.exit(2)
    path_config = sys.argv[1]
    if not os.path.isfile(path_config):
        print("config file not found")
        sys.exit(1)

    conf = config.Config(path_config)

    rsync_settings = conf.get_section("rsync")
    rsync_cmd = rsync_settings.get("cmd", "rsync")
    rsync_args = rsync_settings["args"]

    conf_default = conf.get_section("default")

    conf_default_filter_patterns = conf_default.get("filter" , None)

    conf_default_include_patterns = conf_default.get("include", None)
    conf_default_exclude_patterns = conf_default.get("exclude", None)

    conf_default_include_files = conf_default.get("includefile", None)
    conf_default_exclude_files = conf_default.get("excludefile", None)

    repositories = []
    for task in conf.get_sections("task"):
        destination = task["destination"][0]
        if not os.path.exists(destination):
            print("destination not found")
            sys.exit(3)
        if not os.path.isdir(destination):
            print("destination not a directory")
            sys.exit(2)
        sources = task["source"]
        for source in sources:
            if not os.path.exists(source):
                print("source not found")
                sys.exit(4)

        filter_patterns = task.get("filter", conf_default_filter_patterns)

        include_patterns = task.get("include", conf_default_include_patterns)
        exclude_patterns = task.get("exclude", conf_default_exclude_patterns)

        include_files = task.get("includefile", conf_default_include_files)
        exclude_files = task.get("excludefile", conf_default_exclude_files)

        if include_files is not None:
            for include_file in include_files:
                continue
                if not os.path.exists(include_file):
                    print("include file not found")
                    sys.exit(5)
                elif not os.path.isfile(include_file):
                    print("include file is not a valid file")
                    sys.exit(6)

        if exclude_files is not None:
            for exclude_file in exclude_files:
                continue
                if not os.path.exists(exclude_file):
                    print("exclude file not found")
                    sys.exit(7)
                elif not os.path.isfile(exclude_file):
                    print("exclude file is not a valid file")
                    sys.exit(8)

        rsyncfilter = rsync.Filter(include_patterns, exclude_patterns, include_files, exclude_files, filter_patterns)

        repositories.append(
            Repository(sources,
                       destination,
                       task["name"][0],
                       task["interval"],
                       task["keep"],
                       rsyncfilter))

    while True:
        for repository in repositories:
            necessary_backups = repository.get_necessary_backups()
            if necessary_backups is None:
                print("no backup necessary")
            else:
                new_backup_interval_name = min(necessary_backups)[0]
                new_backup = repository.get_backup_params(new_backup_interval_name)
                for source in new_backup[0]:
                    link_dest = None if new_backup[3] is None else os.path.join(new_backup[1], new_backup[3])
                    print("rsyncing")
                    (returncode, stdoutdata, stderrdata) = \
                    rsync.rsync(rsync_cmd, source, os.path.join(new_backup[1], new_backup[2]),
                                link_dest, rsync_args, new_backup[5])
                    print("rsync exited with code %s\nstdout:\n%s\nstderr:\n%s" % (returncode, stdoutdata, stderrdata))

            expired_backups = repository.get_expired_backups()
            if expired_backups is not None:
                for expired_backup in expired_backups:
                    print("expired:",expired_backup.name)
            else:
                print("no expired backups")
        now = datetime.datetime.now()
        if now.minute == 59:
            wait_seconds = 1
        else:
            nextmin = now.replace(minute=now.minute+1, second=0, microsecond=0)
            wait_seconds = (nextmin - now).seconds + 1
        print(datetime.datetime.now(), wait_seconds)
        time.sleep(wait_seconds)



class Repository(object):

    def __init__(self, sources, destination, name, intervals, keep, rsyncfilter):
        self.sources = sources
        self.destination = destination
        self.name = name
        self.intervals = [(interval_name, cron.Cronjob(interval)) for (interval_name, interval) in intervals.items()]

        self.keep = keep
        self.rsyncfilter = rsyncfilter

        self._oldfolders = None
        self._backups = self._parse_folders(self.destination)

    @property
    def backups(self):
        folders = os.listdir(self.destination)
        if folders != self._oldfolders:
            self._backups = self._parse_folders(self.destination)
            self._oldfolders = folders
        return self._backups

    def _parse_folders(self, directory):
        return [BackupFolder(folder) for folder in os.listdir(directory)]

    def get_necessary_backups(self):
        latest_backup = self._get_latest_backup()
        if latest_backup is None:
            return self.intervals

        # cron.has_occured_since INCLUDES all occurences of the cronjob in the search
        # therefore if would match the last backup if it occured EXACTLY at the given
        # time in the cronjob. ugly fix here: were just add 1 microsecond to the latest
        # backup

        latest_backup_date = latest_backup.date
        latest_backup_date += datetime.timedelta(microseconds=1)

        necessary_backups = []

        for (interval_name, interval) in self.intervals:
            if interval.has_occured_since(latest_backup_date):
                necessary_backups.append((interval_name, interval))

        if len(necessary_backups) == 0:
            return None
        return necessary_backups


    def get_backup_params(self, new_backup_interval_name):
        new_sources = self.sources
        new_destination = self.destination
        new_name = self.name
        new_link_ref = self._get_latest_backup()
        new_link_ref = new_link_ref.name if new_link_ref is not None else None
        new_folder = "%s_%s_%s%s" % (new_name, new_backup_interval_name,
                                     datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), BACKUP_SUFFIX)
        return (new_sources, new_destination, new_folder, new_link_ref, new_name, self.rsyncfilter)


    def get_expired_backups(self):
        # we will sort the folders and just loop from oldest to newest until we have enough
        # expired backups.
        result = []
        for interval in self.intervals:
            interval_name = interval[0]

            if interval_name not in self.keep:
                print("No corresponding interval found for keep value %s" % interval_name)
                sys.exit(9)

            backups_of_that_interval = list(filter(lambda backup: backup.interval_name == interval_name, self.backups))

            count = len(backups_of_that_interval) - self.keep[interval_name]

            if count <= 0:
                continue

            backups_of_that_interval.sort(key=lambda backup: backup.date, reverse=False)
            for i in range(0, count):
                result.append(self.backups[i])

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

class BackupFolder(object):

    def __init__(self, name):
        self._name = name

    @property
    def date(self):
        datestring = self.name.split("_")[2]
        datestring = datestring[:datestring.find(BACKUP_SUFFIX)]
        date = datetime.datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%S")
        return date

    @property
    def interval_name(self):
        return self.name.split("_")[1]

    @property
    def name(self):
        return self._name


if __name__ == "__main__":
    main()

