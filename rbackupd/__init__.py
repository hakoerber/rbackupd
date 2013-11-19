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

import collections
import datetime
import os
import re
import subprocess
import sys
import time

from . import config
from . import constants as const
from . import cron
from . import files
from . import filesystem
from . import interval
from . import repository
from . import rsync


def run(config_file):
    if not os.path.isfile(config_file):
        if not os.path.exists(config_file):
            print("config file not found")
            sys.exit(const.EXIT_CONFIG_FILE_NOT_FOUND)
        else:
            print("invalid config file")
            sys.exit(const.EXIT_INVALID_CONFIG_FILE)

    conf = config.Config(config_file)

    # this is the [rsync] section
    conf_section_rsync = conf.get_section(const.CONF_SECTION_RSYNC)
    conf_rsync_cmd = conf_section_rsync.get(const.CONF_KEY_RSYNC_CMD, "rsync")

    conf_sections_mounts = conf.get_sections(const.CONF_SECTION_MOUNT)

    # these are the [default] options that can be overwritten in the specific
    # [task] section
    conf_section_default = conf.get_section(const.CONF_SECTION_DEFAULT)
    conf_default_rsync_logfile = conf_section_default.get(
        const.CONF_KEY_RSYNC_LOGFILE, None)
    conf_default_rsync_logfile_name = conf_section_default.get(
        const.CONF_KEY_RSYNC_LOGFILE_NAME, None)
    conf_default_rsync_logfile_format = conf_section_default.get(
        const.CONF_KEY_RSYNC_LOGFILE_FORMAT, None)

    conf_default_filter_patterns = conf_section_default.get(
        const.CONF_KEY_FILTER_PATTERNS, None)

    conf_default_include_patterns = conf_section_default.get(
        const.CONF_KEY_INCLUDE_PATTERNS, None)
    conf_default_exclude_patterns = conf_section_default.get(
        const.CONF_KEY_EXCLUDE_PATTERNS, None)

    conf_default_include_files = conf_section_default.get(
        const.CONF_KEY_INCLUDE_FILE, None)
    conf_default_exclude_files = conf_section_default.get(
        const.CONF_KEY_EXCLUDE_FILE, None)

    conf_default_create_destination = conf_section_default.get(
        const.CONF_KEY_CREATE_DESTINATION, None)

    conf_default_one_filesystem = conf_section_default.get(
        const.CONF_KEY_ONE_FILESYSTEM, None)

    conf_default_rsync_args = conf_section_default.get(
        const.CONF_KEY_RSYNC_ARGS, None)

    conf_default_ssh_args = conf_section_default.get(
        const.CONF_KEY_SSH_ARGS, None)

    conf_default_overlapping = conf_section_default.get(
        const.CONF_KEY_OVERLAPPING, None)

    conf_sections_tasks = conf.get_sections(const.CONF_SECTION_TASK)

    if conf_sections_mounts is None:
        conf_sections_mounts = []

    for mount in conf_sections_mounts:
        if len(mount) == 0:
            continue

        conf_partition = mount[const.CONF_KEY_PARTITION][0]
        conf_mountpoint = mount[const.CONF_KEY_MOUNTPOINT][0]
        conf_mountpoint_ro = mount.get(const.CONF_KEY_MOUNTPOINT_RO, [None])[0]
        conf_mountpoint_options = mount.get(
            const.CONF_KEY_MOUNTPOINT_OPTIONS, [None])[0]
        conf_mountpoint_ro_options = mount.get(
            const.CONF_KEY_MOUNTPOINT_RO_OPTIONS, [None])[0]

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

        conf_mountpoint_create = mount[const.CONF_KEY_MOUNTPOINT_CREATE][0]

        conf_mountpoint_ro_create = mount.get(
            const.CONF_KEY_MOUNTPOINT_RO_CREATE, [None])[0]
        if (conf_mountpoint_ro is not None and
                conf_mountpoint_ro_create is None):
            print("mountpoint_ro_create needed")
            sys.exit(const.EXIT_NO_MOUNTPOINT_CREATE)

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

        if conf_partition.startswith('UUID'):
            uuid = conf_partition.split('=')[1]
            partition_identifier = filesystem.PartitionIdentifier(uuid=uuid)
        elif conf_partition.startswith('LABEL'):
            label = conf_partition.split('=')[1]
            partition_identifier = filesystem.PartitionIdentifier(label=label)
        else:
            partition_identifier = filesystem.PartitionIdentifier(
                path=conf_device)

        partition = filesystem.Partition(partition_identifier,
                                         filesystem="auto")

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
            try:
                partition.mount(mountpoint_ro)
            except filesystem.MountpointInUseError as err:
                print("mountpoint %s already in use" % err.path)

            try:
                mountpoint_ro.bind(mountpoint)
            except filesystem.MountpointInUseError as err:
                print("mountpoint %s already in use" % err.path)
            mountpoint.remount(("rw", "relatime", "noexec", "nosuid"))
        else:
            try:
                partition.mount(mountpoint)
            except filesystem.MountpointInUseError as err:
                print("mountpoint %s already in use" % err.path)

    repositories = []
    for task in conf_sections_tasks:
        # these are the options given in the specific tasks. if none are given,
        # the default values from the [default] sections will be used.
        conf_rsync_logfile = task.get(
            const.CONF_KEY_RSYNC_LOGFILE, conf_default_rsync_logfile)
        conf_rsync_logfile_name = task.get(const.CONF_KEY_RSYNC_LOGFILE_NAME,
                                           conf_default_rsync_logfile_name)[0]
        conf_rsync_logfile_format = task.get(
            const.CONF_KEY_RSYNC_LOGFILE_FORMAT,
            conf_default_rsync_logfile_format)[0]

        conf_filter_patterns = task.get(
            const.CONF_KEY_FILTER_PATTERNS, conf_default_filter_patterns)

        conf_include_patterns = task.get(
            const.CONF_KEY_INCLUDE_PATTERNS, conf_default_include_patterns)
        conf_exclude_patterns = task.get(
            const.CONF_KEY_EXCLUDE_PATTERNS, conf_default_exclude_patterns)

        conf_include_files = task.get(
            const.CONF_KEY_INCLUDE_FILE, conf_default_include_files)
        conf_exclude_files = task.get(
            const.CONF_KEY_EXCLUDE_FILE, conf_default_exclude_files)

        conf_create_destination = task.get(
            const.CONF_KEY_CREATE_DESTINATION, conf_default_create_destination)

        conf_one_filesystem = task.get(
            const.CONF_KEY_ONE_FILESYSTEM, conf_default_one_filesystem)[0]

        conf_rsync_args = task.get(
            const.CONF_KEY_RSYNC_ARGS, conf_default_rsync_args)

        conf_ssh_args = task.get(
            const.CONF_KEY_SSH_ARGS, conf_default_ssh_args)
        conf_ssh_args = const.SSH_CMD + " " + " ".join(conf_ssh_args)

        conf_overlapping = task.get(
            const.CONF_KEY_OVERLAPPING, conf_default_overlapping)[0]

        # these are the options that are not given in the [default] section.
        conf_destination = task[const.CONF_KEY_DESTINATION][0]
        conf_sources = task[const.CONF_KEY_SOURCE]

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
            sys.exit(const.EXIT_INVALID_DESTINATION)

        if conf_include_files is not None:
            for include_file in conf_include_files:
                if include_file is None:
                    continue
                if not os.path.exists(include_file):
                    print("include file \"%s\" not found" % include_file)
                    sys.exit(const.EXIT_INCLUDE_FILE_NOT_FOUND)
                elif not os.path.isfile(include_file):
                    print("include file \"%s\" is not a valid file" %
                          include_file)
                    sys.exit(const.EXIT_INCLUDE_FILE_INVALID)

        if conf_exclude_files is not None:
            for exclude_file in conf_exclude_files:
                if exclude_file is None:
                    continue
                if not os.path.exists(exclude_file):
                    print("exclude file \"%s\" not found" % exclude_file)
                    sys.exit(const.EXIT_EXCULDE_FILE_NOT_FOUND)
                elif not os.path.isfile(exclude_file):
                    print("exclude file \"%s\" is not a valid file" %
                          exclude_file)
                    sys.exit(const.EXIT_EXCLUDE_FILE_INVALID)

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

        conf_taskname = task[const.CONF_KEY_TASKNAME][0]
        conf_task_intervals = task[const.CONF_KEY_INTERVAL]
        conf_task_keeps = task[const.CONF_KEY_KEEP]
        conf_task_keep_age = task[const.CONF_KEY_KEEP_AGE]

        task_keep_age = collections.OrderedDict()
        for (backup_interval, max_age) in conf_task_keep_age.items():
            task_keep_age[backup_interval] = \
                interval.interval_to_oldest_datetime(max_age)

        repositories.append(
            repository.Repository(conf_sources,
                                  conf_destination,
                                  conf_taskname,
                                  conf_task_intervals,
                                  conf_task_keeps,
                                  task_keep_age,
                                  conf_rsyncfilter,
                                  conf_rsync_logfile_options,
                                  conf_rsync_args))

    while True:
        start = datetime.datetime.now()
        for repo in repositories:

            for (backup_interval, max_age) in conf_task_keep_age.items():
                task_keep_age[backup_interval] = \
                    interval.interval_to_oldest_datetime(max_age)
            repo.keep_age = task_keep_age

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


