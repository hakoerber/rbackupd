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

"""
This module is used to parse configuration files of a specific format.

The following lines are allowed:

New section:       [<section name>]
Key-value-pair:    <key>["<tag>"] = <value>
Comment:           #<comment>

All key-value pairs automatically belong to the last defined section. Every
section can contain as many key-value pairs as needed, or none. A file can
contain an arbitary amount of sections. Every key-value pair has to belong to a
section, so the file must not start with a key-value pair. Multiple
sections can have the same name and will be grouped together accordingly.

All comment lines will be ignored. A comment sign not being the first
non-whitespace character of a line will not start a comment, but be interpreted
literally.

Key-value pairs have to above defined format. The tag can be used to give
additional information about a key. A tag cannot be used more than once for
every key in the same section, otherwise the last key with the tag will be
used. If a section contains several keys with the same name, they will all be
saved.

Following value types are supported for values in key-value pairs:

string:            "<value>"
int:               <value>

If a line cannot be parsed, a ParseError will be raised, containing information
about the line the error occured in and why parsing failed.

The file will be parsed into the following datastructure, refered to as the
structure:

[
    [
        <section name> ,
        {
            key:
            [
                value ,
                ...
            ]
            ...
            OR
            key:
            [
                {
                    tag:
                    value
                }
                ...
            ]
            ...
        }
    ],
    ...
]
"""

import collections
import logging
import os

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """
    This class represents an error that occured during the parsing of the
    config file. It holds information about the content of the line and the
    line number where the error occured.
    """

    def __init__(self, msg, line, lineno):
        super(ParseError, self).__init__(msg)
        self.message = msg
        self.line = line
        self.lineno = lineno


class Config(object):
    """
    This class represents a configuration file following the format defined
    above.
    """

    def __init__(self, path):
        """
        :param path: The path of the file.
        :type pat: string
        """
        self.path = path
        self._file = None
        self._read_file()
        self._structure = []
        self._parse()

    def get_structure(self):
        """
        Returns the structure of the file.
        """
        return self._structure

    def get_section(self, name):
        """
        Returns a specific section of the file. If the file contains multiple
        sections with the same name, the first one will be returned. If there
        is no section with that name, None will be returned.
        :param name: The name of the section.
        :type name: string
        """
        return self.get_sections(name)[0]

    def get_sections(self, name):
        """
        Returns all sections with a specific name from the file, or none if
        there is no section with the name present.
        :param name: The name of the section.
        :type name: string
        """
        sections = []
        for section in self._structure:
            if section[0] == name:
                sections.append(section[1])
        if len(sections) == 0:
            return [None]
        return sections

    def _read_file(self):
        logger.debug("Reading file %s", self.path)
        if self._file is not None:
            logger.debug("File already read, will not be read again.")
            return
        if not os.path.isfile(self.path):
            raise IOError("file not found")
        self._file = open(self.path).readlines()

    def _is_section(self, line):
        if line.startswith("[") and line.endswith("]"):
            logger.debug("Line \"%s\" is a section.", line)
            return True
        return False

    def _is_comment(self, line):
        if line.startswith("#"):
            logger.debug("Line \"%s\" is a comment.", line)
            return True
        return False

    def _is_key_value(self, line, lineno):
        if self._is_section(line) or self._is_comment(line):
            return False
        if not "=" in line[1:]:
            return False
        (key, _, value) = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (value.isdigit() or
                value == "" or
                value.startswith('"') and value.endswith('"') or
                value.lower() in ["true", "false", "yes", "no"]):
            logger.debug("Line \"%s\" is a key-value pair.", line)
            return True
        raise ParseError("invalid value", line, lineno)

    def _parse_section(self, line, lineno):
        retval = line[1:-1]
        logger.debug("Parsed line \"%s\" as section \"%s\".", line, retval)
        return retval

    def _parse_key_value(self, line, lineno):
        (key_and_tag, _, value) = line.partition("=")
        value = value.strip()
        key_and_tag = key_and_tag.strip()

        if "[" in key_and_tag and key_and_tag.endswith("]"):
            (key, tag) = key_and_tag.rstrip("]").split("[")
            if not tag.startswith('"') or not tag.endswith('"'):
                raise ParseError("invalid value", line, lineno)
            tag = tag[1:-1]
        else:
            tag = None
            key = key_and_tag
        if value.isdigit():
            value = int(value)
        elif value.lower() in ["true", "yes"]:
            value = True
        elif value.lower() in ["false", "no"]:
            value = False
        elif value == "":
            value = None
        else:
            value = value[1:-1]
        logger.debug("Parsed line \"%s\" as key-value pair with key: \"%s\", "
                     "tag: \"%s\", value: \"%s\".", line, key, tag, value)
        return (key, tag, value)

    def _is_empty(self, line):
        return len(line) == 0

    def _parse(self):
        current_section = None
        lineno = 0
        for line in self._file:
            lineno += 1
            line = line.strip()
            logger.debug("Parsing line %s: \"%s\"", lineno, line)
            if self._is_empty(line) or self._is_comment(line):
                logger.debug("Skipping line because comment or empty.")
                continue
            elif self._is_section(line):
                current_section = [None, None]
                current_section[0] = self._parse_section(line, lineno)
                current_section[1] = collections.OrderedDict()
                logger.debug("Starting new section \"%s\".",
                             current_section[0])
                self._structure.append(current_section)
            elif self._is_key_value(line, lineno):
                if current_section is None:
                    raise ParseError(
                        "key-value pair without corresponding section",
                        line,
                        lineno)
                (key, tag, value) = self._parse_key_value(line, lineno)
                if tag is None:
                    logger.debug("Key-value pair without tag found.")
                    if not key in current_section[1]:
                        logger.debug("Adding new key \"%s\"", key)
                        current_section[1][key] = [value]
                    else:
                        logger.debug("Appending to already existing key "
                                     "\"%s\".", key)
                        current_section[1][key].append(value)
                else:
                    logger.debug("Key-value pair with tag found.")
                    if not key in current_section[1]:
                        logger.debug("Adding new key \"%s\"", key)
                        current_section[1][key] = collections.OrderedDict(
                            {tag: value})
                    else:
                        logger.debug("Appending to already existing key "
                                     "\"%s\".", key)
                        current_section[1][key][tag] = value
            else:
                raise ParseError("invalid line", line, lineno)
