# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import functools
import logging

from rbackupd import constants as const
from rbackupd.config import configmanager

logger = logging.getLogger(__name__)

LOGLEVEL_MAPPING = {
    "quiet"   : logging.WARNING,
    "default" : logging.INFO,
    "verbose" : logging.VERBOSE,
    "debug"   : logging.DEBUG}

LOGLEVEL_VALUES = list(LOGLEVEL_MAPPING.keys())

LOGLEVEL_MAPPING_REVERSE = {v: k for k, v in LOGLEVEL_MAPPING.items()}

LOGLEVEL_VALUES_REVERSE = list(LOGLEVEL_MAPPING_REVERSE.keys())


def _write_config_after(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        retval = func(self, *args, **kwargs)
        print("writing config:")
        print(self.configmanager)
        self.write_config()
        return retval
    return wrapper


class ConfigMapper(object):

    def __init__(self, config_path):
        self.config_path = config_path
        self.configmanager = None

        self.tasks = []

        self.read_config()

    def _sanitize(self, value):
        # this is a bit ugly but necessary. if there is not value specified
        # for a list in the configuration file (like this: "include ="),
        # instead of returning an empty list configobj returns [''], which
        # we have to convert into an empty list manually
        if (isinstance(value, list)
                and len(value) == 1
                and len(value[0]) == 0):
            value = []
        return value


    def read_config(self, reload=False):
        """
        Reads the configuration file specified in the constructor. By default
        it will not re-read the configuration file if it was already read.

        :param reload: If True, forces a re-read of the configuration file
                       even when it was already read. Defaults to False.
        :type reload: bool
        """
        if (self.configmanager is not None and
                not reload):
            return
        logger.debug("Starting configuration file parsing.")
        try:
            self.configmanager = configmanager.ConfigManager(
                path=self.config_path, configspec=const.DEFAULT_SCHEME_PATH)

        except IOError as error:
            logger.critical("Error accessing a file: %s", str(error))
            exit(const.EXIT_FILE_NOT_FOUND)
        except configmanager.ValidationError as error:
            logger.critical("The validation of the configuration file failed. "
                            "Message:\n%s", str(error))
            exit(const.EXIT_CONFIG_FILE_INVALID)
        except configmanager.ConfigError as err:
            logger.critical("Invalid config file: error line %s (\"%s\"): %s",
                            err.line_number,
                            err.line,
                            err.msg)
            exit(const.EXIT_CONFIG_FILE_INVALID)
        logger.debug("Config file parsed successfully.")

    def write_config(self):
        """
        Write the configuration file to disk.
        """
        if self.configmanager is None:
            raise ValueError("configuration file has to be read before it can "
                             "be written back")
        self.configmanager.write()


    def reload_config(self):
        """
        Reload the configuration file from the path given at startup.
        """
        if self.configmanager is None:
            raise ValueError("configuration file has to be read before it can "
                             "be reloaded")
        self.configmanager.reload()

    @property
    def logfile_path(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_LOGGING][const.CONF_KEY_LOGFILE_PATH])

    @logfile_path.setter
    @_write_config_after
    def logfile_path(self, value):
        self.configmanager[const.CONF_SECTION_LOGGING][
            const.CONF_KEY_LOGFILE_PATH] = value

    @property
    def loglevel(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_LOGGING][const.CONF_KEY_LOGLEVEL])

    @loglevel.setter
    @_write_config_after
    def loglevel(self, value):
        self.configmanager[
            const.CONF_SECTION_LOGGING][const.CONF_KEY_LOGLEVEL] = value

    @property
    def loglevel_as_int(self):
        return LOGLEVEL_MAPPING[self.loglevel]



    @property
    def rsync_command(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_RSYNC][const.CONF_KEY_RSYNC_CMD])

    @rsync_command.setter
    @_write_config_after
    def rsync_command(self, value):
        self.configmanager[const.CONF_SECTION_RSYNC][
            const.CONF_KEY_RSYNC_CMD] = value

    @property
    def default_rsync_logfile(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_RSYNC_LOGFILE])

    @default_rsync_logfile.setter
    @_write_config_after
    def default_rsync_logfile(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_RSYNC_LOGFILE] = value

    @property
    def default_rsync_logfile_name(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_RSYNC_LOGFILE_NAME])

    @default_rsync_logfile_name.setter
    @_write_config_after
    def default_rsync_logfile_name(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_RSYNC_LOGFILE_NAME] = value

    @property
    def default_rsync_logfile_format(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_RSYNC_LOGFILE_FORMAT])

    @default_rsync_logfile_format.setter
    @_write_config_after
    def default_rsync_logfile_format(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_RSYNC_LOGFILE_FORMAT] = value

    @property
    def default_filters(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_FILTER_PATTERNS])

    @default_filters.setter
    @_write_config_after
    def default_filters(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_FILTER_PATTERNS] = value

    @property
    def default_includes(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_INCLUDE_PATTERNS])

    @default_includes.setter
    @_write_config_after
    def default_includes(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_INCLUDE_PATTERNS] = value

    @property
    def default_include_files(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_INCLUDE_FILE])

    @default_include_files.setter
    @_write_config_after
    def default_include_files(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_INCLUDE_FILE] = value

    @property
    def default_excludes(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_EXCLUDE_PATTERNS])

    @default_excludes.setter
    @_write_config_after
    def default_excludes(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_EXCLUDE_PATTERNS] = value

    @property
    def default_exclude_files(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_EXCLUDE_FILE])

    @default_exclude_files.setter
    @_write_config_after
    def default_exclude_files(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_EXCLUDE_FILE] = value

    @property
    def default_create_destination(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_CREATE_DESTINATION])

    @default_create_destination.setter
    @_write_config_after
    def default_create_destination(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_CREATE_DESTINATION] = value

    @property
    def default_one_filesystem(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_ONE_FILESYSTEM])

    @default_one_filesystem.setter
    @_write_config_after
    def default_one_filesystem(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_ONE_FILESYSTEM] = value

    @property
    def default_rsync_args(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_RSYNC_ARGS])

    @default_rsync_args.setter
    @_write_config_after
    def default_rsync_args(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_RSYNC_ARGS] = value

    @property
    def default_ssh_args(self):
        return self._sanitize(self.configmanager[
            const.CONF_SECTION_TASKS][const.CONF_KEY_SSH_ARGS])

    @default_ssh_args.setter
    @_write_config_after
    def default_ssh_args(self, value):
        self.configmanager[const.CONF_SECTION_TASKS][
            const.CONF_KEY_SSH_ARGS] = value

    class TaskSubsection(object):
        def __init__(self, outer, name):
            self.outer = outer
            self.name = name

            self.section_dict = outer.configmanager[const.CONF_SECTION_TASKS][
                name]
            self.write_config = outer.write_config
            self.configmanager = outer.configmanager

        @property
        def rsync_logfile(self):
            value = self.section_dict[
                const.CONF_KEY_RSYNC_LOGFILE]
            if value is None:
                return self.outer.default_rsync_logfile
            return value

        @rsync_logfile.setter
        @_write_config_after
        def rsync_logfile(self, value):
            self.section_dict[
                const.CONF_KEY_RSYNC_LOGFILE] = value

        @property
        def rsync_logfile_name(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_RSYNC_LOGFILE_NAME])
            if value is None:
                return self.outer.default_rsync_logfile_name
            return value

        @rsync_logfile_name.setter
        @_write_config_after
        def rsync_logfile_name(self, value):
            self.section_dict[
                const.CONF_KEY_RSYNC_LOGFILE_NAME] = value

        @property
        def rsync_logfile_format(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_RSYNC_LOGFILE_FORMAT])
            if value is None:
                return self.outer.default_rsync_logfile_format
            return value

        @rsync_logfile_format.setter
        @_write_config_after
        def rsync_logfile_format(self, value):
            self.section_dict[
                const.CONF_KEY_RSYNC_LOGFILE_FORMAT] = value

        @property
        def filter_patterns(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_FILTER_PATTERNS])
            if value is None:
                return self.outer.default_filters
            return value

        @filter_patterns.setter
        @_write_config_after
        def filter_patterns(self, value):
            self.section_dict[
                const.CONF_KEY_FILTER_PATTERNS] = value

        @property
        def include_patterns(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_INCLUDE_PATTERNS])
            if value is None:
                return self.outer.default_includes
            return value

        @include_patterns.setter
        @_write_config_after
        def include_patterns(self, value):
            self.section_dict[
                const.CONF_KEY_INCLUDE_PATTERNS] = value

        @property
        def include_files(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_INCLUDE_FILE])
            if value is None:
                return self.outer.default_include_files
            return value

        @include_files.setter
        @_write_config_after
        def include_files(self, value):
            self.section_dict[
                const.CONF_KEY_INCLUDE_FILE] = value

        @property
        def exclude_patterns(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_EXCLUDE_PATTERNS])
            if value is None:
                return self.outer.default_excludes
            return value

        @exclude_patterns.setter
        @_write_config_after
        def exclude_patterns(self, value):
            self.section_dict[
                const.CONF_KEY_EXCLUDE_PATTERNS] = value

        @property
        def exclude_files(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_EXCLUDE_FILE])
            if value is None:
                return self.outer.default_exclude_files
            return value

        @exclude_files.setter
        @_write_config_after
        def exclude_files(self, value):
            self.section_dict[
                const.CONF_KEY_EXCLUDE_FILE] = value

        @property
        def create_destination(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_CREATE_DESTINATION])
            if value is None:
                return self.outer.default_create_destination
            return value

        @create_destination.setter
        @_write_config_after
        def create_destination(self, value):
            self.section_dict[
                const.CONF_KEY_CREATE_DESTINATION] = value

        @property
        def one_filesystem(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_ONE_FILESYSTEM])
            if value is None:
                return self.outer.default_one_filesystem
            return value

        @one_filesystem.setter
        @_write_config_after
        def one_filesystem(self, value):
            self.section_dict[
                const.CONF_KEY_ONE_FILESYSTEM] = value

        @property
        def rsync_args(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_RSYNC_ARGS])
            if value is None:
                return self.outer.default_rsync_args
            return value

        @rsync_args.setter
        @_write_config_after
        def rsync_args(self, value):
            self.section_dict[
                const.CONF_KEY_RSYNC_ARGS] = value

        @property
        def ssh_args(self):
            value = self.outer._sanitize(self.section_dict[
                const.CONF_KEY_SSH_ARGS])
            if value is None:
                return self.outer.default_ssh_args
            return value

        @ssh_args.setter
        @_write_config_after
        def ssh_args(self, value):
            self.section_dict[
                const.CONF_KEY_SSH_ARGS] = value

        @property
        def sources(self):
            return self.outer._sanitize(self.section_dict[
                const.CONF_KEY_SOURCES])

        @sources.setter
        @_write_config_after
        def sources(self, value):
            self.section_dict[const.CONF_KEY_SOURCES] = value

        @property
        def destination(self):
            return self.outer._sanitize(self.section_dict[
                const.CONF_KEY_DESTINATION])

        @destination.setter
        @_write_config_after
        def destination(self, value):
            self.section_dict[const.CONF_KEY_DESTINATION] = value
            #self.outer.configmanager[const.CONF_SECTION_TASKS][
            #    self.name] = self.section_dict

        @property
        def interval_names(self):
            return self.section_dict[const.CONF_SECTION_INTERVALS].keys()

        def get_subsection(self, name):
            return self.section_dict[name]

    def task(self, name):
        return self.TaskSubsection(self, name)

    @property
    def task_names(self):
        return self.configmanager[const.CONF_SECTION_TASKS].sections