def create_backups_if_necessary(repository, conf_overlapping, conf_rsync_cmd):
    necessary_backups = repository.get_necessary_backups()
    if len(necessary_backups) != 0:
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
                    files.copy_hardlinks(source, destination)
                elif conf_overlapping == "symlink":
                    # We should create RELATIVE symlinks with "-r", as the
                    # repository might move, but the relative location of all
                    # backups will stay the same
                    files.create_symlink(source, destination)
                else:
                    # panic and run away
                    print("invalid value for overlapping")
                    sys.exit(const.EXIT_CONFIG_FILE_INVALID)
    else:
        print("no backup necessary")


def create_backup(new_backup, rsync_cmd):
    destination = os.path.join(new_backup.destination,
                               new_backup.folder)
    symlink_latest = os.path.join(new_backup.destination,
                                  const.SYMLINK_LATEST_NAME)
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
            sys.exit(const.EXIT_RSYNC_FAILED)
    if os.path.islink(symlink_latest):
        files.remove_symlink(symlink_latest)
    files.create_symlink(destination, symlink_latest)


def handle_expired_backups(repository, current_time):
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
                files.remove_symlink(expired_path)
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
                    files.remove_recursive(os.path.join(
                        repository.destination, expired_backup.name))
                else:
                    # replace the first symlink with the backup
                    symlink_path = os.path.join(repository.destination,
                                                symlinks[0].name)
                    files.remove_symlink(symlink_path)

                    # move the real backup over
                    files.move(expired_path, symlink_path)

                    # now update all symlinks to the directory
                    for remaining_symlink in symlinks[1:]:
                        remaining_symlink_path = os.path.join(
                            repository.destination,
                            remaining_symlink.name)
                        files.remove_symlink(remaining_symlink_path)
                        files.create_symlink(symlink_path,
                                             remaining_symlink_path)
    else:
        print("no expired backups")


if __name__ == '__main__':
    run(sys.argv[1])
