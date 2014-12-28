import datetime

def get_module(name):
    return modules[name]


class Backup(object):
    def __init__(self):
        self._valid = True

        self._read_metadata()

    @property
    def name(self):
        return self._name

    @property
    def metadata(self):
        return self._metadata

    def _write_metadata(self):
        pass

    def _read_metadata(self):
        pass

    def set_metadata(self, metadata):
        self._metadata = metadata
        self._write_metadata()

    def is_valid(self):
        return self._valid


class StorageManager(object):
    def __init__(self, name):
        self._name = name

    def _get_backups(self, path):
        return []

    @property
    def name(self):
        return self._name

from . import filesystem

modules = {
    "filesystem": filesystem.FilesystemStorageManager
}
