.. include:: global.rst

Introduction
============

|appname| is a backup program for linux using
`rsync <http://rsync.samba.org/>`_. It creates "snapshots" of the filesystem
that contain all files and directories of that filesystem at the time of the
snapshot. To reduce the required disk space, files that have not changed since
the last snapshot are hardlinked into the new snapshot.

You can specify multiple intervals in which snapshots will be created, and a
maximum number of snapshots that should be kept for every interval. Intervals
can be given in a
`cron <https://en.wikipedia.org/wiki/Cron#CRON_expression>`_-like format,
which means you have great flexibility in specifying these intervals.

Thanks to rsync, |appname| will preserve hardlinks, special files such as named
sockets and fifos, device files, permissions, ownership, modification times,
ACLs and extended attributes.

As the snapshots are neither compressed nor encrypted by |appname|, every user
can access all files owned by him without requiring root privileges.

|appname| is written in python, for version 3.

Requirements
------------

- a POSIX compatible operating system
- **rsync** v2.5.7 or later
- **python** v3.3 or later
- a filesystem supporting hardlinks

Installation
------------

Look :ref:`here <install>` for a guide about installing |appname|.

Usage
-----

Type ``rbackupd --help`` to get a list of all available commands. Also look
:ref:`here <running>` for help with an initial setup and :ref:`here <config>`
for help with the configuration file.

Issue Tracker
-------------

|appname| uses the `Issue Tracker on GitHub <http://github.com/whatevsz/
rbackupd/issues>`_. Look also :ref:`here <issues>`. Don't hesitate to file bugs
or add feature requests!

Contributing
------------

Look :ref:`here <contributing>` for a guide about how to contribute to
|appname|.

Changelog
---------

Look :ref:`here <changes>` for a complete changelog.

License
-------

|appname| is licensed under the GNU General Public License version 3. See
:download:`LICENSE <../../../LICENSE>` for a copy of the GPL or
`here <http://www.gnu.org/licenses/gpl-3.0.txt>`_ for an online version.

Contact
-------

e-mail: hannes.koerber+rbackupd@gmail.com
