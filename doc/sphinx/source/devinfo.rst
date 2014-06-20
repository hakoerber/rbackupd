.. include:: global.rst

Developer information
*********************

.. _contributing:

Contributing
------------

This is a brief guide about contributing to |appname|.

Install *git*
+++++++++++++

Install ``git`` from your distribution's repositories or from `the website
<http://git-scm.com/>`_. If you are unfamiliar with ``git``, `this book
<http://git-scm.com/book>`_ is a great resource and reference.

Fork on GitHub
++++++++++++++

Login or signup on `GitHub <http://www.github.com>`_ and fork `rbackupd
<http://github.com/whatevsz/rbackupd>`_ into your own account.

Clone the repository locally
++++++++++++++++++++++++++++

Run the following to get the source code on your machine:

.. code-block:: console

    $ git clone git@github.com:<your-github-name>/rbackupd.git

Create a feature branch
+++++++++++++++++++++++

With the following command, you create a new branch and switch to it:

.. code-block:: console

    $ git checkout -b <your-branch-name>

Make your changes and commit them
+++++++++++++++++++++++++++++++++

Now you can make the changes you want. When you are done, run the test with
the ``tests.sh`` script in the project root and make sure they pass. Then, you
can commit them with the following commands:

.. code-block:: console

    $ git add -A
    $ git commit

Enter a descriptive message for the commit and you are done. Of course, you can
create as many commits as you want.

Push your branch to GitHub
++++++++++++++++++++++++++

Now it is time to get your changes back to GitHub. Push the commit(s) you just
did with the following command:

.. code-block:: console

    $ git push origin <your-branch-name>

Create a pull request
+++++++++++++++++++++

Go to your project page on GitHub, switch to your branch with the drop-down menu
and click the green `Compare & Review` button. In the next window, you can
review the pull request, and after making sure everything is ok, click `Send
pull request`. That's it!

.. _issues:

Issue tracker
-------------

If you have feature requests or find a potential bug, don't hesitate to file a
ticket in the `Issue Tracker <http://github.com/whatevsz/rbackupd/issues>`_ on
GitHub! You can also claim an open ticket and :ref:`contribute <contributing>`
a bugfix or new feature if you want.

Project structure
-----------------

folders
+++++++

- ``doc/`` contains the whole documentation
    * ``ideas/`` contains textfiles with ideas about the project
    * ``sphinx/`` contains the sphinx documentation you are reading right now
    * ``man/`` contains man pages
- ``init/`` contains files for the init system
    * ``systemd/`` contains service files for systemd
- ``conf/`` contains configuration files for the final application
- ``scripts/`` contains executables for the final application
- ``test/`` contains test modules
- ``other/`` contains various stuff not fitting any other categories
    * ``dbus/`` contains D-Bus policy .conf files

files
+++++

Most of them should be self-explanatory. However, there are some helper scripts
that deserve an explanation:

- ``install.sh`` installs the program, it is merely are wrapper for
  ``python setup.py install``
- ``make-html-docs.sh`` generates the sphinx documentation and displays it in
  the browser
- ``stats.sh`` shows some stats about the source files
- ``tests.sh`` runs all available tests and reports back
- ``clean.sh`` removes all files that can be regenerated or is unnecessary, such
  as everything in the build directory and log files.
- ``run.sh`` runs the daemon process and makes sure to use the packages in the
  source tree instead of installed ones
- ``run-client.sh`` does the same as the above, but with the client program.

Testing
-------

Testing is done using tox together with pep8 and py.test. The bash script
`tests.sh` in the project root executes all tests and reports back.

All unittests can be found in the `test/` subdirectory of the prject root.

Tox is configured so that it will run py.test to run all tests in the test
directory against python version 3.4 and test if the sphinx documentation can be
built.
