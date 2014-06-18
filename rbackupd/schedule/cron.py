# -*- encoding: utf-8 -*-
# Copyright (c) 2013 Hannes Körber <hannes.koerber+rbackupd@gmail.com>

"""
This module implements a cron scheduling flavor.
"""

import datetime

_ranges = (range(60), range(24), range(1, 32), range(1, 13),
           range(1900, 3000), range(1, 8))  # Creating year 3000 problem


# This list contains the indices of the fields that should be considered for
# all operations of that module. The value range(0,6) means that all fields
# should be considered, which is the desired behaviour. For now, the last
# field (week) is ignored. When changing this value, look at the methods
# _datetime_to_tuple() and _tuple_to_datetime() too to read and write datetime
# objects correctly.
_check_range = range(0, 5)


# mapping strings to integer for every field, so you can for example use
# JUN-OCT instead of 6-10 in the "month" field
_name_mapping = ({},
                 {},
                 {},
                 {"JAN": 1, "FEB": 2, "MAR": 3, "APR":  4, "MAY":  5,
                  "JUN":  6, "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10,
                  "NOV": 11, "DEC": 12},
                 {},
                 {"MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
                  "SUN": 7})


class Cronjob(object):
    """
    Represents a single cronjob schedule. It will not execute any code, but
    will provide methods to poll information about that cronjob in relation to
    a specific time, for example whether the cronjob elapsed between two
    different times and so on.
    Look here (https://en.wikipedia.org/wiki/Cron#CRON_expression) for an
    deeper insight into the formatting of a cron expression. This class does
    not support all formatting options mentioned in this article, and the order
    of the fields differ.

    Fields::

    <minute>  <hour>  <day_of_month>  <month>  <year>  [<weekday>]

    Here are the possible values for all fields:



    ============  ======================================================
    field         possible value
    ============  ======================================================
    minute        0..59
    hour          0..23
    day_of_month  1..31
    month         1..12, JAN..DEC
    year:         1900..3000
    weekday       0..7 (1 = monday ... 7 = sunday, 0 = sunday), MON..SUN
    ============  ======================================================

    The following matching expressions are supported:

    - `<integer>` to match `<integer>`
    - `<start>-<end>` to match the range from `<start>` (inclusive) to `<end>`\
        (inclusive).
    - `*` to match all possible values for the given position.
    - `/<step>` as the last specifier to only match all values of the be\
        preceding range that can be reached by starting at the first matched\
        value and going steps of size <step>.
    - `,` to separate different expressions, the union of all given\
        expressions will be matched.

    Examples:

    ======================  ====================================================
    pattern                 meaning
    ======================  ====================================================
    ``0      *   * * * *``  matches the beginning of every hour.
    ``3,*/5  1,4 * * * *``  matches the third and every fifth minute beginning
                            at 0 of the first and forth hour everyday.
    ``3-59/5 2,4 * * * *``  does the same as above, apart from matching the
                            third and every fifth minute starting at the second
                            one instead of starting at 0.
    ======================  ====================================================


    IMPORTANT: `<weekday>` is not yet supported and can be omitted. For all
    comparisons in this class, the weekday information is ignored.

    :param schedule_string: The string to represent.
    :type schedule_string: str
    """
    def __init__(self, schedule_string):
        self.cronstring = schedule_string
        self.schedule = _parse_cronjob_string(schedule_string)

    def matches(self, date_time):
        """
        Determines whether a given datetime has a match in the cronjob, that
        means that there is a cronjob occurrence now or in the past that
        matches the datetime. Only the year, month, day, hour and minute
        values of the datetime are used to determine a match, all other values
        are ignored.

        :param date_time: The datetime to check.
        :type date_time: datetime instance

        :returns: True if the datetime matches the cronjob, False otherwise.
        :rtype: bool
        """
        d_schedule = _datetime_to_tuple(date_time)
        for i in _check_range:
            if not d_schedule[i] in self.schedule[i]:
                return False
        return True

    def has_occured_between(self, date_time_1, date_time_2,
                            include_start=True):
        """
        Determines whether the cronjob has occurred between two datetimes, what
        means that there was any match in this period. If date_time_1 and
        date_time_2 represent the same point in time, the behaviour is
        identical to matches(date_time_1).

        :param date_time_1: The datetime determining the start of the period.
        :type date_time_1: datetime instance

        :param date_time_2: The datetime determining the end of the period.
        :type date_time_2: datetime instance

        :param include_start: Determines whether the start should be included
                              into the search range.
        :type include_start: bool

        :returns: True if the cronjob has occurred between the two datetimes,
                  False otherwise.
        :rtype: bool

        :raise ValueError: if date_time_2 is older than date_time_1
        """
        if date_time_2 < date_time_1:
            raise ValueError(
                "date_time_1 has to be older than or equal to date_time_2.")
        min_val = self.get_min_time()
        max_val = self.get_max_time()
        if date_time_1 < min_val:
            date_time_1 = min_val
        if date_time_2 > max_val:
            date_time_2 = max_val
        if date_time_2 < min_val:
            return False
        if date_time_1 > max_val:
            return False
        if ((date_time_1 < min_val and date_time_2 < min_val) or
                (date_time_1 > max_val and date_time_2 > max_val)):
            return False
        most_recent_occurence = self.get_most_recent_occurence(date_time_2)
        if include_start:
            return most_recent_occurence >= date_time_1
        else:
            return most_recent_occurence > date_time_1

    def has_occured_since(self, date_time, include_start=True):
        """
        Determines whether the cronjob has ever occurred since date_time, what
        means that there was any match in this period. If date_time represents
        now, the bahaviour is identical to matches(date_time).

        :param date_time: The datetime in the past to check against.
        :type date_time: datetime instance

        :param include_start: Determines whether the start should be included
                              into the search range.
        :type include_start: bool

        :returns: True if the cronjob has occurred since date_time, False
                  otherwise.
        :rtype: bool

        :raise ValueError: if date_time is in the future
        """
        return self.has_occured_between(date_time,
                                        datetime.datetime.now(),
                                        include_start)

    def get_max_time(self):
        """
        Determines the last possible datetime at which the cronjob occurs.

        :returns: The last possible datetime at which the cronjob occurs.
        :rtype: datetime instance
        """
        return _tuple_to_datetime([max(val) for val in self.schedule])

    def get_min_time(self):
        """
        Determines the first possible datetime at which the cronjob occurs.

        :returns: The first possible datetime at which the cronjob occurs.
        :rtype: datetime instance
        """
        return _tuple_to_datetime([min(val) for val in self.schedule])

    def get_most_recent_occurence(self, date_time=None):
        """
        Determines the most recent occurrence of the cronjob relative to a
        specific datetime.

        :param d: The datetime relative to which to determine the most
                  recent occurrence. If None is given, datetime.datetime.now()
                  is used instead.
        :type d: datetime instance

        :returns: The most recent occurrence of the cronjob relative to d.
        :rtype: datetime instance

        :raise ValueError: if d is older than the first possible occurrence
                           of the cronjob
        """
        if not date_time:
            date_time = datetime.datetime.now()
        d_schedule = _datetime_to_tuple(date_time)
        latest_schedule = [0, 0, 0, 0, 0, None]

        # we go from the most significant to the least significant position,
        # from year to minute
        # for each position we compare the d_schedule value with all possible
        # values in self.schedule:
        #
        # we choose the hightest value in self.schedule that is lower or equal
        # than the value of d_schedule
        #
        # if we choose a lower value than d_schedule, we have change the
        # procedure: in all following lower significant positions, instead of
        # comparing, we always choose the hightest value from self.schedule[i]
        #
        # if we choose the equal value, we just continue with our procedure
        #
        # if we cannot choose a lower or equal value that means that there is
        # no matching for the current i+1 position. so we have to choose the
        # next lower possible value for the i+1 position. if this is not
        # possible,  either because i+1 does not exist (we are currently at the
        # year position) or there already is the lowest possible value at
        # position i+1, that means that d_schedule is older than every possible
        # value in self.schedule, so we raise an error
        #
        # this is shittier than everything, but it somehow passes the tests
        max_only_now = False
        i = 5
        while i > 0:
            i -= 1
            if not max_only_now:
                lower_equal_range = [val for val in self.schedule[i]
                                     if val <= d_schedule[i]]

                if len(lower_equal_range) == 0:
                    _set_lower_value(self.schedule, latest_schedule, i)
                    latest_schedule[i] = max(self.schedule[i])
                    max_only_now = True
                    continue

                lower_equal_value = max(lower_equal_range)
                is_equal_value = (lower_equal_value == d_schedule[i])

                latest_schedule[i] += lower_equal_value
            else:
                latest_schedule[i] += max(self.schedule[i])

            if not is_equal_value:
                max_only_now = True

        return _tuple_to_datetime(latest_schedule)


