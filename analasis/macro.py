#!/usr/bin/env python
# encoding: utf-8

from sqlalchemy import Column, Integer, Float, String, DateTime, BIGINT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import pandas as pd
import time
import sys
sys.path.append("..")
from data_collection.basic_classes import *
from data_collection.const import *

engine = create_engine(DB_CONNECT_STRING % (USERNAME, PASSWORD), encoding="utf8", convert_unicode=True)
DB_Session = sessionmaker(bind=engine)
session = DB_Session()

class Stock:
    sec_codes = ""
    name = ""
    df = 0

    def __init__(self, s_codes, tp="stock"):
        self.sec_codes = s_codes
        if(tp == "stock"):
            self.name = session.query(StockInfo).filter(StockInfo.sec_codes == s_codes).first().name
        elif(tp == "index"):
            self.name = ""
        self.getData(tp)

    def getData(self, tp):
        sql = ""
        if(tp == "stock"):
            sql = session.query(Market).filter(Market.sec_codes == self.sec_codes)
        elif(tp == "index"):
            sql = session.query(Index).filter(Index.sec_codes == self.sec_codes)
        result = pd.read_sql(sql.statement, sql.session.bind)
        self.df = result.set_index('trade_date')

    def profile(self):
        print self.df.describe()

    def pprint(self):
        print self.sec_codes + "  " + self.name

if __name__ == "__main__":
    sql = session.query(StockInfo)
    stocks = pd.read_sql(sql.statement, sql.session.bind)
    stock_list = list(stocks['sec_codes'])
    macro = Stock("sh", tp="index")
    beta = {}
    for st in stock_list:
        if st >= '600000' and st <= '600010':
            b = Stock(st)
            mergeFrame = pd.concat([macro.df['chng_pct'], b.df['chng_pct']], axis=1, join="inner")
            mergeFrame.columns = ['a', 'b']
            model = pd.ols(y=mergeFrame['b'], x=mergeFrame['a'])
            print b.sec_codes + " " + b.name + " " + str(model.beta.x) + " " + str(model.beta.intercept)
