# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

import copy
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

    def get_oldest_datetime(self, reference=None):
        """
        Returns the oldest datetime that still lies inside the interval.

        :param reference: The reference time for the comparison. If missing, the
            current date is taken.
        :type reference: datetime instance

        :rtype: datetime instance
        """
        if reference is None:
            reference = datetime.datetime.now().replace(microsecond=0)

        return _interval_to_oldest_datetime(self.interval_string, reference)


def _interval_to_oldest_datetime(interval, reference):
    result = copy.copy(reference)
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
        year = (reference.year +
                ((reference.month - 1) - value) // 12)
        month = ((reference.month - 1) - value) % 12 + 1
        # get the last day of the month by going back one month from the first
        # day of the following month
        month_plus_one = ((month - 1) + 1) % 12 + 1
        last_day_of_month = (datetime.date(year=year,
                                           month=month_plus_one,
                                           day=1) -
                             datetime.timedelta(days=1)).day
        day = reference.day
        if day > last_day_of_month:
            day = last_day_of_month
        result = result.replace(year=year, month=month, day=day)
    else:
        logger.critical("Invalid interval: \"%s\". Aborting.", interval)
        sys.exit(13)
    return result
