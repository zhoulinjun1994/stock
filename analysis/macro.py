#!/usr/bin/env python
# encoding: utf-8

from sqlalchemy import Column, Integer, Float, String, DateTime, BIGINT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import pandas as pd
import argparse
import time
import sys
import numpy as np
from util import *
sys.path.append("..")
from data_collection.basic_classes import *
from data_collection.const import *

engine = create_engine(DB_CONNECT_STRING % (USERNAME, PASSWORD), encoding="utf8", convert_unicode=True)
DB_Session = sessionmaker(bind=engine)
session = DB_Session()

class Stock:
    sec_codes = ""
    name = ""
    df = pd.DataFrame()

    def __init__(self, s_codes, tp="stock"):
        self.sec_codes = s_codes
        if(tp == "stock"):
            self.name = session.query(StockInfo).filter(StockInfo.sec_codes == s_codes).first().name
        elif(tp == "index"):
            self.name = ""
        self.getData(tp)
        recover_factor = getRecoverFactor(self.df['tclose'], self.df['chng_pct'])
        self.df['rec_factor'] = pd.Series(recover_factor).values

    def getData(self, tp):
        sql = ""
        if(tp == "stock"):
            sql = session.query(Market).filter(Market.sec_codes == self.sec_codes)
        elif(tp == "index"):
            sql = session.query(Index).filter(Index.sec_codes == self.sec_codes)
        result = pd.read_sql(sql.statement, sql.session.bind)
        self.df = result.drop_duplicates(['trade_date'], keep='last').set_index('trade_date') \
                .sort_index()

    def profile(self):
        print self.df.describe()

    def pprint(self):
        print self.sec_codes + "  " + self.name

def calc_beta(stock_list, stocks, macro):
    cnt = 0
    for st in stock_list:
        b = Stock(st)
        mergeFrame = pd.concat([macro.df['chng_pct'], b.df['chng_pct']], axis=1, join="inner")
        if b.df.shape[0] < 100:
            continue
        mergeFrame.columns = ['a', 'b']
        model = pd.ols(y=mergeFrame['b'], x=mergeFrame['a'])
        st_beta = Beta(sec_codes = st)
        interval_left = model.beta - 1.96 * model.std_err
        interval_right = model.beta + 1.96 * model.std_err
        st_beta.beta = model.beta.x
        st_beta.beta_lowerbound = interval_left.x
        st_beta.beta_upperbound = interval_right.x
        st_beta.alpha = model.beta.intercept
        st_beta.alpha_lowerbound = interval_left.intercept
        st_beta.alpha_upperbound = interval_right.intercept
        session.add(st_beta)
        print str(cnt) + " " + str(st) + " " + str(st_beta.beta) + " " + str(st_beta.alpha)
        cnt += 1
        if(cnt % 50 == 0):
            session.commit()
    session.commit()

def calc_cov(stock_list, stocks, macro):
    flag = [1 for i in range(0, len(stock_list))]
    cnt = 0
    mergeFrame = macro.df['chng_pct']
    for st in stock_list:
        print str(cnt) + " " + st
        b = Stock(st)
        if b.df.shape[0] < 100:
            flag[cnt] = 0
            cnt += 1
            continue
        mergeFrame = pd.concat([mergeFrame, b.df['chng_pct']], axis=1)
        cnt += 1
    covariance = mergeFrame.cov()
    new_stock_list = ['sh']
    for i in range(0, len(stock_list)):
        if(flag[i] == 1):
            new_stock_list.append(stock_list[i])
    assert(covariance.shape[0] == len(new_stock_list))
    for i in range(1, len(new_stock_list)):
        for j in range(1, len(new_stock_list)):
            res = Covariance(sec_codes1 = new_stock_list[i], sec_codes2 = new_stock_list[j], \
                    cov = covariance.iloc[i][j])
            session.add(res)
        session.commit()

if __name__ == "__main__":
    sql = session.query(StockInfo)
    stocks = pd.read_sql(sql.statement, sql.session.bind)
    stock_list = list(stocks['sec_codes'])
    macro = Stock("sh", tp="index")
    if sys.argv[1] == "-beta":
        calc_beta(stock_list, stocks, macro)
    elif sys.argv[1] == "-cov":
        calc_cov(stock_list, stocks, macro)
