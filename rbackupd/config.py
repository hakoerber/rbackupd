import os
import collections


class ParseError(Exception):

    def __init__(self, line):
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
        return _is_comment(line) or _is_section(line) or _is_key_value(line)

    def _parse(self):
        section = None
        for line in self._file:
            line = line.strip()
            if len(line) == 0 or self._is_comment(line):
                continue
            elif self._is_section(line):
                section = [None, None]
                section[0] = self._parse_section(line)
                section[1] = collections.OrderedDict()
                self._structure.append(section)
            elif self._is_key_value(line):
                if section is None:
                    raise ParseError(line)
                (key, tag, value) = self._parse_key_value(line)
                if tag is None:
                    if not key in section[1]:
                        section[1][key] = [value]
                    else:
                        section[1][key].append(value)
                else:
                    if not key in section[1]:
                        section[1][key] = collections.OrderedDict({tag: value})
                    else:
                        section[1][key][tag] = value
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

if __name__ == "__main__":
    import sys
    config = Config(sys.argv[1])
    #print(config.get_structure())
    #print(config.get_section("noexist"))
    #print(config.get_section("main"))
    #print(config.get_sections("task"))
