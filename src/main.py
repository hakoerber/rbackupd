import datetime
import os
import subprocess
import sys
import time

import config
import cron
import rsync

BACKUP_SUFFIX = ".snapshot"

EXIT_INVALID_COMMANDLINE = 1
EXIT_CONFIG_FILE_NOT_FOUND = 2
EXIT_INCLUDE_FILE_NOT_FOUND = 3
EXIT_INCLUDE_FILE_INVALID = 4
EXIT_EXCULDE_FILE_NOT_FOUND = 5
EXIT_EXCLUDE_FILE_INVALID = 6
EXIT_RM_FAILED = 7
EXIT_RSYNC_FAILED = 8

DEFAULT_RSYNC_CMD = "rsync"

def main():
    if len(sys.argv) != 2:
        print("invalid arguments")
        sys.exit(EXIT_INVALID_COMMANDLINE)
    path_config = sys.argv[1]
    if not os.path.isfile(path_config):
        print("config file not found")
        sys.exit(EXIT_CONFIG_FILE_NOT_FOUND)

    conf = config.Config(path_config)

    # this is the [rsync] section
    conf_section_rsync = conf.get_section("rsync")
    conf_rsync_cmd = conf_section_rsync.get("cmd", DEFAULT_RSYNC_CMD)

    # these are the [default] options that can be overwritten in the specific
    # [task] section
    conf_section_default = conf.get_section("default")

    conf_default_rsync_logfile = conf_section_default.get("rsync_logfile", None)
    conf_default_rsync_logfile_name = conf_section_default.get(
        "rsync_logfile_name", None)
    conf_default_rsync_logfile_format = conf_section_default.get(
        "rsync_logfile_format", None)

    conf_default_filter_patterns = conf_section_default.get("filter", None)

    conf_default_include_patterns = conf_section_default.get("include", None)
    conf_default_exclude_patterns = conf_section_default.get("exclude", None)

    conf_default_include_files = conf_section_default.get("includefile", None)
    conf_default_exclude_files = conf_section_default.get("excludefile", None)

    conf_default_create_destination = conf_section_default.get(
        "create_destination", None)

    conf_default_one_filesystem = conf_section_default.get("one_fs", None)

    conf_default_rsync_args = conf_section_default.get("rsync_args", None)

    conf_sections_tasks = conf.get_sections("task")

    repositories = []
    for task in conf_sections_tasks:
        # these are the options given in the specific tasks. if none are given,
        # the default values from the [default] sections will be used.
        conf_rsync_logfile = task.get(
            "rsync_logfile", conf_default_rsync_logfile)
        conf_rsync_logfile_name = task.get(
            "rsync_logfile_name", conf_default_rsync_logfile_name)[0]
        conf_rsync_logfile_format = task.get(
            "rsync_logfile_format", conf_default_rsync_logfile_format)[0]

        conf_filter_patterns = task.get("filter", conf_default_filter_patterns)

        conf_include_patterns = task.get(
            "include", conf_default_include_patterns)
        conf_exclude_patterns = task.get(
            "exclude", conf_default_exclude_patterns)

        conf_include_files = task.get(
            "includefile", conf_default_include_files)
        conf_exclude_files = task.get(
            "excludefile", conf_default_exclude_files)

        conf_create_destination = task.get(
            "create_destination", conf_default_create_destination)

        conf_one_filesystem = task.get(
            "one_fs", conf_default_one_filesystem)[0]

        conf_rsync_args = task.get("rsync_args", conf_default_rsync_args)

        # these are the options that are not given in the [default] section.
        conf_destination = task["destination"][0]
        conf_sources = task["source"]

        # now we can check the values
        if not os.path.exists(conf_destination):
            if not create_destination:
                print("destination \"%s\" does not exists, will no be "
                      "created. repository will be skipped." %
                      conf_destination)
                continue
        if not os.path.isdir(conf_destination):
            print("destination \"%s\" not a directory" % conf_destination)
            sys.exit(EXIT_INVALID_DESTINATION)

        if conf_include_files is not None:
            for include_file in conf_include_files:
                continue
                if not os.path.exists(include_file):
                    print("include file \"%s\" not found" % include_file)
                    sys.exit(EXIT_INCLUDE_FILE_NOT_FOUND)
                elif not os.path.isfile(include_file):
                    print("include file \"%s\" is not a valid file" %
                          include_file)
                    sys.exit(EXIT_INCLUDE_FILE_INVALID)

        if conf_exclude_files is not None:
            for exclude_file in conf_exclude_files:
                continue
                if not os.path.exists(exclude_file):
                    print("exclude file \"%s\" not found" % exclude_file)
                    sys.exit(EXIT_EXCULDE_FILE_NOT_FOUND)
                elif not os.path.isfile(exclude_file):
                    print("exclude file \"%s\" is not a valid file" %
                          exclude_file)
                    sys.exit(EXIT_EXCLUDE_FILE_INVALID)

        if conf_rsync_logfile:
            conf_rsync_logfile_options = rsync.LogfileOptions(
                conf_rsync_logfile_name, conf_rsync_logfile_format)
        else:
            conf_rsync_logfile_options = None

        conf_rsyncfilter = rsync.Filter(conf_include_patterns,
                                        conf_exclude_patterns,
                                        conf_include_files,
                                        conf_exclude_files,
                                        conf_filter_patterns)

        rsync_args = []
        for arg in conf_rsync_args:
            rsync_args.extend(arg.split())
        conf_rsync_args = rsync_args

        if conf_one_filesystem:
            conf_rsync_args.append("-x")

        conf_taskname = task["name"][0]
        conf_task_intervals = task["interval"]
        conf_task_keeps = task["keep"]

        repositories.append(
            Repository(conf_sources,
                       conf_destination,
                       conf_taskname,
                       conf_task_intervals,
                       conf_task_keeps,
                       conf_rsyncfilter,
                       conf_rsync_logfile_options,
                       conf_rsync_args))

    while True:
        for repository in repositories:
            necessary_backups = repository.get_necessary_backups()
            if necessary_backups is None:
                print("no backup necessary")
            else:
                print(necessary_backups)

                new_backup_interval_name = min(necessary_backups)[0]

                new_backup = repository.get_backup_params(
                    new_backup_interval_name)

                for source in new_backup.sources:
                    if new_backup.link_ref is None:
                        link_dest = None
                    else:
                        link_dest = os.path.join(new_backup.destination,
                                                 new_backup.link_ref)
                    destination = os.path.join(new_backup.destination,
                                               new_backup.folder)
                    print("rsyncing")
                    (returncode, stdoutdata, stderrdata) = rsync.rsync(
                        conf_rsync_cmd,
                        source,
                        destination,
                        link_dest,
                        new_backup.rsync_args,
                        new_backup.rsyncfilter,
                        new_backup.rsync_logfile_options)
                    print("rsync exited with code %s\n\nstdout:\n%s\n\n"
                          "stderr:\n%s\n" % (returncode, str(stdoutdata),
                                             str(stderrdata)))
                    if returncode != 0:
                        print("rsync FAILED. aborting")
                        sys.exit(EXIT_RSYNC_FAILED)

            expired_backups = repository.get_expired_backups()
            if len(expired_backups) > 0:
                for expired_backup in expired_backups:
                    print("expired:", expired_backup.name)
                    returncode = subprocess.call(
                        ["rm", "-r", "-f", os.path.join(
                            repository.destination, expired_backup.name)])

                    if returncode == 0:
                        print("backup removed.")
                    else:
                        print("removing the backup failed. aborting.")
                        sys.exit(EXIT_RM_FAILED)

            else:
                print("no expired backups")
        now = datetime.datetime.now()
        if now.second == 59:
            wait_seconds = 1
        else:
            nextmin = now.replace(minute=now.minute+1, second=0, microsecond=0)
            wait_seconds = (nextmin - now).seconds + 1
        time.sleep(wait_seconds)


