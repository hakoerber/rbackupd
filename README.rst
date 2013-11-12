rbackupd
========

rbackupd is a backup program for linux using rsync. It creates "snapshots" of
the filesystem that contain all files and directories of that filesystem at the
time of the snapshot. To reduce the required disk space, files that have not
changed since the last snapshot are hardlinked into the new snapshot.

You can specify multiple intervals in which snapshots will be created, and a
maximum number of backups that should be kept for every interval. Intervals
can be given in a cron-like format, which means you have great flexibility in
specifiying these intervals.

Thanks to rsync, rbackupd will preserve hard links, special files such as named
sockets and fifos, device files, permissions, ownership, modification times,
ACLs and extended attributes.

As the snapshots are neither compressed nor encrypted by rbackupd, every user
can access all files owned by him without requiring root privileges.

rbackupd is written in python, for version 3.3.

Requirements
------------

- a POSIX compatible operating system
- rsync v2.5.7 or later
- python v3.3 or later
- a filesystem supporting hardlinks

Usage
-----

``rbackupd [-c <configuration file>]``

Documentation
-------------

Look into ``doc/`` for more detailed documentation.

Installation
------------

See ``INSTALL`` for installation information.

Authors
-------

See ``AUTHORS`` for a list of authors.

Changelog
---------

See ``CHANGELOG`` for a complete changelog.

License
-------

rbackupd is licensed under the GNU General Public License version 3. See
``LICENSE`` for a copy of the GPL.

Contact
-------

e-mail: hannes.koerber+rbackupd@gmail.com

