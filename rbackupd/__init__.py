import datetime
import os
import re
import subprocess
import sys
import time

from . import cmd
from . import config
from . import cron
from . import filesystem
from . import repository
from . import rsync

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
EXIT_INVALID_DESTINATION = 10
EXIT_INVALID_CONFIG_FILE = 11
EXIT_NO_MOUNTPOINT_CREATE = 12

SYMLINK_LATEST_NAME = "latest"

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
CONF_KEY_KEEP_AGE = "keep_age"


def run(config_file):
    if not os.path.isfile(config_file):
        if not os.path.exists(config_file):
            print("config file not found")
            sys.exit(EXIT_CONFIG_FILE_NOT_FOUND)
        else:
            print("invalid config file")
            sys.exit(EXIT_INVALID_CONFIG_FILE)

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

    if conf_sections_mounts is None:
        conf_sections_mounts = []

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
            sys.exit(EXIT_NO_MOUNTPOINT_CREATE)

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
            if not conf_create_destination:
                print("destination \"%s\" does not exists, will no be "
                      "created. repository will be skipped." %
                      conf_destination)
                continue
        if not os.path.isdir(conf_destination):
            print("destination \"%s\" not a directory" % conf_destination)
            sys.exit(EXIT_INVALID_DESTINATION)

        if conf_include_files is not None:
            for include_file in conf_include_files:
                if include_file is None:
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
                if exclude_file is None:
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

        ssh_args = []
        if conf_ssh_args is not None:
            ssh_args = ["--rsh", conf_ssh_args]
        conf_rsync_args.extend(ssh_args)

        conf_taskname = task[CONF_KEY_TASKNAME][0]
        conf_task_intervals = task[CONF_KEY_INTERVAL]
        conf_task_keeps = task[CONF_KEY_KEEP]
        conf_task_keep_ages = task[CONF_KEY_KEEP_AGE]

        for i in conf_task_keep_ages.keys():
            conf_task_keep_ages[i] = \
                _interval_to_oldest_datetime(conf_task_keep_ages[i])

        repositories.append(
            repository.Repository(conf_sources,
                                  conf_destination,
                                  conf_taskname,
                                  conf_task_intervals,
                                  conf_task_keeps,
                                  conf_task_keep_ages,
                                  conf_rsyncfilter,
                                  conf_rsync_logfile_options,
                                  conf_rsync_args))

    while True:
        start = datetime.datetime.now()
        for repo in repositories:
            create_backups_if_necessary(repo, conf_overlapping,
                                        conf_rsync_cmd)
            handle_expired_backups(repo, start)

        # we have to get the current time again, as the above might take a lot
        # of time
        now = datetime.datetime.now()
        if now.minute == 59:
            wait_seconds = 60 - now.second
        else:
            nextmin = now.replace(minute=now.minute+1, second=0, microsecond=0)
            wait_seconds = (nextmin - now).seconds + 1
        time.sleep(wait_seconds)


def _interval_to_oldest_datetime(interval):
    result = datetime.datetime.now()
    suffix = interval[-1:]
    value = int(interval[:-1])
    if suffix == "m":
        result = result - datetime.timedelta(minutes=value)
    elif suffix == "h":
        result = result - datetime.timedelta(hours=value)
    elif suffix == "w":
        result = result - datetime.timedelta(weeks=value)
    elif suffix == "d":
        result = result - datetime.timedelta(days=value)
    elif suffix == "M":
        year = (datetime.date.today().year +
                (datetime.date.today().month - value) // 12)
        month = datetime.date.today().month - value % 12
        if month == 0:
            month = 12
        # get the last day of the month by going back one month from the first
        # day of the following month
        last_day_of_month = (datetime.date(year=year, month=month, day=1) -
                             datetime.timedelta(days=1)).day
        day = datetime.date.today().day
        if day > last_day_of_month:
            day = last_day_of_month
        result = result.replace(year=year, month=month, day=day)
    else:
        print("Invalid interval: %s" % interval)
        sys.exit(13)
    return result


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
            timestamp = datetime.datetime.now()
            real_backup = repository.get_backup_params(necessary_backups[0][0],
                                                       timestamp=timestamp)
            create_backup(real_backup, conf_rsync_cmd)
            for backup in necessary_backups[1:]:
                backup = repository.get_backup_params(backup[0], timestamp)
                # real_backup.destination and backup.destination are guaranteed
                # to be identical as they are from the same repository
                source = os.path.join(real_backup.destination,
                                      real_backup.folder)
                destination = os.path.join(real_backup.destination,
                                           backup.folder)
                if conf_overlapping == "hardlink":
                    cmd.copy_hardlinks(source, destination)
                elif conf_overlapping == "symlink":
                    # We should create RELATIVE symlinks with "-r", as the
                    # repository might move, but the relative location of all
                    # backups will stay the same
                    cmd.create_symlink(source, destination)
                else:
                    # panic and run away
                    print("invalid value for overlapping")
                    sys.exit(EXIT_CONFIG_FILE_INVALID)
    else:
        print("no backup necessary")


def create_backup(new_backup, rsync_cmd):
    destination = os.path.join(new_backup.destination,
                               new_backup.folder)
    symlink_latest = os.path.join(new_backup.destination, SYMLINK_LATEST_NAME)
    for source in new_backup.sources:
        if new_backup.link_ref is None:
            link_dest = None
        else:
            link_dest = os.path.join(new_backup.destination,
                                     new_backup.link_ref)
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
    if os.path.islink(symlink_latest):
        cmd.remove_symlink(symlink_latest)
    cmd.create_symlink(destination, symlink_latest)


def handle_expired_backups(repository, current_time):
    expired_backups = repository.get_expired_backups(current_time)
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
                cmd.remove_symlink(expired_path)
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
                    cmd.remove_recursive(os.path.join(
                        repository.destination, expired_backup.name))
                else:
                    # replace the first symlink with the backup
                    symlink_path = os.path.join(repository.destination,
                                                symlinks[0].name)
                    cmd.remove_symlink(symlink_path)

                    # move the real backup over
                    cmd.move(expired_path, symlink_path)

                    # now update all symlinks to the directory
                    for remaining_symlink in symlinks[1:]:
                        remaining_symlink_path = os.path.join(
                            repository.destination,
                            remaining_symlink.name)
                        cmd.remove_symlink(remaining_symlink_path)
                        cmd.create_symlink(symlink_path,
                                           remaining_symlink_path)
    else:
        print("no expired backups")


if __name__ == '__main__':
    run(sys.argv[1])
