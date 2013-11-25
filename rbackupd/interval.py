# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>
#
# This file is part of rbackupd.
#
# rbackupd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rbackupd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import sys

logger = logging.getLogger(__name__)


def interval_to_oldest_datetime(interval):
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
                (datetime.date.today().month - value) // 12)
        month = datetime.date.today().month - value % 12
        if month == 0:
            month = 12
        # get the last day of the month by going back one month from the first
        # day of the following month
        last_day_of_month = (datetime.date(year=year, month=month, day=1) -
                             datetime.timedelta(days=1)).day
        day = datetime.date.today().day
        if day > last_day_of_month:
            day = last_day_of_month
        result = result.replace(year=year, month=month, day=day)
    else:
        logger.critical("Invalid interval: \"%s\". Aborting.", interval)
        sys.exit(13)
    return result
