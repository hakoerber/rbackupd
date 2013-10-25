import datetime
import os
import re
import subprocess
import sys
import time

from . import config
from . import cron
from . import filesystem
from . import rsync


BACKUP_SUFFIX = ".snapshot"

BACKUP_REGEX = re.compile('^.*_.*_.*\.snapshot$')

SSH_CMD = "ssh"

EXIT_INVALID_COMMANDLINE = 1
EXIT_CONFIG_FILE_NOT_FOUND = 2
EXIT_INCLUDE_FILE_NOT_FOUND = 3
EXIT_INCLUDE_FILE_INVALID = 4
EXIT_EXCULDE_FILE_NOT_FOUND = 5
EXIT_EXCLUDE_FILE_INVALID = 6
EXIT_RM_FAILED = 7
EXIT_RSYNC_FAILED = 8
EXIT_CONFIG_FILE_INVALID = 9

DEFAULT_RSYNC_CMD = "rsync"

CONF_SECTION_RSYNC = "rsync"
CONF_KEY_RSYNC_CMD = "cmd"

CONF_SECTION_MOUNT = "mount"
CONF_KEY_DEVICE = "device"
CONF_KEY_MOUNTPOINT = "mountpoint"
CONF_KEY_MOUNTPOINT_RO = "mountpoint_ro"
CONF_KEY_MOUNTPOINT_OPTIONS = "mountpoint_options"
CONF_KEY_MOUNTPOINT_RO_OPTIONS = "mountpoint_options"
CONF_KEY_MOUNTPOINT_CREATE = "mountpoint_create"
CONF_KEY_MOUNTPOINT_RO_CREATE = "mountpoint_ro_create"

CONF_SECTION_DEFAULT = "default"
CONF_KEY_RSYNC_LOGFILE = "rsync_logfile"
CONF_KEY_RSYNC_LOGFILE_NAME = "rsync_logfile_name"
CONF_KEY_RSYNC_LOGFILE_FORMAT = "rsync_logfile_format"
CONF_KEY_FILTER_PATTERNS = "filter"
CONF_KEY_INCLUDE_PATTERNS = "include"
CONF_KEY_EXCLUDE_PATTERNS = "exclude"
CONF_KEY_INCLUDE_FILE = "includefile"
CONF_KEY_EXCLUDE_FILE = "excludefile"
CONF_KEY_CREATE_DESTINATION = "create_destination"
CONF_KEY_ONE_FILESYSTEM = "one_fs"
CONF_KEY_RSYNC_ARGS = "rsync_args"
CONF_KEY_SSH_ARGS = "ssh_args"
CONF_KEY_OVERLAPPING = "overlapping"

CONF_SECTION_TASK = "task"
CONF_KEY_DESTINATION = "destination"
CONF_KEY_SOURCE = "source"
CONF_KEY_TASKNAME = "name"
CONF_KEY_INTERVAL = "interval"
CONF_KEY_KEEP = "keep"


