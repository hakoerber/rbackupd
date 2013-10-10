from distutils.core import setup

setup(
      name = 'rbackupd',
      version = '0.2-dev',
      url = 'http://github.com/whatevsz/rbackupd',
      download_url = 'http://github.com/whatevsz/rbackupd/releases',

      author = 'Hannes Körber',
      author_email = 'hannes.koerber+rbackupd@gmail.com',
      maintainer = 'Hannes Körber',
      maintainer_email = 'hannes.koerber+rbackupd@gmail.com',

      license = 'GNU GPL',
      platforms = ['Linux'],
      description = 'A backup program creating snapshots through rsync.',
      long_description = open('README.rst').read(),

      package_dir = {'rbackupd': 'src'},
      packages = ['rbackupd'],
      scripts = ['scripts/rbackupd'],
      data_files = [('/etc/rbackupd/', ['conf/rbackupd.conf'])],
      requires = [],

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
      keywords = 'backup snapshot rsync'
      )
