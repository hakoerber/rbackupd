import unittest

import configmanager


class Tests(unittest.TestCase):

    def setUp(self):
        pass

    def test_nonexistent_file(self):
        self.assertRaises(IOError,
                          configmanager.ConfigManager,
                          "/does/not/exist",
                          None)
