# -*- coding:  utf-8 -*-

import tushare as ts
import pandas as pd
from collections import namedtuple

Trend = namedtuple('Trend', ['directon', 'start', 'end'])


def reverse_df(df):
    df.sort_index(axis=0, ascending=True, inplace=True)
    return df


def split_trend(df, index_col=None):
    # make sure input df is properly sorted and minimum required length is satisfied
    df.sort_index(axis=0, ascending=True, inplace=True)
    assert(len(df) > 4)

    # trend list
    upl = []
    dnl = []
    rows = []
    trend = None
    for row in rows:

        if trend is None:
            trend = Trend(direction=1, start=1, end=1)
            if row.pct < 0:
                trend._replace(direction=1)
            trend._replace(start=row.num)
        else:
            if not trend.direction and row.pct >= 0:
                trend._replace(end=row.num-1)
                dnl.append(trend)
                trend = Trend(direction=1, start=row.num, end=0)
            elif trend.direction and row.pct < 0:
                trend._replace(end=row.num-1)
                upl.append(trend)
                trend.Trend(direction=0, start=row.num, end=0)
            else:
                pass

        # finalize
        if row.last:
            trend._replace(end=row.num)
            if trend.direction:
                upl.append(trend)
            else:
                dnl.append(trend)
