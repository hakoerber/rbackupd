import datetime
import sys


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
        print("Invalid interval: %s" % interval)
        sys.exit(13)
    return result
