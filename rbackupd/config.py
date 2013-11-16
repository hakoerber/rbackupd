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

import os
import collections


class ParseError(Exception):

    def __init__(self, line):
        super(ParseError, self).__init__(line)
        self.line = line


class Config(object):

    def __init__(self, path):
        self.path = path
        self._file = None
        self._read_file()
        self._structure = []
        self._parse()

    def _read_file(self):
        if self._file is not None:
            return
        if not os.path.isfile(self.path):
            raise IOError("File not found.")
        self._file = open(self.path).readlines()

    def _is_section(self, line):
        return line.startswith("[") and line.endswith("]")

    def _is_comment(self, line):
        return line.startswith("#")

    def _is_key_value(self, line):
        if self._is_section(line) or self._is_comment(line):
            return False
        if not "=" in line[1:]:
            return False
        (key, _, value) = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value.isdigit():
            return True
        if value == "":
            return True
        if value.startswith('"') and value.endswith('"'):
            return True
        if value.lower() in ["true", "false", "yes", "no"]:
            return True
        raise ParseError(line)

    def _parse_section(self, line):
        if not self._is_section(line):
            raise ParseError(line)
        return line[1:-1]

    def _parse_key_value(self, line):
        if not self._is_key_value(line):
            raise ParseError(line)
        (key_and_tag, _, value) = line.partition("=")
        value = value.strip()
        key_and_tag = key_and_tag.strip()

        if "[" in key_and_tag and key_and_tag.endswith("]"):
            (key, tag) = key_and_tag.rstrip("]").split("[")
            if not tag.startswith('"') or not tag.endswith('"'):
                raise ParseError(line)
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
        return (key, tag, value)

    def _is_valid(self, line):
        return (self._is_comment(line) or
                self._is_section(line) or
                self._is_key_value(line))

    def _is_empty(self, line):
        return len(line) == 0

    def _parse(self):
        current_section = None
        lineno = 0
        for line in self._file:
            lineno += 1
            line = line.strip()
            if self._is_empty(line) or self._is_comment(line):
                continue
            elif self._is_section(line):
                current_section = [None, None]
                current_section[0] = self._parse_section(line)
                current_section[1] = collections.OrderedDict()
                self._structure.append(current_section)
            elif self._is_key_value(line):
                if current_section is None:
                    raise ParseError(line)
                (key, tag, value) = self._parse_key_value(line)
                if tag is None:
                    if not key in current_section[1]:
                        current_section[1][key] = [value]
                    else:
                        current_section[1][key].append(value)
                else:
                    if not key in current_section[1]:
                        current_section[1][key] = collections.OrderedDict(
                            {tag: value})
                    else:
                        current_section[1][key][tag] = value
            else:
                raise ParseError(line)

    def get_structure(self):
        return self._structure

    def get_section(self, name):
        return self.get_sections(name)[0]

    def get_sections(self, name):
        sections = []
        for section in self._structure:
            if section[0] == name:
                sections.append(section[1])
        if len(sections) == 0:
            return None
        return sections
