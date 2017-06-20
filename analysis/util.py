#!/usr/bin/env python
# encoding: utf-8
import sys
sys.path.append('..')
from data_collection.model import Tradedate
import pandas as pd
import datetime

# Calculate recover factor
def getRecoverFactor(price, pricechng):
    rf = [1.0]
    T = [price[0]]
    for i in range(1, len(price)):
        tmp = price[i-1] * (1 + 0.01 * pricechng[i])
        if abs(tmp - price[i]) < 0.015:
            rf.append(rf[-1])
            T.append(price[i] * rf[i])
        else:
            T.append(T[-1] * (1 + 0.01 * pricechng[i]))
            rf.append(T[-1] / price[i])
    return rf

# Get all weeks start day and end day. Notice that the week must be complete
# i.e. Monday to Friday are all trade date.
def getCompWeekStartEnd(session, s_time, e_time):
    query = session.query(Tradedate)
    sql = query.filter(Tradedate.date >= s_time, Tradedate.date <= e_time)
    result = pd.read_sql(sql.statement, sql.session.bind)['date']
    week_start_end = []
    for i in range(len(result) - 4):
        d1 = result[i].to_pydatetime()
        d2 = result[i+4].to_pydatetime()
        if d1 + datetime.timedelta(days = 4) == d2:
            week_start_end.append((d1, d2))
    return week_start_end

# Get all weeks start day and end day. The week need't to be complete.
def getWeekStartEnd(session, s_time, e_time):
    query = session.query(Tradedate)
    sql = query.filter(Tradedate.date >= s_time, Tradedate.date <= e_time)
    result = pd.read_sql(sql.statement, sql.session.bind)['date']
    week_start_end = []
    tmp_week = result[0].to_pydatetime().date().isocalendar()[1]
    tmp_start = result[0]
    for i in range(len(result)):
        d = result[i].to_pydatetime().date()
        week = d.isocalendar()[1]
        if week != tmp_week:
            week_start_end.append((tmp_start, result[i-1]))
            tmp_start = result[i]
            tmp_week = week
    return week_start_end


# Get the period percentage change of a stock
def getPeriodChange(stock, s_time, e_time):
    day_chng_pct = stock.df[s_time : e_time]['chng_pct']
    if len(day_chng_pct) == 0:
        return 0.0
    else:
        return reduce(lambda x,y: x*y, [(num * 0.01 + 1.0) for num in day_chng_pct]) - 1.0

# If the stock is stop on the first day or last day
def getStockStop(stock, s_time, e_time):
    return not (s_time in stock.df.index and e_time in stock.df.index)


