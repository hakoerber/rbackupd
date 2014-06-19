.. include:: global.rst

Setup
*****

.. _install:

Installation
------------

First, you need to get the source code by cloning the repository. To get a
folder named ``rbackupd`` in the current directory, run

.. code-block:: console

    $ git clone http://github.com/whatevsz/rbackupd.git

Now enter the folder with

.. code-block:: console

    $ cd rbackupd

To install, just run

.. code-block:: console

    # python setup.py install

with root privileges.

Now look into the template configuration file located at ::

    /etc/rbackupd/rbackupd.conf

Every options has a short description, so an initial setup should be easy. For
a more thorough description of the configuration file, look
:ref:`here <config>`.

You should generally be fine with leaving everything as it is, and just change
the ``sources`` and ``destination`` keys to the desired paths. For example, if
you want to back up the entire ``/home/`` and ``/etc/`` directories to a device
mounted at ``/mnt/backup``, set them to

.. code-block:: cfg

    sources = /home/, /etc/
    destination = /mnt/backup

Now you are set to start backup up your data:

.. _running:

Running
-------

To run |appname|, just execute

.. code-block:: console

    # rbackupd

This will use the configuration file at :file:`/etc/rbackupd/rbackupd.conf`. If
you want to use a different location, use the :option:`-c` / :option:`--config`
switch like this

.. code-block:: console

    # rbackupd --config="/my/own/configuration/file"

You require root privileges for the program to work.

There is also a `systemd <http://www.freedesktop.org/wiki/Software/systemd/>`_
service file shipped with the program. If you want to run |appname| as a
systemd service, you can do so by executing

.. code-block:: console

    # systemctl enable rbackupd.service

This will make sure |appname| is executed on next boot. If you want to start it
right away, execute

.. code-block:: console

    # systemctl start rbackupd.service

With this method |appname| will use the default configuration file at ::

     /etc/rbackupd/rbackupd.conf

Using a different configuration file with systemd
+++++++++++++++++++++++++++++++++++++++++++++++++

If you want to use a different configuration file while using systemd, you have
to edit the systemd service file located at ::

    /usr/lib/systemd/system/rbackupd.service

Look at the ``ExecStart`` line and add ``--config=<your config>`` at the end of
it, so

.. code-block:: cfg

    ExecStart=/usr/bin/rbackupd --quiet

becomes

.. code-block:: cfg

    ExecStart=/usr/bin/rbackupd --quiet --config=/path/to/your/config

If the path contains whitespace, instead of quoting only the path, you have to
quote the whole option, like this

.. code-block:: cfg

    ExecStart=/usr/bin/rbackupd --quiet "--config=/path with whitespace/"

Then you have to tell systemd to reload the new service file by executing

.. code-block:: console

    # systemctl daemon-reload

If |appname| is not running, it will use the new configuration file when it is
started next time. If it is running, restart it by running

.. code-block:: console

    # systemctl restart rbackupd.service

Packages
--------

Arch Linux
++++++++++

For Arch Linux users, there is a :file:`PKGBUILD` available at

    http://github.com/whatevsz/pkgbuilds/blob/master/rbackupd-git/PKGBUILD

that will package the latest development version from the github repository.
