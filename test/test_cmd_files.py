import unittest

import rbackupd.cmd.files

import tempfile
import shutil
import os


class Tests(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp()
        self.realfile = os.path.join(self.testdir, "file")
        self.symlink = os.path.join(self.testdir, "symlink")

        with open(self.realfile, 'w'):
            pass

        os.symlink(self.realfile, self.symlink)

    def tearDown(self):
        shutil.rmtree(self.testdir)

    def test_remove_symlink(self):
        self.assertTrue(os.path.islink(self.symlink))
        rbackupd.cmd.files.remove_symlink(self.symlink)
        self.assertFalse(os.path.exists(self.symlink))

    def test_create_symlink(self):
        tempsymlink = os.path.join(self.testdir, "templink")
        self.assertFalse(os.path.exists(tempsymlink))
        rbackupd.cmd.files.create_symlink(self.realfile, tempsymlink)
        self.assertTrue(os.path.islink(tempsymlink))
        target = os.path.realpath(tempsymlink)
        self.assertTrue(os.path.exists(target))
        self.assertTrue(os.path.samefile(target, self.realfile))

    def test_move(self):
        target = os.path.join(self.testdir, "target")
        self.assertTrue(os.path.exists(self.realfile))
        self.assertFalse(os.path.exists(target))
        rbackupd.cmd.files.move(self.realfile, target)
        self.assertFalse(os.path.exists(self.realfile))
        self.assertTrue(os.path.exists(target))
        rbackupd.cmd.files.move(target, self.realfile)
