# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import logging
import configobj
import validate

logger = logging.getLogger(__name__)


class ConfigManager(configobj.ConfigObj):

    def __init__(self, path, configspec):
        configobj.ConfigObj.__init__(
            self,
            infile=path,
            list_values=True,
            create_empty=False,
            file_error=True,
            interpolation="template",
            raise_errors=True,
            configspec=configspec,
            write_empty_values=True)

        logger.debug("Validating configuration file.")
        validator = validate.Validator()
        result = self.validate(validator)
        if result:
            logger.debug("Validation successful.")
        else:
            logger.error("Validation failed.")

ConfigError = configobj.ConfigObjError