class Repository(object):

    def __init__(self, sources, destination, name, intervals, keep,
                 rsyncfilter, rsync_logfile_options, rsync_args):
        self.sources = sources
        self.destination = destination
        self.name = name
        self.intervals = [(interval_name, cron.Cronjob(interval)) for
                          (interval_name, interval) in intervals.items()]
        self.keep = keep
        self.rsyncfilter = rsyncfilter
        self.rsync_logfile_options = rsync_logfile_options
        self.rsync_args = rsync_args

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

        # cron.has_occured_since INCLUDES all occurences of the cronjob in the
        # search. therefore if would match the last backup if it occured
        # EXACTLY at the given time in the cronjob. ugly fix here: were just
        # add 1 microsecond to the latest backup

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
        new_link_ref = self._get_latest_backup()
        new_link_ref = new_link_ref.name if new_link_ref is not None else None
        new_folder = "%s_%s_%s%s" % (self.name, new_backup_interval_name,
                                     datetime.datetime.now().strftime(
                                         "%Y-%m-%dT%H:%M:%S"), BACKUP_SUFFIX)

        backup_params = BackupParameters(self.sources,
                                         self.destination,
                                         new_folder,
                                         new_link_ref,
                                         self.rsyncfilter,
                                         self.rsync_logfile_options,
                                         self.rsync_args)

        return backup_params

    def get_expired_backups(self):
        # we will sort the folders and just loop from oldest to newest until we
        # have enough expired backups.
        result = []
        for interval in self.intervals:
            interval_name = interval[0]

            if interval_name not in self.keep:
                print("No corresponding interval found for keep value %s" %
                      interval_name)
                sys.exit(9)

            backups_of_that_interval = list(filter(
                lambda backup: backup.interval_name == interval_name,
                self.backups))

            count = len(backups_of_that_interval) - self.keep[interval_name]

            if count <= 0:
                continue

            backups_of_that_interval.sort(key=lambda backup: backup.date,
                                          reverse=False)
            for i in range(0, count):
                result.append(backups_of_that_interval[i])

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

class BackupParameters(object):

    def __init__(self, sources, destination, folder, link_ref,
                 rsyncfilter, rsync_logfile_options, rsync_args):
        self.sources = sources
        self.destination = destination
        self.folder = folder
        self.link_ref = link_ref
        self.rsyncfilter = rsyncfilter
        self.rsync_logfile_options = rsync_logfile_options
        self.rsync_args  = rsync_args

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
