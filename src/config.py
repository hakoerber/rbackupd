import os

class ParseError(Exception):
    pass

class Config(object):

    def __init__(self, path):
        self.path = path
        self._file = None
        self._read_file()
        self._structure = []
        self._parse()

    def _read_file(self):
        if not self._file == None:
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
        (key, value) = line.split("=")
        key = key.strip()
        value = value.strip()
        if not (value.startswith('"') or not value.endswith('"')) and not value == "":
            print('"',value,'"', "is invalid")
            return False
        return True

    def _parse_section(self, line):
        if not self._is_section(line):
            raise ParseError()
        return line[1:-1]

    def _parse_key_value(self, line):
        if not self._is_key_value(line):
            raise ParseError()
        (key_and_tag, value) =  line.split("=")
        value = value.strip()
        key_and_tag = key_and_tag.strip()

        if "[" in key_and_tag and key_and_tag.endswith("]"):
            (key, tag) = key_and_tag.rstrip("]").split("[")
            if not tag.startswith('"') or not tag.endswith('"'):
                raise ParseError()
            tag = tag[1:-1]
        else:
            tag = None
            key = key_and_tag
        if value.isdigit():
            value = int(value)
        elif value.lower() in ["true"]:
            value = True
        elif value.lower() in ["false"]:
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
                section[1] = {}
                self._structure.append(section)
            elif self._is_key_value(line):
                if section == None:
                    raise ParseError()
                (key, tag, value) = self._parse_key_value(line)
                if tag is None:
                    if not key in section[1]:
                        section[1][key] = [value]
                    else:
                        section[1][key].append(value)
                else:
                    if not key in section[1]:
                        section[1][key] = {tag: value}
                    else:
                        section[1][key].append({tag: value})
            else:
                raise ParseError()

    def get_structure(self):
        return self._structure

    def get_section(self, name):
        for section in self._structure:
            if section[0] == name:
                return section[1]
        return None

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
