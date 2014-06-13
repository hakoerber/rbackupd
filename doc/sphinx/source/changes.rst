.. include:: global.rst

.. _changes:

Changelog
=========

v0.1 - *2013-10-09*
-------------------

+ Initial release.

v0.2 - *2013-11-10*
-------------------

+ [NEW] Option to automatically mount devices on startup.
+ [NEW] Dynamic handling of overlapping backups.

+ [FIXED] Various little and serious bugs.

v0.3 - *2013-11-25*
-------------------

+ [NEW] A symlink called "latest" that always points to the latest snapshot.
+ [NEW] A "keep_age" option in the configuration file that determines the maximum age of a snapshot before it is deleted.
+ [NEW] Logging implemented.

+ [FIXED] The [mount] section can now be omitted when no mounting should be done.

v0.4 - *2013-12-10*
-------------------

+ [NEW] Log messages added and extended.

+ [CHANGED] The backup folder structure is now more flexible.
+ [CHANGED] The options for overlapping backups were dropped, backups are now always symlinked together.

+ [FIXED] Serious bug that might wrongly delete backups in december.

v0.5 - *2014-05-31*
-------------------

+ [NEW] Runnable with systemd.
+ [NEW] D-Bus interface to interact with the daemon.

+ [REMOVED] Automatically mounting devices is no longer supported.

+ [CHANGED] The structure of the configuration file changed.

+ [FIXED] Various little and serious bugs.
