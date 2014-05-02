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

# Constants for the configuration file.
CONF_SECTION_LOGGING = "logging"
CONF_KEY_LOGFILE_PATH = "logfile"
CONF_KEY_LOGLEVEL = "loglevel"
CONF_SECTION_RSYNC = "rsync"
CONF_KEY_RSYNC_CMD = "cmd"

CONF_SECTION_MOUNT = "mount"
CONF_KEY_PARTITION = "partition"
CONF_KEY_MOUNTPOINT = "mountpoint"
CONF_KEY_MOUNTPOINT_RO = "mountpoint_ro"
CONF_KEY_MOUNTPOINT_OPTIONS = "mountpoint_options"
CONF_KEY_MOUNTPOINT_RO_OPTIONS = "mountpoint_options"
CONF_KEY_MOUNTPOINT_CREATE = "mountpoint_create"
CONF_KEY_MOUNTPOINT_RO_CREATE = "mountpoint_ro_create"

CONF_KEY_RSYNC_LOGFILE = "rsync_logfile"
CONF_KEY_RSYNC_LOGFILE_NAME = "rsync_logfile_name"
CONF_KEY_RSYNC_LOGFILE_FORMAT = "rsync_logfile_format"
CONF_KEY_FILTER_PATTERNS = "filters"
CONF_KEY_INCLUDE_PATTERNS = "includes"
CONF_KEY_EXCLUDE_PATTERNS = "excludes"
CONF_KEY_INCLUDE_FILE = "includefiles"
CONF_KEY_EXCLUDE_FILE = "excludefiles"
CONF_KEY_CREATE_DESTINATION = "create_destination"
CONF_KEY_ONE_FILESYSTEM = "one_fs"
CONF_KEY_RSYNC_ARGS = "rsync_args"
CONF_KEY_SSH_ARGS = "ssh_args"

CONF_SECTION_TASKS = "tasks"
CONF_KEY_DESTINATION = "destination"
CONF_KEY_SOURCE = "sources"
CONF_KEY_TASKNAME = "name"

CONF_SECTION_INTERVALS = "intervals"
CONF_SECTION_KEEP = "keep"
CONF_SECTION_AGE = "age"


# Exit codes.
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
EXIT_MOUNTPOINT_DOES_NOT_EXIST = 13
EXIT_ERROR_GENERAL = 14
EXIT_KEYBOARD_INTERRUPT = 130


# The name of the symlink to the latest backup.
SYMLINK_LATEST_NAME = "latest"


# The default rsync command, can be overwritten in the configuration file.
DEFAULT_RSYNC_CMD = "rsync"


# The ssh command
SSH_CMD = "ssh"


NAME_META_FILE = "rbackupd.info"
NAME_BACKUP_SUBFOLDER = "backup"
PATTERN_BACKUP_FOLDER = "%s_%s_%s.snapshot"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

META_FILE_LINES = 3
META_FILE_INDEX_NAME = 0
META_FILE_INDEX_DATE = 1
META_FILE_INDEX_INTERVAL = 2

META_FILE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


# logfile options
LOGFILE_MAX_BYTES = 1000000
LOGFILE_BACKUP_COUNT = 9


DEFAULT_PATH_CONFIG = "/etc/rbackupd/rbackupd.conf"
DEFAULT_SCHEME_PATH = "/usr/share/rbackupd/scheme.ini"


BUS_NAME="org.rbackupd.daemon"
BUS_PATH="/org/rbackupd/daemon"
