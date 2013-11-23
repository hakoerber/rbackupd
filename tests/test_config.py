import unittest

import config

class Tests(unittest.TestCase):

    def setUp(self):
        pass


    def test_nonexistent_file(self):
        self.assertRaises(IOError, config.Config, "/does/not/exist")

