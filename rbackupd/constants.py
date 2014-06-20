# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

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

CONF_SECTION_TASKS = "tasks"
CONF_KEY_DESTINATION = "destination"
CONF_KEY_SOURCES = "sources"
CONF_KEY_TASKNAME = "name"

CONF_SECTION_INTERVALS = "intervals"
CONF_SECTION_KEEP = "keep"
CONF_SECTION_AGE = "age"


# Exit codes.
EXIT_RSYNC_FAILED = 1
EXIT_FILE_NOT_FOUND = 2
EXIT_FILE_INVALID = 3
EXIT_CONFIG_FILE_NOT_FOUND = 4
EXIT_NO_CREATE_DESTINATION = 5
EXIT_INVALID_DESTINATION = 6
EXIT_CONFIG_FILE_INVALID = 7
EXIT_DBUS_ACCESS_DENIED = 8

EXIT_ERROR_OTHER = 100

EXIT_KEYBOARD_INTERRUPT = 130


# The name of the symlink to the latest backup.
SYMLINK_LATEST_NAME = "latest"


NAME_META_FILE = "rbackupd.info"
NAME_BACKUP_SUBFOLDER = "backup"
PATTERN_BACKUP_FOLDER = "{name}_{date}_{interval_name}.snapshot"
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


DBUS_BUS_NAME = "org.rbackupd.daemon"
DBUS_OBJECT_PATH_BACKUP_MANAGER = "/org/rbackupd/daemon"

LOGGING_CONSOLE_FORMAT = "[{asctime}] [{levelname}] {message}"
LOGGING_CONSOLE_DATE_FORMAT = "%H:%M:%S"
LOGGING_FILE_FORMAT = "[{asctime}] [{levelname}] {filename}: {message}"
LOGGING_FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