def run(config_file):
    if not os.path.isfile(config_file):
        print("config file not found")
        sys.exit(EXIT_CONFIG_FILE_NOT_FOUND)

    conf = config.Config(config_file)

    # this is the [rsync] section
    conf_section_rsync = conf.get_section(CONF_SECTION_RSYNC)
    conf_rsync_cmd = conf_section_rsync.get(CONF_KEY_RSYNC_CMD, "rsync")

    conf_sections_mounts = conf.get_sections(CONF_SECTION_MOUNT)

    # these are the [default] options that can be overwritten in the specific
    # [task] section
    conf_section_default = conf.get_section(CONF_SECTION_DEFAULT)
    conf_default_rsync_logfile = conf_section_default.get(
        CONF_KEY_RSYNC_LOGFILE, None)
    conf_default_rsync_logfile_name = conf_section_default.get(
        CONF_KEY_RSYNC_LOGFILE_NAME, None)
    conf_default_rsync_logfile_format = conf_section_default.get(
        CONF_KEY_RSYNC_LOGFILE_FORMAT, None)

    conf_default_filter_patterns = conf_section_default.get(
        CONF_KEY_FILTER_PATTERNS, None)

    conf_default_include_patterns = conf_section_default.get(
        CONF_KEY_INCLUDE_PATTERNS, None)
    conf_default_exclude_patterns = conf_section_default.get(
        CONF_KEY_EXCLUDE_PATTERNS, None)

    conf_default_include_files = conf_section_default.get(
        CONF_KEY_INCLUDE_FILE, None)
    conf_default_exclude_files = conf_section_default.get(
        CONF_KEY_EXCLUDE_FILE, None)

    conf_default_create_destination = conf_section_default.get(
        CONF_KEY_CREATE_DESTINATION, None)

    conf_default_one_filesystem = conf_section_default.get(
        CONF_KEY_ONE_FILESYSTEM, None)

    conf_default_rsync_args = conf_section_default.get(
        CONF_KEY_RSYNC_ARGS, None)

    conf_default_ssh_args = conf_section_default.get(
        CONF_KEY_SSH_ARGS, None)

    conf_default_overlapping = conf_section_default.get(
        CONF_KEY_OVERLAPPING, None)

    conf_sections_tasks = conf.get_sections(CONF_SECTION_TASK)

    for mount in conf_sections_mounts:
        if len(mount) == 0:
            continue

        conf_device = mount[CONF_KEY_DEVICE][0]
        conf_mountpoint = mount[CONF_KEY_MOUNTPOINT][0]
        conf_mountpoint_ro = mount.get(CONF_KEY_MOUNTPOINT_RO, [None])[0]
        conf_mountpoint_options = mount.get(
            CONF_KEY_MOUNTPOINT_OPTIONS, [None])[0]
        conf_mountpoint_ro_options = mount.get(
            CONF_KEY_MOUNTPOINT_RO_OPTIONS, [None])[0]

        if conf_mountpoint_options is None:
            conf_mountpoint_options = ['rw']
        else:
            conf_mountpoint_options = conf_mountpoint_options.split(',')
            conf_mountpoint_options.append('rw')

        if conf_mountpoint_ro_options is None:
            conf_mountpoint_ro_options = ['ro']
        else:
            conf_mountpoint_ro_options = conf_mountpoint_ro_options.split(',')
            conf_mountpoint_ro_options.append('ro')

        conf_mountpoint_create = mount[CONF_KEY_MOUNTPOINT_CREATE][0]

        conf_mountpoint_ro_create = mount.get(CONF_KEY_MOUNTPOINT_RO_CREATE,
                                              [None])[0]
        if (conf_mountpoint_ro is not None and
                conf_mountpoint_ro_create is None):
            print("mountpoint_ro_create needed")
            sys.exit(EXIT_INVALID_CONFIG)

        if (conf_mountpoint_ro is not None and conf_mountpoint_ro_create and
                not os.path.exists(conf_mountpoint_ro)):
            os.mkdir(conf_mountpoint_ro)
        if not os.path.exists(conf_mountpoint_ro):
            print("mountpoint_ro does not exist")
            sys.exit()
        if conf_mountpoint_create and not os.path.exists(conf_mountpoint):
            os.mkdir(conf_mountpoint)
        if not os.path.exists(conf_mountpoint):
            print("mountpoint does not exist")
            sys.exit()

        if conf_device.startswith('UUID'):
            uuid = conf_device.split('=')[1]
            device_identifier = filesystem.DeviceIdentifier(uuid=uuid)
        elif conf_device.startswith('LABEL'):
            label = conf_device.split('=')[1]
            device_identifier = filesystem.DeviceIdentifier(label=label)
        else:
            device_identifier = filesystem.DeviceIdentifier(path=conf_device)

        print(device_identifier.get())
        device = filesystem.Device(device_identifier, filesystem="auto")

        mountpoint = filesystem.Mountpoint(
            path=conf_mountpoint,
            options=conf_mountpoint_options)
        # How to get two mounts of the same device with different rw/ro:
        # mount readonly
        # bind readonly to the writeable mountpoint without altering rw/ro
        # remount writeable mountpoint with rw
        if conf_mountpoint_ro is not None:
            mountpoint_ro = filesystem.Mountpoint(
                path=conf_mountpoint_ro,
                options=conf_mountpoint_ro_options)
            device.mount(mountpoint_ro)

            mountpoint_ro.bind(mountpoint)
            mountpoint.remount(("rw", "relatime", "noexec", "nosuid"))
        else:
            device.mount(mountpoint)

    repositories = []
    for task in conf_sections_tasks:
        # these are the options given in the specific tasks. if none are given,
        # the default values from the [default] sections will be used.
        conf_rsync_logfile = task.get(
            CONF_KEY_RSYNC_LOGFILE, conf_default_rsync_logfile)
        conf_rsync_logfile_name = task.get(
            CONF_KEY_RSYNC_LOGFILE_NAME, conf_default_rsync_logfile_name)[0]
        conf_rsync_logfile_format = task.get(
            CONF_KEY_RSYNC_LOGFILE_FORMAT,
            conf_default_rsync_logfile_format)[0]

        conf_filter_patterns = task.get(
            CONF_KEY_FILTER_PATTERNS, conf_default_filter_patterns)

        conf_include_patterns = task.get(
            CONF_KEY_INCLUDE_PATTERNS, conf_default_include_patterns)
        conf_exclude_patterns = task.get(
            CONF_KEY_EXCLUDE_PATTERNS, conf_default_exclude_patterns)

        conf_include_files = task.get(
            CONF_KEY_INCLUDE_FILE, conf_default_include_files)
        conf_exclude_files = task.get(
            CONF_KEY_EXCLUDE_FILE, conf_default_exclude_files)

        conf_create_destination = task.get(
            CONF_KEY_CREATE_DESTINATION, conf_default_create_destination)

        conf_one_filesystem = task.get(
            CONF_KEY_ONE_FILESYSTEM, conf_default_one_filesystem)[0]

        conf_rsync_args = task.get(
            CONF_KEY_RSYNC_ARGS, conf_default_rsync_args)

        conf_ssh_args = task.get(
            CONF_KEY_SSH_ARGS, conf_default_ssh_args)
        conf_ssh_args = SSH_CMD + " " + " ".join(conf_ssh_args)

        conf_overlapping = task.get(
            CONF_KEY_OVERLAPPING, conf_default_overlapping)[0]

        # these are the options that are not given in the [default] section.
        conf_destination = task[CONF_KEY_DESTINATION][0]
        conf_sources = task[CONF_KEY_SOURCE]

        if conf_overlapping not in ["single", "hardlink", "symlink"]:
            print("invalid value for \"overlapping\": %s" % conf_overlapping)

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
                if not os.path.exists(include_file):
                    print("include file \"%s\" not found" % include_file)
                    sys.exit(EXIT_INCLUDE_FILE_NOT_FOUND)
                elif not os.path.isfile(include_file):
                    print("include file \"%s\" is not a valid file" %
                          include_file)
                    sys.exit(EXIT_INCLUDE_FILE_INVALID)

        if conf_exclude_files is not None:
            for exclude_file in conf_exclude_files:
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

        ssh_args = []
        if conf_ssh_args is not None:
            ssh_args = ["--rsh", conf_ssh_args]
        conf_rsync_args.extend(ssh_args)

        conf_taskname = task[CONF_KEY_TASKNAME][0]
        conf_task_intervals = task[CONF_KEY_INTERVAL]
        conf_task_keeps = task[CONF_KEY_KEEP]

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
            create_backups_if_necessary(repository, conf_overlapping,
                                        conf_rsync_cmd)
            handle_expired_backups(repository)

        now = datetime.datetime.now()
        if now.minute == 59:
            wait_seconds = 60 - now.second
        else:
            nextmin = now.replace(minute=now.minute+1, second=0, microsecond=0)
            wait_seconds = (nextmin - now).seconds + 1
        time.sleep(wait_seconds)


