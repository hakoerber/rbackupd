.. include:: global.rst

.. _config:

The configuration file
**********************

The configuration file (by default located at ``/etc/rbackupd/rbackupd.conf``)
contains everything |appname| needs in order to know what to do.

:download:`Here <../../../conf/rbackupd.conf>` you can take a look into the
default configuration file that will be installed with |appname|. Most keys have
sensible default values, but you should take a closer look into the ``main``
task section to specify when backups are created and deleted, where the backup
should be stored, and what to back up in the first place.

All keys you encounter in the file have a brief description with them, a more
thorough one can be found in the :ref:`key-list` section for each key.

General format
--------------

You can most likely skip this section as the format should be quite obvious from
the default configuration file. However, in some special cases a look here might
be worth it.

As |appname| uses `ConfigObj <http://github.com/DiffSK/configobj>`_ for config
file parsing, everything from its documentation applies here. Look
`here <http://www.voidspace.org.uk/python/
configobj.html#the-config-file-format>`_
for a complete specification.

The layout of the configuration file is fairly simple and similar to the
popular `.ini <http://en.wikipedia.org/wiki/INI_file>`_ format:

The options are simple key-value-pairs, which key and value separated by an
equal sign. Comments are invoked with the ``#`` sign. Inline comments (on the
same line as a non-comment) are possible, too. So all in all, it looks
like this::

    # comment
    key = value  # inline comment

Note that trailing or preceding whitespace will be stripped, if you want to
conserve it you have to quote the value, see :ref:`quoting` for more detail.

.. _lists:

Lists
+++++

The value of a key-value-pair can also be a list of values. This can be done by
simply separating multiple values by a comma. If a list only contains a single
item, a comma is appended. Here are some examples::

    key = value1, value2, value3
    key = value1,                 # a list with a single item

An empty list is represented by a single comma ::

    key = ,

.. _quoting:

Quoting
+++++++

If a value contains a comma, in order to it not being mistaken for a list, you
have to quote the value. ::

    key = value1, value2          # this is a list
    key = "value1, value2"        # this is a string containing "value1, value2"

    key =  spaceinthebeginning    # the preceding space will be stripped
    key = " spaceinthebeginning"  # is has to look like this to be preserved

You can also quote single items of a list like this::

    key = "value1, value2", value3
    # this will be parsed to a list containing two items:
    # 1 : "value1, value2"
    # 2 : "value3"

Note that you do *not* have to quote whitespace in the middle of a token, so ::

    key = /example path/with whitespace/

if perfectly fine.

