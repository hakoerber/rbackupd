import datetime
import os.path

import yaml

from . import StorageManager, Backup

class FilesystemStorageManager(StorageManager):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self._path = kwargs["path"]
        self._backups = self._get_backups()
        self.type = "filesystem"

    def allocate(self, name, metadata):
        newpath = os.path.join(self._path, name)
        assert(not os.path.exists(newpath))
        os.mkdir(newpath)
        new_backup = FilesystemBackup(newpath)
        new_backup.set_metadata(metadata)
        return new_backup

    def _get_backups(self):
        result = []
        for backup in os.listdir(self._path):
            backup_path = os.path.join(self._path, backup)
            result.append(FilesystemBackup(backup_path))
        return result

    @property
    def path(self):
        return self._path

class FilesystemBackup(Backup):
    def __init__(self, path):
        self._path = path
        self._metadata_file = os.path.join(self._path, "metadata.yml")

        super().__init__()

    def get_path(self):
        return self._path

    def _read_metadata(self):
        if os.path.exists(self._metadata_file):
            with open(self._metadata_file) as stream:
                self._metadata = yaml.load(stream)
        else:
            self._metadata = {}

    def _write_metadata(self):
        with open(self._metadata_file, 'w') as stream:
            yaml.dump(self._metadata, stream)
