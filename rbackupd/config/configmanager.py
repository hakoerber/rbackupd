# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import logging
import configobj
import validate

logger = logging.getLogger(__name__)


class ConfigManager(configobj.ConfigObj):
    """
    This class is derived from ConfigObj and validates the configuration file
    automatically.

    :param path: The path to the configuration file.
    :type path: str

    :param configspec: The path to the configspec describing the structure of
                       the configuration file. Consult the configobj
                       documentation for details.
    :type path: str

    :raise ValidationError: if the validation fails
    :raise IOError: if the configuration file or the configspec is not found
    """

    def __init__(self, path, configspec):
        configobj.ConfigObj.__init__(
            self,
            infile=path,
            list_values=True,
            create_empty=False,
            file_error=True,
            interpolation=False,
            raise_errors=True,
            configspec=configspec,
            write_empty_values=True)

        logger.debug("Validating configuration file.")
        validator = validate.Validator()
        try:
            result = self.validate(validator, preserve_errors=True)
        except IOError:
            raise
        if result is not True:
            message = ""
            for entry in configobj.flatten_errors(self, result):
                (sections, key, error) = entry
                expanded_section = ".".join(sections)
                if error is False:
                    message += ("In section \"%s\": key \"%s\" not found\n" %
                                (expanded_section, key))
                else:
                    message += ("In section \"%s\": failed valiation for key "
                                "\"%s\"\n" %
                                (expanded_section, key))
            message = message.rstrip("\n")
            raise ValidationError(message)


class ValidationError(Exception):
    """
    This exception is raised when the validation of the configuration file
    fails.

    :param message: A message with details about how the validation failed.
    :type message: str
    """

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

ConfigError = configobj.ConfigObjError
