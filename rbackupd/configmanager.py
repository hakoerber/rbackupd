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
