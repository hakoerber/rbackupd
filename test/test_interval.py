# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import datetime
import unittest

from rbackupd.schedule.interval import Interval


class Tests(unittest.TestCase):

    def setUp(self):
        self.now = datetime.datetime.now().replace(microsecond=0)

    def test_minute(self):
        interval = Interval("1m")
        self.assertEqual(interval.get_oldest_datetime(),
                         self.now - datetime.timedelta(minutes=1))

    def test_hours(self):
        interval = Interval("200h")
        self.assertEqual(interval.get_oldest_datetime(),
                         self.now - datetime.timedelta(hours=200))

    def test_weeks(self):
        interval = Interval("135w")
        self.assertEqual(interval.get_oldest_datetime(),
                         self.now - datetime.timedelta(weeks=135))

    def test_days(self):
        interval = Interval("400d")
        self.assertEqual(interval.get_oldest_datetime(),
                         self.now - datetime.timedelta(days=400))

    def test_month_trivial(self):
        interval = Interval("1M")
        timestamp = datetime.datetime(year=2013, month=8, day=15)
        target = datetime.datetime(year=2013, month=7, day=15)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp),
                         target)

    def test_month_exceeding_last_day(self):
        interval = Interval("1M")
        timestamp = datetime.datetime(year=2013, month=5, day=31)
        target = datetime.datetime(year=2013, month=4, day=30)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp),
                         target)

    def test_month_leap_year(self):
        interval = Interval("1M")
        timestamp1 = datetime.datetime(year=2012, month=3, day=31)
        timestamp2 = datetime.datetime(year=2012, month=3, day=29)
        timestamp3 = datetime.datetime(year=2012, month=3, day=28)

        target = datetime.datetime(year=2012, month=2, day=29)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp1),
                         target)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp2),
                         target)
        self.assertNotEqual(interval.get_oldest_datetime(reference=timestamp3),
                            target)

    def test_month_no_leap_year(self):
        interval = Interval("1M")
        timestamp1 = datetime.datetime(year=2013, month=3, day=31)
        timestamp2 = datetime.datetime(year=2013, month=3, day=29)
        timestamp3 = datetime.datetime(year=2013, month=3, day=28)

        target = datetime.datetime(year=2013, month=2, day=28)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp1),
                         target)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp2),
                         target)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp3),
                         target)

    def test_month_crossing_years(self):
        interval = Interval("23M")
        interval2 = Interval("2M")

        timestamp1 = datetime.datetime(year=2012, month=1, day=31)
        timestamp2 = datetime.datetime(year=2012, month=1, day=29)
        timestamp3 = datetime.datetime(year=2012, month=1, day=28)
        timestamp4 = datetime.datetime(year=2014, month=1, day=31)
        timestamp5 = datetime.datetime(year=2014, month=1, day=29)
        timestamp6 = datetime.datetime(year=2014, month=1, day=28)
        timestamp7 = datetime.datetime(year=2014, month=1, day=31)

        target1 = datetime.datetime(year=2010, month=2, day=28)
        target2 = datetime.datetime(year=2010, month=2, day=28)
        target3 = datetime.datetime(year=2010, month=2, day=28)
        target4 = datetime.datetime(year=2012, month=2, day=29)
        target5 = datetime.datetime(year=2012, month=2, day=29)
        target6 = datetime.datetime(year=2012, month=2, day=28)
        target7 = datetime.datetime(year=2013, month=11, day=30)

        self.assertEqual(interval.get_oldest_datetime(reference=timestamp1),
                         target1)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp2),
                         target2)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp3),
                         target3)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp4),
                         target4)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp5),
                         target5)
        self.assertEqual(interval.get_oldest_datetime(reference=timestamp6),
                         target6)
        self.assertEqual(interval2.get_oldest_datetime(reference=timestamp7),
                         target7)
