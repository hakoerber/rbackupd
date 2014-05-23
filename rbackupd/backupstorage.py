# -*- encoding: utf-8 -*-
# Copyright (c) 2014 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
This module provides classes to interact with locations where a backup can be
stored.

The abstract class :class:`BackupStorage` provides the interface for all
classes that are used to represent backup locations.

The class :class:`BackupFolder` represents a backup location in the local file
system. The structure looks like this::

    path ---+--- <metadata file>
            |
            +--- <data subfolder> ---+--- <copied source 1>
                                     |
                                     +--- <copied source 2>
                                     |
                                     ...

The metadata file contains the following information about the project:
    - the name of the backup
    - the date of the backup
    - the interval the backup belongs to

The access the metadata file, a separate class :class:`BackupMetadataFile` is
used. It is responsible for actually reading, writing and parsing the metadata
file so the BackupFolder class does not have to care about its layout.

The data subfolder contains the actual content of the backup. This is where
the files that should be backed up have to be stored.

The class could be used like this to read already existing backups::

    import backupstorage

    folder = backupstorage.BackupFolder("/path/to/a/backup")

    # read the metadata from the metadata file
    folder.load_metadata()

    date = folder.date
    name = folder.name
    interval_name = interval_name

    if folder.is_finished():
        # save the backup for later use
        pass
    else:
        # discard the backup as it is not valid
        pass

    # this is the path to the saved data
    content_path = folder.data_path

For creating a new backup the class could be used like this::

    import backupstorage

    newfolder = backupstorage.BackupFolder("/path/to/new/backup")

    # prepare the folder so data can be copied into it
    newfolder.prepare()

    # actually copy the data into the backup
    copy(your_backup_source, newfolder.data_path)

    # tell the folder about the metadata
    newfolder.set_metadata(name=my_backup_name,
                           date=backup_creation_time,
                           interval_name=my_backup_interval)

    # save the metadata and mark the backup as finished
    newfolder.finish()


"""

import os
import datetime
import logging
import functools

from rbackupd import constants as const
from rbackupd import files

logger = logging.getLogger(__name__)


def _only_unfinished(func):
    """
    Wrap functions that must not be called on a finished backup.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.is_finished():
            raise BackupStorageIllegalOperationError(
                self,
                "you cannot perform this operation on a finished backup")
        return func(self, *args, **kwargs)
    return wrapper


class BackupStorage(object):
    """
    Abstract class that represents a location where a backup can be stored
    including meta information about that backup.
    """
    def __init__(self):
        self._name = None
        self._date = None
        self._interval_name = None

    def load_metadata(self):
        raise NotImplementedError()

    def set_metadata(self, name, date, interval_name):
        raise NotImplementedError()

    def prepare(self):
        raise NotImplementedError()

    def finish(self):
        raise NotImplementedError()

    def is_finished(self):
        raise NotImplementedError()

    def link_data_from(self, storage):
        raise NotImplementedError()

    def data_is_link(self):
        raise NotImplementedError()

    def data_is_link_to(self, storage):
        raise NotImplementedError()

    @property
    def date(self):
        raise NotImplementedError()

    @property
    def name(self):
        raise NotImplementedError()

    @property
    def interval_name(self):
        raise NotImplementedError()

    @property
    def folder(self):
        raise NotImplementedError()

    @property
    def data_path(self):
        raise NotImplementedError()


