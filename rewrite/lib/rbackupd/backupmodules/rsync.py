import datetime
import logging

logger = logging.getLogger(__name__)

class BackupCreator(object):
    def __init__(self, name, **kwargs):
        assert(kwargs["type"] == "rsync")
        self._logfile = kwargs.get("logfile", False)
        self._args = kwargs.get("args", "")
        self._name = name

    def create(self, sources, storage, name, metadata):
        logger.info("Creating new backup \"%s\".", name)
        logger.verbose("Creating new backup named \"%s\" from \"%s\" to storage "
                     "\"%s\" with metadata \"%s\".",
                     name,
                     sources,
                     storage.name,
                     metadata)

        if storage.type == "filesystem":
            destination = storage.allocate(
                name=str(datetime.datetime.now()),
                metadata={"done": False})
            result = self._copy(
                sources,
                destination.get_path())
            if result:
                logger.info("Backup finished.")
                logger.verbose("Backup successfully finished. Marking as done.")
                destination.set_metadata({"done": True})
            return result
        else:
            self._unsupported_storage_module(storage)

    def remove(self, storage, name):
        logger.verbose("Removing backup named \"%s\" from storage \"%s\".",
                       name,
                       storage)
        if isinstance(storage, Filesystem):
            folder = storage.find(name=name)
            if folder is None:
                return False
            return self._delete(folder)
        else:
            self._unsupported_storage_module(storage)

    def get_name(self):
        return self._name

    def _copy(self, sources, path):
        logger.debug("Copying files from \"%s\" to \"%s\".", sources, path)
        return True

    def _delete(self, path):
        logger.debug("Deleting files at \"%s\".", path)
        return True

    def _unsupported_storage_module(self, storage):
        raise TypeError("{0} storage module not supported in {1}".format(
            str(type(storgage),
            str(self))))
