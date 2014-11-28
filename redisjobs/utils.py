import time


SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE 
DAY = 24 * HOUR
WEEK = 7 * DAY
MONTH = 30.4375 * DAY
QUARTER = 13 * WEEK
YEAR = 12 * MONTH


def identity(obj):
    return obj


def forever(fn, *vargs, **kwargs):
    """ Put a function on an endless loop, but 
    execute at most once a second. """

    last = time.time()
    while True:
        now = time.time()
        elapsed = now - last
        if elapsed >= 1:
            last = now
            fn(*vargs, **kwargs)
        else:
            time.sleep(1 - elapsed)


units = {
    'seconds': SECOND, 
    'minutes': MINUTE, 
    'hours': HOUR, 
    'days': DAY, 
    'weeks': WEEK, 
    'months': MONTH, 
    'quarters': QUARTER, 
    'years': YEAR, 
    }

def seconds(**spec):
    t = 0

    for unit, value in spec.items():
        if unit in units:
            t = t + units[unit] * (value or 0)

    return t