class BackupFolder(BackupStorage):
    """
    Represents a folder containing a single backup of a task. The structure
    looks like this::

        path ---+--- <metadata file>
                |
                +--- <backup subfolder> ---+--- <copied source 1>
                                           |
                                           +--- <copied source 2>
                                           |
                                           ...

    The metadata file contains the following information about the project:
        - the name of the backup
        - the date of the backup
        - the interval the backup belongs to

    The backup subfolder contains the actual content of the backup.

    :param path: The path to the folder.
    :type path: str
    """

    def __init__(self, path):
        BackupStorage.__init__(self)
        self._path = path
        self.meta_file = BackupMetadataFile(
            os.path.join(self.path, const.NAME_META_FILE))

    def _read_meta_file(self):
        """
        Read the metadata file in the backup folder and makes the info
        available in the attributes.

        :raise InvalidBackupError: if the backup is invalid, which means it
            does not contain a metadata file or the metadata file is invalid.
        """
        if not self.meta_file.exists():
            raise InvalidBackupError(self.path, "metadata file not found")
        logger.debug("Reading metadata file of backup \"%s\".", self.path)
        try:
            self.meta_file.read()
        except IOError as error:
            raise InvalidBackupError(
                self.path,
                "metadata file could not be read: %s" % str(error))
        self.date = self.meta_file.date
        self.name = self.meta_file.name
        self.interval_name = self.meta_file.interval

    def load_metadata(self):
        """
        Loads the metadata of the folder.

        :raise InvalidBackupError: if the backup is invalid, which means it
            does not contain a metadata file or the metadata file is invalid.
        """
        self._read_meta_file()

    @_only_unfinished
    def _write_meta_file(self):
        """
        Write the information to the metadata file.

        .. note:: You cannot perform this operation on an unfinished backup.

        :raise BackupStorageIllegalOperationError:
            if you try this operation on an unfinised backup
        """
        self.meta_file.write()

    @_only_unfinished
    def set_metadata(self, name, date, interval_name):
        """
        Set the meta data of the backup folder. All existing data will be
        overwritten. Note that the metadata is not automatically saved in the
        backup.

        .. note:: You cannot perform this operation on an unfinished backup.

        :param name: The name of the backup.
        :type name: str

        :param date: The date the backup was created.
        :type date: datetime instance

        :param interval: The interval this backup belongs to
        :type interval: str

        :raise BackupStorageIllegalOperationError:
            if you try this operation on an unfinised backup
        """
        self.name = name
        self.date = date
        self.interval_name = interval_name
        self.meta_file.set_info(name, date, interval_name)

    @_only_unfinished
    def prepare(self):
        """
        Prepare the backup folder so that files can be copied into it.

        .. note:: You cannot perform this operation on an unfinished backup.

        :raise BackupStorageIllegalOperationError:
            if you try this operation on an unfinised backup

        :raise IOError:
            if the folder could not be prepared
        """
        logger.debug("Preparing backup folder \"%s\".", self.path)
        try:
            if not os.path.exists(self.path):
                os.mkdir(self.path)
        except IOError:
            raise

    @_only_unfinished
    def finish(self):
        """
        Mark the backup as finished and save the metadata. After that, you
        cannot change the metadata anymore.

        .. note:: You cannot perform this operation on an unfinished backup.

        :raise BackupStorageIllegalOperationError:
            if you try this operation on an unfinised backup
        """
        self._write_meta_file()

    def is_finished(self):
        """
        Determine whether the backup folder contains a valid, finished backup.

        :rtype: bool
        """
        if not os.path.exists(self.path):
            return False
        content = os.listdir(self.path)
        return (const.NAME_META_FILE in content and
                const.NAME_BACKUP_SUBFOLDER in content)

    @_only_unfinished
    def link_data_from(self, storage):
        """
        Link the data from the given backup storage into this folder. The
        backup to link to has to be finished.

        :param storage: The storage to link to.
        :type storage: BackupStorage instance

        :raise BackupStorageIllegalOperationError:
            if you try this operation on an unfinised backup
        """
        if not storage.is_finished():
            raise ValueError("the backup to link to has to be finished")
        link_target = storage.data_path
        link_name = self.data_path
        logger.info("Creating symlink \"%s\" pointing to \"%s\"",
                    link_name,
                    link_target)
        files.create_symlink(link_target, link_name)

    def data_is_link(self):
        """
        Determine whether the data the folder contains is a link to another
        backup storage.

        :rtype: bool

        :raise ValueError: if the backup is not finished
        """
        if not self.is_finished():
            raise ValueError("the backup has to be finished")
        return os.path.islink(self.data_path)

    def data_is_link_to(self, storage):
        """
        Determine whether the data of the folder is linked to the data of
        another storage.

        :param storage: The storage that might be the target of the link.
        :type storage: BackupStorage instance

        :rtype: bool

        :raise ValueError: if the backup is not finished
        """
        try:
            is_link = self.data_is_link()
        except ValueError:
            raise
        if not is_link:
            return False
        print(self.data_is_link())
        return (self.data_is_link() and
                os.path.samefile(self.data_path, storage.data_path))

    def remove(self):
        """
        Removes the backup folder.
        """
        logger.info("Removing directory \"%s\".", self.path)
        files.remove_recursive(self.path)

    def remove_data_link(self):
        """
        Remove the data from the backup, but leaves the metadata unchanged. If
        the data is not a link to another storage, this will raise an error.

        :raise ValueError: if the data is not a link to another storage
        """
        logger.info("Removing data link at \"%s\"", self.data_path)
        if not self.data_is_link():
            raise ValueError("the data is not a link")
        files.remove_symlink(self.data_path)

    def move_data_to(self, storage):
        """
        Move the data from this backup to the specified storage. The folder has
        to be finished and the storage to move the data to must not.
        Additionally, the folder must not be a link.

        :param storage: The backup to move the data to.
        :type storage: BackupStorage instance

        :raise ValueError: if the folder is not finished
        :raise ValueError: if the data is a link
        :raise ValueError: if the folder to move to is finished
        """
        if not self.is_finished():
            raise ValueError("the backup has to be finished")
        if self.data_is_link():
            raise ValueError("the backup data is a link")
        if storage.is_finished():
            raise ValueError("the target backup must not be finshed")
        logger.debug("Moving data from folder \"%s\" to folder \"%s\"",
                     self.path,
                     storage.path)
        files.move(self.data_path, storage.data_path)

    @property
    def date(self):
        """
        The date of the creation of the backup.
        """
        return self._date

    @date.setter
    def date(self, value):
        self._date = value

    @property
    def name(self):
        """
        The name of the backup.
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def interval_name(self):
        """
        The name of the interval the backup belongs to.
        """
        return self._interval_name

    @interval_name.setter
    def interval_name(self, value):
        self._interval_name = value

    @property
    def folder(self):
        """
        The name of the folder.
        """
        return os.path.basename(self.path)

    @property
    def data_path(self):
        """
        The path to the backup data. This is where the actual backup is stored.
        """
        return os.path.join(self.path, const.NAME_BACKUP_SUBFOLDER)

    @property
    def path(self):
        """
        The path to the folder.
        """
        return self._path


class BackupMetadataFile(object):
    """
    Represents the metadata file containing information about a specific backup
    contained in the backup folder.

    :param path: The path to the metadata file.
    :type path: str
    """

    def __init__(self, path):
        self.path = path
        self.name = None
        self.date = None
        self.interval = None

    def read(self):
        """
        Read the metadata file and parse its content.

        :raise IOError: if the file could not be read
        :raise InvalidMetaFile: if the file does not adhere to the metadata file
                                structure

        """
        logger.debug("Reading metadata file \"%s\".", self.path)
        try:
            lines = open(self.path).readlines()
        except IOError:
            raise
        logger.debug("Content: %s.", lines)

        if len(lines) != const.META_FILE_LINES:
            raise InvalidMetaFileError(self.path, "invalid number of lines")
        self.name = lines[const.META_FILE_INDEX_NAME].strip()
        logger.debug("Name set to \"%s\".", self.name)
        try:
            self.date = self._unpack_date(
                lines[const.META_FILE_INDEX_DATE].strip())
        except ValueError as error:
            message = str(error)
            raise InvalidMetaFileError(self.path, message)
        logger.debug("Date set to \"%s\".", self.date.isoformat())
        self.interval = lines[const.META_FILE_INDEX_INTERVAL].strip()
        logger.debug("Interval set to \"%s\".", self.interval)

    def set_info(self, name, date, interval):
        """
        Set the information saved in the metadata file.

        :param name: The name of the backup
        :type name: str

        :param date: The date of the backup
        :type date: datetime instance

        :param interval: The interval of the backup
        :type interval: str
        """
        self.name = name
        self.date = date
        self.interval = interval

    def write(self):
        """
        Writes the information into the metadata file.
        """
        logger.debug("Writing metadata file \"%s\".", self.path)
        content = self._get_string()
        logger.debug("Content to write:\n\"%s\".", content)
        with open(self.path, 'w') as file:
            file.write(content)

    def _get_string(self):
        """
        Returns a string representing the information of the backup that
        can be directly written into the metadata file.

        :rtype: str
        """
        content = [None] * const.META_FILE_LINES
        content[const.META_FILE_INDEX_NAME] = self.name
        content[const.META_FILE_INDEX_DATE] = self._pack_date(self.date)
        content[const.META_FILE_INDEX_INTERVAL] = self.interval
        ret = "\n".join([str(f) for f in content]) + "\n"
        return ret

    def _unpack_date(self, content):
        """
        Converts a string found in a metadata file into a datetime object.

        :param content: The string to convert.
        :type content: str

        :rtype: datetime instance

        :raise ValueError: if the date could not be packed
        """
        try:
            ret = datetime.datetime.strptime(content,
                                             const.META_FILE_DATE_FORMAT)
        except ValueError:
            raise
        return ret

    def _pack_date(self, date):
        """
        Converts the datetime object into a string representation suitable for
        being stored into a metadata file.

        :param date: The date object to convert.
        :type date: datetime instance

        :rtype: str
        """
        return date.strftime(const.META_FILE_DATE_FORMAT)

    def exists(self):
        """
        Determine whether the metadata file exists.

        :rtype: bool
        """
        return os.path.exists(self.path)


class InvalidBackupError(Exception):
    """
    Error that is raised when a backup folder is not valid.

    :param path: The path of the invalid backup.
    :type path: str

    :param message: A message with more specific information about the error.
    :type message: str
    """

    def __init__(self, path, message):
        Exception.__init__()
        self.path = path
        self.message = message


class InvalidMetaFileError(Exception):
    """
    This error is raised when the the reading of a metadata file fails due to
    the metadata file not following the metadata file structure or containing
    invalid values.

    :param path: The path of the metadata file.
    :type path: str

    :param message: A message with more specific information about the error.
    :type message: str
    """
    def __init__(self, path, message):
        Exception.__init__()
        self.path = path
        self.message = message


class BackupStorageIllegalOperationError(Exception):
    """
    This error is raised when an illegal operation is tried on a backup folder,
    e.g. trying to change the meta data of an already finished backup.

    :param backup_storage: The backup storage the operation was tried on.
    :type backup_storage: BackupStorage instance

    :param message: A message with more specific information about the error.
    :type message: str
    """
    def __init__(self, backup_storage, message):
        Exception.__init__()
        self.backup_storage = backup_storage
        self.message = message