def _set_lower_value(schedule, latest_schedule, i):
    """
    Helper function for Cronjob.get_most_recent_occurence(). Shitty.
    """
    if i == 4:
        raise ValueError("d is older than every possible value in "
                         "this crontab")
    # not using indices, as that would rely on self.schedule to
    # be sorted
    # lets revert to the last position
    i += 1
    # lower it to the next possible value and continue
    last_value = latest_schedule[i]
    lower_values = [val for val in schedule[i]
                    if val < last_value]
    if len(lower_values) == 0:
        _set_lower_value(schedule, latest_schedule, i)
        return
    latest_schedule[i] = max(lower_values)


def _parse_cronjob_string(cronjob_string):
    """
    Parses a cronjob string to a list of sets containing all possible values
    for a position.

    :param cronjob_string: The cronjob string to parse. For the format, see
    the Cronjob class.
    :type cronjob_string: str

    :returns: All possible values for every position.
    :rtype: list of sets.
    """
    if not isinstance(cronjob_string, str):
        raise ValueError("Schedule string is not a string.")
    possible_values = []
    fields = _parse_string_to_fields(cronjob_string)
    if len(fields) != 6:
        raise ValueError("Too few or too many fields found.")
    for i in _check_range:
        possible_values.append(
            _parse_expression_at_index(fields[i], i))
    return possible_values


