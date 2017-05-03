# -*- coding: utf-8 -*-

import datetime


def get_next_day(date):
    parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    next_day = parsed_date + datetime.timedelta(days = 1)
    return next_day.isoformat().split('T')[0]
