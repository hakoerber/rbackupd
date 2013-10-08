import unittest
import datetime
import itertools

import cron

class Tests(unittest.TestCase):

    def setUp(self):

        self.c1 = cron.Cronjob("1 10-15 5 6,7,8,11 2012-2015 *")

        self.now = datetime.datetime.now()

        # higest possible value
        self.d_in_hi    =  datetime.datetime(2015, 11,  5, 15,  1)
        # lowest possible value
        self.d_in_lo    =  datetime.datetime(2012,  6,  5, 10,  1)

        # datetimes maching an occurence exactly
        self.d_in_exact = [self.d_in_hi, self.d_in_lo,
                           datetime.datetime(2013, 8, 5, 13, 1)]


        # datetimes older than the lowest possible value
        self.d_out_lo   = [datetime.datetime(2011,  6,  5, 10,  1),
                           datetime.datetime(2012,  5,  5, 10,  1),
                           datetime.datetime(2012,  6,  4, 10,  1),
                           datetime.datetime(2012,  6,  5,  9,  1),
                           datetime.datetime(2012,  6,  5, 10,  0)]


        # datetimes younger than the lowerst possible value
        self.d_out_hi   = [datetime.datetime(2016, 11,  5, 15,  1),
                           datetime.datetime(2015, 12,  5, 15,  1),
                           datetime.datetime(2015, 11,  6, 15,  1),
                           datetime.datetime(2015, 11,  5, 16,  1),
                           datetime.datetime(2015, 11,  5, 15,  2)]

        # datetimes younger or equal than the oldest and older or equal than
        # the yougest possible value
        self.d_in_any   = [datetime.datetime(2013,  8,  5, 13,  1),
                           datetime.datetime(2014,  3,  7, 23, 12),
                           datetime.datetime(2014,  1,  5, 15,  1)] + \
                          [self.d_in_lo, self.d_in_hi]


        # datetimes older than the oldest possible value and younger than the
        # youngest possible value
        self.d_out_any  = [datetime.datetime(1999, 8, 5, 13, 1),
                           datetime.datetime(2023, 5, 24, 2, 54)] + \
                          self.d_out_hi + \
                          self.d_out_lo

        self.d_all      = self.d_in_exact + self.d_out_lo + self.d_out_hi + \
                          self.d_in_any + self.d_out_any + [self.now]



    def test_matching(self):
        for d in self.d_in_exact:
            self.assertTrue(self.c1.matches(d))

        for d in self.d_out_any:
            self.assertFalse(self.c1.matches(d))


    def test_latest_occurence(self):

        d1 = datetime.datetime(2014, 8, 7, 23, 12)
        self.assertEqual(self.c1.get_most_recent_occurence(d1),
                         datetime.datetime(2014, 8, 5, 15, 1))

    def test_latest_occurence_exact(self):
        for d in self.d_in_exact:
            self.assertEqual(self.c1.get_most_recent_occurence(d), d)

    def test_latest_occurence_fails_when_too_old(self):
        for d in self.d_out_lo:
            self.assertRaises(ValueError, self.c1.get_most_recent_occurence, d)

    def test_latest_occurence_max(self):
        for d in self.d_out_hi:
            self.assertEqual(self.c1.get_most_recent_occurence(d), self.d_in_hi)

    def test_max_time(self):
        self.assertEqual(self.c1.get_max_time(), self.d_in_hi)

    def test_min_time(self):
        self.assertEqual(self.c1.get_min_time(), self.d_in_lo)

    def test_has_occured_fails_wrong_order(self):
        for (d1, d2) in zip(self.d_out_hi, self.d_out_lo):
            self.assertRaises(ValueError,
                              self.c1.has_occured_between, d1, d2)

    def test_has_occured_between(self):
        for (d1, d2) in zip(self.d_out_lo, self.d_in_any):
            last = self.c1.get_most_recent_occurence(d2)
            self.assertEqual(self.c1.has_occured_between(d1, d2),
                             last >= d1)

    def test_has_occured_between_identical_to_match_if_d1_equal_d2(self):
        for d in self.d_all:
            self.assertEqual(self.c1.has_occured_between(d, d),
                             self.c1.matches(d))