If a string contains a line break, it has to be surrounded with triple quotes
(``'''``) which looks like this::

    key = '''this
             contains
             linebreaks'''

This would be parsed as ::

    "this\n             contains\n             linebreaks"

Sections
++++++++

The configuration file is separated into sections and subsections. A section
header is surrounded by square brackets, while the number of brackets
corresponds to the nesting level of the section. It is fairly obvious:

.. code-block:: cfg

    [section]
    # ...
    # key-value-pairs
    # ...
        [[subsection]]
        # ...
        # more key-value-pairs
        # ...
            [[[sub-subsection]]]
            # ...

Note that the indentation is not significant, but makes reading the file much
more pleasureable.

Data types
++++++++++

Generally, every value will simply be parsed as a string or list of strings.
Where it is explicitly stated that a **boolean** is expected, the following
values are accepted:

+-------------------+-------------------+
| true              | false             |
+===================+===================+
| true, yes, on, 1  | false, no, off, 0 |
+-------------------+-------------------+

.. _key-list:

List of all keys
----------------

logging section
+++++++++++++++

This section contains information about the logging |appname| should do. This
might be useful when one wants to know when backups occurred, the reason for
failed backups and to trace back unexpected behaviour.

logfile
~~~~~~~

The path to the logfile. If it does not exist already, it will be created. The
directory containing the file will be created, too, but higher ones will not.
This means that with the default value

.. code-block:: cfg

    logfile = /var/log/rbackupd/log

the ``rbackupd/`` subfolder will be created, whereas neither ``/var/`` nor
``/var/log/`` will. Note that environment variables and the tilde character
(``~``) will be expanded.

loglevel
~~~~~~~~

The loglevel for the logfile. Available options are:

+---------+-------------------------------------------+
| level   | meaning                                   |
+=========+===========================================+
| quiet   | only warnings and errors will be logged   |
+---------+-------------------------------------------+
| default | the default log level                     |
+---------+-------------------------------------------+
| verbose | more information will be logged           |
+---------+-------------------------------------------+
| debug   | a whole lot of information will be logged |
+---------+-------------------------------------------+

Note that setting this to ``debug`` fills the logfile with a lot of information
that is only relevant for tracing bugs and unexpected behaviour and expands the
size of the logfile significantly.

rsync section
+++++++++++++

This section contains information related to the ``rsync``.

cmd
~~~

The absolute path to the rsync exectuable. If this key is missing,
``/usr/bin/rsync`` will be used as default.

tasks section
+++++++++++++

This section contains the default values applying to all tasks, and the tasks
themselves as subsections. If a default key is also present in a task
subsection, the latter takes precedence and overwrites the default.

rsync_logfile
~~~~~~~~~~~~~

A **boolean** specifying whether an rsync logfile should be created.

rsync_logfile_name
~~~~~~~~~~~~~~~~~~

The name of the rsync logfile. Note that the logfile will always be created in
the destination folder, so a relative or absolute path is not supported.

rsync_logfile_format
~~~~~~~~~~~~~~~~~~~~

The format of the entries in the rsync logfile. If this is left blank, the
default is used. See the ``--log-file-format`` option in :manpage:`rsync(1)` and
the ``log format`` section in :manpage:`rsyncd.conf(5)` for a list of available
parameters.

filters, includes, excludes, include_files, exclude_files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are filters applied to the file list by ``rsync``. You can specify as many
filters as you want per option as a :ref:`list <lists>`. Regardless of their
order in the configuration file, the options will always be ordered in like this
when passed to rsync:

- filters
- includes
- include_files
- excludes
- exclude_files

The \*_files options are not patterns, but paths to files with contain patterns.
Note that these paths have to be absolute.

See the ``FILTER RULES`` section in :manpage:`rsync(1)` for more information
about the patterns.

create_destination
~~~~~~~~~~~~~~~~~~

This **boolean** specifies whether the destination directory should be created
if it does not exist already. This might be useful when the backup destination
is located on a removable device. When setting this option to *false* one could
prevent creating a backup on the mountpoint of this device if it is not mounted.

Note that no higher directories will be created, that means when you specify

.. code-block:: cfg

    destination = /mount/backup

the ``backup/`` subfolder will be created if it does not exist, whereas
``/mount`` will not.

one_fs
~~~~~~

This **boolean** specifies whether ``rsync`` should cross filesystem boundaries
on the source when creating a backup. Compare the ``-x``/``--one-file-system``
option in :manpage:`rsync(1)`. Note that rsync treats "bind"-mount to the same
device as being on the same filesystem.

Note that you can of course still specify mount point in ``sources`` with this
set to ``true``, it only tells ``rsync`` not to descend into mountpoints when
recursing.

rsync_args
~~~~~~~~~~

This is a string that will be passed directly to ``rsync``, so you can use every
option available. These options will be put at the end of the whole rsync
command, after all other options that are results from options in the
configuration file (filters etc.).

.. warning::

    You should not alter the default value unless you know what you are doing,
    otherwise the creation of backups might fail.

.. note::

    Multiple whitespace will be condensed into a single space, so multiple lines
    can be indented nicely.

ssh_args
~~~~~~~~

This is a string with options that are passed to ``ssh`` when starting a remote
connection.

tasks
+++++

You can specify all options from the **task section** here to override them. In
addition, the following option have to be specified:

.. _sources:

sources
~~~~~~~

A comma separated list of paths with sources of the backup. These have to be
absolute paths. Environment variables and the tilde (``~``) character will be
expanded.

destination
~~~~~~~~~~~

The path to the destination of the backup. The same limitations as in
:ref:`sources` apply.

.. _interval-subsection:

interval subsection
~~~~~~~~~~~~~~~~~~~

This section is used to specify an arbitrary number of intervals in which
backups will be created. Every interval is represented by a key-value-pair. The
name of the key is the name of the interval, and the value is a string of a
specific format describing the interval. You can specify as many intervals as
you want. The intervals are specified in a format similar to the cron scheduling
program, look into :ref:`this section <cron-format>` for a description.

.. _keep-subsection:

keep subsection
~~~~~~~~~~~~~~~

This section specifies the maximum age for all backups of a specific interval.
For every entry in the :ref:`interval-subsection`, you have to specify a keep
value with the same key name here. The value is simply an integer stating how
many backups of that interval will be kept.

For example, if the value is ``1``, only one backup of that interval will be
kept. As the deletion will be done after new backups are created, these are also
counted, which means that after a new backup has been created, all potentially
existing old backups will be deleted.

The value must *not* be set to zero or a negative value.

age subsection
~~~~~~~~~~~~~~

Similar to the :ref:`keep-subsection`, this section specifies the maxiumum age
for every backup of an interval. Look :ref:`here <age-format>` for a description
of the format.

Special formats
---------------

.. _cron-format:

Cron-like format
++++++++++++++++

The format for specifying intervals is similar to the well-known
`cron <http://en.wikipedia.org/wiki/Cron>`_ scheduling daemon specification.
However, there are some important differences.

Generally, the interval is described by a string containing six *fields* that
are separated by a single space. Each *field* corresponds to a part of a date.
It looks like this::

    <minute> <hour> <day of month> <month> <year> <weekday>

.. note::

    In the current implementation, the ``weekday`` field is ignored, though it
    must not be omitted. It is best to just set it to ``*`` for now.

The following matching expressions are supported for each *field*:


- ``<integer>`` to match ``<integer>``
- ``<start>-<end>`` to match the range from ``<start>`` (inclusive) to ``<end>``
  (inclusive).
- ``*`` to match all possible values for the given position.
- ``/<step>`` as the last specifier to only match all values of the be preceding
  range that can be reached by starting at the first matched value and going steps of size <step>.
- ``,`` to separate different expressions, the union of all given expressions
  will be matched.

The minimum and maximum values for each field are as follows:


+-------------------+-------------------+----------------------------+
| field             | value boundaries  | note                       |
+-------------------+---------+---------+----------------------------+
|                   | min     | max     |                            |
+===================+=========+=========+============================+
| minute            | 0       | 59      |                            |
+-------------------+---------+---------+----------------------------+
| hour              | 0       | 23      |                            |
+-------------------+---------+---------+----------------------------+
| day of month      | 1       | 31      |                            |
+-------------------+---------+---------+----------------------------+
| month             | 1       | 12      |                            |
+-------------------+---------+---------+----------------------------+
| year              | 1900    | 3000    |                            |
+-------------------+---------+---------+----------------------------+
| weekday           | 0       | 7       | 1 = monday, 0 = 7 = sunday |
+-------------------+---------+---------+----------------------------+

For ``month`` and ``weekday``, there are handy abbreviations:

- ``month``: ``JAN``, ``FEB``, ``MAR``, ``APR``, ``MAY``, ``JUN``, ``JUL``,
  ``AUG``, ``SEP``, ``OCT``, ``NOV``, ``DEC``
- ``weekday``: ``MON``, ``TUE``, ``WED``, ``THU``, ``FRI``, ``SAT``, ``SUN``

Examples:

+------------------------+-----------------------------------------------------+
| pattern                | meaning                                             |
+========================+=====================================================+
| ``0      *   * * * *`` | matches the beginning of every hour.                |
+------------------------+-----------------------------------------------------+
| ``3,*/5  1,4 * * * *`` | matches the third and every fifth minute beginning  |
|                        | at 0 of the first and forth hour everyday.          |
+------------------------+-----------------------------------------------------+
| ``3-59/5 2,4 * * * *`` | does the same as above, apart from matching the     |
|                        | third and every fifth minute starting at the second |
|                        | one instead of starting at 0.                       |
+------------------------+-----------------------------------------------------+

.. _age-format:

Age format
++++++++++

The format to specify an age is very simple, it is just an integer with a
"multiplier" char at the end. The available multipliers are:

- ``m`` for minutes
- ``h`` for hours
- ``d`` for days
- ``w`` for weeks
- ``M`` for months

You cannot combine the multipliers with each other.