def create_backups_if_necessary(repository, conf_overlapping, conf_rsync_cmd):
    necessary_backups = repository.get_necessary_backups()
    if necessary_backups is not None:
        if conf_overlapping == "single":
            new_backup_interval_name = None
            exitloop = False
            for (name, _) in repository.intervals:
                for (backup_name, _) in necessary_backups:
                    if name == backup_name:
                        new_backup_interval_name = name
                        exitloop = True
                        break
                if exitloop:
                    break
            new_backup = repository.get_backup_params(new_backup_interval_name)
            create_backup(new_backup, conf_rsync_cmd)

        else:
            # Make one "real" backup and just hard/symlink all others to this
            # one
            real_backup = repository.get_backup_params(necessary_backups[0][0])
            create_backup(real_backup, conf_rsync_cmd)
            for backup in necessary_backups[1:]:
                backup = repository.get_backup_params(backup[0])
                # real_backup.destination and backup.destination are guaranteed
                # to be identical as they are from the same repository
                source = os.path.join(real_backup.destination,
                                      real_backup.folder)
                destination = os.path.join(real_backup.destination,
                                           backup.folder)
                if conf_overlapping == "hardlink":
                    copy_hardlinks(source, destination)
                elif conf_overlapping == "symlink":
                    # We should create RELATIVE symlinks with "-r", as the
                    # repository might move, but the relative location of all
                    # backups will stay the same
                    create_symlink(source, destination)
                else:
                    # panic and run away
                    print("invalid value for overlapping")
                    sys.exit(EXIT_CONFIG_FILE_INVALID)
    else:
        print("no backup necessary")


