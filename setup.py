# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import os
import sys

import setuptools

# get __version__ from the package.
exec(open("./rbackupd/version.py").read())

setuptools.setup(
    name = 'rbackupd',
    version = __version__,
    description = 'A backup program creating snapshots through rsync.',
    long_description = open('README.rst').read(),
    url = 'http://github.com/whatevsz/rbackupd',
    download_url = 'http://github.com/whatevsz/rbackupd/releases',
    author = 'Hannes Körber',
    author_email = 'hannes.koerber+rbackupd@gmail.com',

    packages = [
        'rbackupd',
        'rbackupd.cmd',
        'rbackupd.config',
        'rbackupd.log',
        'rbackupd.schedule'
    ],
    scripts = ['scripts/rbackupd'],
    data_files = [
        ('/etc/rbackupd', ['conf/rbackupd.conf']),
        ('/usr/share/rbackupd', ['conf/scheme.ini']),
        ('/usr/lib/systemd/system/', ['init/systemd/rbackupd.service']),
        ('/etc/dbus-1/system.d/', ['other/dbus/rbackupd.conf']),
        ('/usr/share/rbackupd/', ['conf/scheme.ini'])
    ],

    install_requires = ['configobj'],
    setup_requires = [],
    extras_require = {},
    tests_require = ['tox'],

    license = 'GNU GPL',
    platforms = ['Linux'],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: System',
        'Topic :: System :: Archiving',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Archiving :: Mirroring',
    ],
    keywords = 'backup snapshot rsync')