def _parse_string_to_fields(cron_string):
    """
    Converts a given string into a list of all fields found in this string.

    :param cron_string: The string to parse.
    :type cron_string: str

    :returns: A list containing all fields found in the string.
    :rtype: list of strings
    """
    return cron_string.split()


def _datetime_to_tuple(date_time):
    """
    Converts a datetime to a (minute, hour, day_of_month, month, year,
    weekday) tuple.

    :param d: The datetime object to convert.
    :type d: datetime instance

    :returns: A tuple derived from the datetime.
    :rtype: tuple
    """
    (d_year, d_month, d_day, d_hour, d_minute, _, d_weekday, _, _) = \
        date_time.timetuple()
    # ATTENTION: timetuple's tm_wday is in range(0,7), but we need range(1,8)
    # for our weekday attribute.
    d_weekday += 1
    return (d_minute, d_hour, d_day, d_month, d_year, d_weekday)


def _tuple_to_datetime(date_time_tuple):
    """
    Converts a (minute, hour, day_of_month, month, year, weekday) tuple to
    the corresponding datetime.

    :param date_time_tuple: The tuple to convert.
    :type date_time_tuple: tuple

    :returns: A datetime derived from the tuple.
    :rtype: datetime
    """
    return datetime.datetime(year=date_time_tuple[4],
                             month=date_time_tuple[3],
                             day=date_time_tuple[2],
                             hour=date_time_tuple[1],
                             minute=date_time_tuple[0])