def create_backup(new_backup, rsync_cmd):
    for source in new_backup.sources:
        if new_backup.link_ref is None:
            link_dest = None
        else:
            link_dest = os.path.join(new_backup.destination,
                                     new_backup.link_ref)
        destination = os.path.join(new_backup.destination,
                                   new_backup.folder)
        (returncode, stdoutdata, stderrdata) = rsync.rsync(
            rsync_cmd,
            source,
            destination,
            link_dest,
            new_backup.rsync_args,
            new_backup.rsyncfilter,
            new_backup.rsync_logfile_options)
        if returncode != 0:
            print(stderrdata)
            print("rsync FAILED. aborting")
            sys.exit(EXIT_RSYNC_FAILED)


def handle_expired_backups(repository):
    expired_backups = repository.get_expired_backups()
    if len(expired_backups) > 0:
        for expired_backup in expired_backups:
            # as a backup might be a symlink to another backup, we have to
            # consider: when it is a symlink, just remove the symlink. if not,
            # other backupSSS!! might be a symlink to it, so we have to check
            # all other backups. we overwrite one symlink with the backup and
            # update all remaining symlinks
            print("expired:", expired_backup.name)
            expired_path = os.path.join(repository.destination,
                                        expired_backup.name)
            if os.path.islink(expired_path):
                remove_symlink(expired_path)
            else:
                symlinks = []
                for backup in repository.backups:
                    backup_path = os.path.join(repository.destination,
                                               backup.name)
                    if (os.path.samefile(expired_path,
                                         os.path.realpath(backup_path))
                            and os.path.islink(backup_path)):
                        symlinks.append(backup)

                if len(symlinks) == 0:
                    # just remove the backups, no symlinks present
                    remove_recursive(os.path.join(
                        repository.destination, expired_backup.name))
                else:
                    # replace the first symlink with the backup
                    symlink_path = os.path.join(repository.destination,
                                                symlinks[0].name)
                    remove_symlink(symlink_path)

                    # move the real backup over
                    move(expired_path, symlink_path)

                    # now update all symlinks to the directory
                    for remaining_symlink in symlinks[1:]:
                        remaining_symlink_path = os.path.join(
                            repository.destination,
                            remaining_symlink.name)
                        remove_symlink(remaining_symlink)
                        create_symlink(expired_path, remaining_symlink_path)
    else:
        print("no expired backups")


def remove_symlink(path):
    # to remove a symlink, we have to strip the trailing
    # slash from the path
    args = ["rm", path.rstrip("/")]
    subprocess.check_call(args)


def create_symlink(path, target):
    args = ["ln", "-s", "-r", path, target]
    print(args)
    subprocess.check_call(args)


def move(path, target):
    args = ["mv", path, target]
    subprocess.check_call(args)


def remove_recursive(path):
    args = ["rm", "-r", "-f", path]
    subprocess.check_call(args)


def copy_hardlinks(path, target):
    # we could alternatively use rsync with destination
    # being the same as link-dest, this would create
    # only hardlinks, too
    args = ["cp", "-a", "-l", path, target]
    subprocess.check_call(args)


def is_backup_folder(name):
    if BACKUP_REGEX.match(name):
        return True
    else:
        print("%s is not a backup folder" % name)
        return False


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

    def get_backup_params(self, new_backup_interval_name):
        new_link_ref = self._get_latest_backup()
        new_link_ref = new_link_ref.name if new_link_ref is not None else None
        new_folder = "%s_%s_%s%s" % (self.name,
                                     datetime.datetime.now().strftime(
                                         "%Y-%m-%dT%H:%M:%S"),
                                     new_backup_interval_name, BACKUP_SUFFIX)

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

            backups_of_that_interval = [backup for backup in self.backups if
                backup.interval_name == interval_name]

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

if __name__ == '__main__':
    run(sys.argv[1])
