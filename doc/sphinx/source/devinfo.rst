.. include:: global.rst

Developer information
*********************

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


Testing
-------

Testing is done using tox together with pep8 and py.test. The bash script
`tests.sh` in the project root executes all tests and reports back.

All unittests can be found in the `test/` subdirectory of the prject root.

Tox is configured so that it will run py.test to run all tests in the test
directory against python version 3.4 and test if the sphinx documentation can be
built.