def _parse_expression_at_index(expression, index):
    """
    Parses the expression at a specific index and returns a set containing all
    possible values for the field at the specified index.

    :param expression: The expression to parse.
    :type expression: str

    :param index: The index of the expression in a cronjob string.
    :type index: int

    :returns: A set containing all possible values for the field at index.
    :rtype: set

    :raise ParseError: if the expression is invalid
    """
    # We will just split the exception and parse every subexpression
    # individually. If an error occurs, we want the exception to contain the
    # whole expression, not just the substring
    if not expression:
        raise ParseError(expression, "Empty expression.")
    subexpressions = expression.split(',')
    possible_values_set = set()
    for expression in subexpressions:
        try:
            possible_values = _parse_subexpression_at_index(expression, index)
        except ParseError:
            raise
        possible_values_set = possible_values_set.union(possible_values)
    return possible_values_set


def _parse_subexpression_at_index(expression, index):
    """
    Helper function for _parse_expression_at_index(), same signature, but only
    works on expressions without ",".
    """
    possible_values = None
    rest = expression.strip()
    if not expression or ',' in expression:
        raise ParseError(expression, "Empty subexpression.")

    # if there is a step value, remember it, otherwise just use 1
    parts = rest.split('/')
    if len(parts) == 1:
        step = 1
    elif len(parts) == 2:
        try:
            step = int(parts[1])
        except ValueError:
            raise ParseError(expression, "Invalid step value.")
    else:
        raise ParseError(expression, "Multiple step formatters found.")
    rest = parts[0]

    # now, everything else might be "*", "x-y" or "z", let's look for a hyphen
    # formatter
    if '-' in rest:
        parts = rest.split('-')
        if len(parts) != 2:
            raise ParseError(expression, "Multiple range formatters found.")
        if not parts[0]:
            raise ParseError(expression,
                             "Missing start value for range formatter.")
        if not parts[1]:
            raise ParseError(expression,
                             "Missing end value for range formatter.")
        start = _get_integer_at_index(parts[0], index)
        end = _get_integer_at_index(parts[1], index)
        if start is None:
            raise ParseError(expression,
                             "Invalid start value for range formatter.")
        if end is None:
            raise ParseError(expression,
                             "Invalid end value for range formatter.")
        if start > end:
            raise ParseError(
                expression,
                "Start value must be lower than or equal to end value.")
        possible_values = set(range(start, end + 1))
    elif '*' == rest:
        possible_values = set(_ranges[index])
    elif _get_integer_at_index(rest, index) is not None:
        possible_values = set([_get_integer_at_index(rest, index)])
    else:
        raise ParseError(expression, "Invalid expression")

    # Now we have a list containing all possible values as specified by the
    # expression without the potential step formatter. If the step value is 1,
    # we do not have to do anything, but when it is not, we have to filter out
    # all values not met by the step criteria.
    if step != 1:
        possible_values = \
            {i for i in possible_values if i % step == min(possible_values)}
    return possible_values


def _get_integer_at_index(parse_string, index):
    """
    Returns the integer corresponding to a string at a specific index, or
    None if no appropriate value was found.

    :param parse_string: The string to parse.
    :type parse_string: str

    :param index: The index of the string in a field list.
    :type index: int

    :returns: The corresponding integer or None if no appropriate value was
    found.
    :rtype: int
    """
    if parse_string.isdigit():
        return int(parse_string)
    if parse_string in _name_mapping[index]:
        return _name_mapping[parse_string]
    return None


class ParseError(Exception):
    """
    Exception that is raised when the parsing of a cronstring fails. Contains
    the expression that was parsed and a message explaining how it failed.

    :param expression: The expression that could not be parsed
    :type expression: str

    :param message: A message with details about the error.
    :type message: str
    """
    def __init__(self, expression, message):
        Exception.__init__(self, message)
        self.message = message
        self.expression = expression

    def __str__(self):
        return self.message
