# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import datetime
import logging
import sys

logger = logging.getLogger(__name__)


class Interval(object):
    """
    Represents an interval relative to the current date.
    You can use the following suffixes:
    ======  ==========
    suffix  stands for
    ======  ==========
    m       minutes
    h       hours
    w       weeks
    d       days
    M       months
    ======  ==========

    You can use this module for example to check whether some event happened
    in the last 3 days like this::

        import interval

        point_in_time = some_datetime

        interval = interval.Interval("3d")

        if interval.get_oldest_datetime >= datetime_to_check:
            print("point_in_time happened in the last 3 days")

    :param interval_string: Describes the interval.
    :type interval_string: str
    """
    def __init__(self, interval_string):
        self.interval_string = interval_string

    def get_oldest_datetime(self):
        """
        Returns the oldest datetime that still lies inside the interval.

        :rtype: datetime instance
        """
        return _interval_to_oldest_datetime(self.interval_string)


def _interval_to_oldest_datetime(interval):
    result = datetime.datetime.now()
    suffix = interval[-1:]
    value = int(interval[:-1])
    if suffix == "m":
        result = result - datetime.timedelta(minutes=value)
    elif suffix == "h":
        result = result - datetime.timedelta(hours=value)
    elif suffix == "w":
        result = result - datetime.timedelta(weeks=value)
    elif suffix == "d":
        result = result - datetime.timedelta(days=value)
    elif suffix == "M":

        year = (datetime.date.today().year +
                (datetime.date.today().month - value - 1) // 12)
        month = datetime.date.today().month - value % 12
        if month == 0:
            month = 12
        # get the last day of the month by going back one month from the first
        # day of the following month
        month_plus_one = (month + 1) % 12
        last_day_of_month = (datetime.date(year=year,
                                           month=month_plus_one,
                                           day=1) -
                             datetime.timedelta(days=1)).day
        day = datetime.date.today().day
        if day > last_day_of_month:
            day = last_day_of_month
        result = result.replace(year=year, month=month, day=day)
    else:
        logger.critical("Invalid interval: \"%s\". Aborting.", interval)
        sys.exit(13)
    return result
