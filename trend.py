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


class Analyzer(object):
    
    def __call__(self, df):
        self.df = df
                
class BaseAnalyzer(object):
    
    def first_max_by_column(self, df, cname):
        """Return a tuple of (index, series) of the first maximum's location and row(as series),
        """
        idx = df[cname].idxmax()
        row = df.loc[idx]
        return idx, row
    
    def first_min_by_column(self, df, cname):
        """Return a tuple of (index, series) of the first maximum's location and row(as series),
        """
        idx = df[cname].idxmax()
        row = df.loc[idx]
        return idx, row
    
    
    def nlargest(self, df, cname):
        """Return a tuple of (list, DataFrame) of the nlargests, list's element are indexes of
        the founded row, df is just return by nlargest method
        """
        d = df.nlargest(cname)
        idxes = d.index.to_list()
        
        return idxes, d
        
    
    def nan_columns(self, df):
        """Return a list of column's name contains nan value"""
        d = df.isna().any().to_dict()
        return [ k for k, v in d.items() if v is True]
    
    
class QuoteFormater(object):

    def ensure_base_column_name(df):
        pass
    
    
    
GDK_COLUMN_NAME = 'gdk'






class BaseReporter(object):
    
    def __call__(self, df):
        self.df = df


class GDKReporter(BaseReporter):
    
    
    def report(self):
        # gk analysis, 高开
        gkdf = df[df[GDK_COLUMN_NAME] > 0]
        
        # dk analysis，低开
        dkdf = df
        
    def nday_yield(self, ):
        df = self.df
        
        


class TrendAnalyzer(BaseAnalyzer):
    
    def updn(self):
        
        # 当天涨跌限制
        df = self.df
        df[UPDN_COLUMN_NAME] = df['Close'] - df['Open']
    
    def gdk(self):
        df = self.df
        
        # 高低开的Gap
        df[GDK_COLUMN_NAME] = df['Open'] - df['Preclose']
        
        # 高低开当天的涨跌Gap
        self.updn()
