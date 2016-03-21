#!/usr/bin/env python
# encoding: utf-8

import tushare as ts
from sqlalchemy import Column, Integer, Float, String, DateTime, BIGINT, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func
from basic_classes import *
import const
import json
import sys
import urllib2
import string
import time
import datetime
import os

#Connect Mysql
engine = create_engine(const.DB_CONNECT_STRING % (const.USERNAME, const.PASSWORD), encoding="utf8", convert_unicode=True)
DB_Session = sessionmaker(bind=engine)
session = DB_Session()

def view_bar(num=1, sum=100, bar_word=":"):
    rate = float(num) / float(sum)
    rate_num = int(rate * 100)
    print '\r%d%% :' %(rate_num),
    for i in range(0, int(rate_num / 5)):
        os.write(1, bar_word)
    sys.stdout.flush()

def init_db():
    BaseModel.metadata.create_all(engine)

def drop_db():
    BaseModel.metadata.drop_all(engine)

def getData(timestr):
    pass

def getPeriodData(start, end):
    starttimestr = start[0:4] + '-' + start[4:6] + '-' + start[6:8]
    endtimestr = end[0:4] + '-' + end[4:6] + '-' + end[6:8]
    stock_list = list(ts.get_stock_basics().index)
    total = len(stock_list)
    cnt = 0
    for s in stock_list:
        print "Current Stock Number: " + s
        cnt += 1
        if(cnt % 100 == 0):
            view_bar(cnt, total)
        item = ts.get_hist_data(code=s, start=starttimestr, end=endtimestr)
        item2 = ts.get_h_data(code=s, start=starttimestr, end=endtimestr)
        if(item is None or item2 is None):
            continue
        timeperiod = list(item.index)
        for t in timeperiod:
            session.add(Market(sec_codes = s, trade_date = t,\
                    topen = item['open'][t], tclose = item['close'][t],\
                    thigh = item['high'][t], tlow = item['low'][t], \
                    tvolume = item['volume'][t], tvalue = float(item2['amount'][t] / 1000.0),\
                    chng = item['price_change'][t],  chng_pct = item['p_change'][t]))
        session.commit()

def getIndexPeriodData(start, end):
    starttimestr = start[0:4] + '-' + start[4:6] + '-' + start[6:8]
    endtimestr = end[0:4] + '-' + end[4:6] + '-' + end[6:8]
    stock_list = ['sh', 'sz', 'hs300', 'sz50', 'zxb', 'cyb']
    for s in stock_list:
        print "Current Stock Number: " + s
        item = ts.get_hist_data(code=s, start=starttimestr, end=endtimestr)
        if(item is None):
            continue
        timeperiod = list(item.index)
        for t in timeperiod:
            session.add(Index(sec_codes = s, trade_date = t,\
                    topen = item['open'][t], tclose = item['close'][t],\
                    thigh = item['high'][t], tlow = item['low'][t], \
                    tvolume = item['volume'][t], tvalue = None,\
                    chng = item['price_change'][t],  chng_pct = item['p_change'][t]))
        session.commit()


def deleteData(timestr):
    newtimestr = timestr[0:4] + '-' + timestr[4:6] + '-' + timestr[6:8]
    query = session.query(Market)
    query.filter(Market.trade_date == newtimestr).delete()
    session.commit()

def deletePeriodData(start, end):
    dstart = datetime.datetime.strptime(start, "%Y%m%d")
    dend = datetime.datetime.strptime(end, "%Y%m%d")
    while((dend - dstart).days >= 0):
        deleteData(datetime.datetime.strftime(dstart, "%Y%m%d"))
        dstart = dstart + datetime.timedelta(days = 1)

def maxDate():
    query = session.query(func.max(Market.trade_date)).all()
    print query[0]

def addTradeDate(start, end):
    print "Processing..."
    dstart = datetime.datetime.strptime(start, "%Y%m%d")
    dend = datetime.datetime.strptime(end, "%Y%m%d")
    while((dend - dstart).days >= 0):
        tmp = datetime.datetime.strftime(dstart, "%Y-%m-%d")
        query = session.query(func.count('*')).filter(Market.trade_date == tmp).scalar()
        if(query > 0):
            session.add(Tradedate(date = tmp))
        dstart = dstart + datetime.timedelta(days = 1)
    session.commit()

def calcChange(sec_codes, start, end, seq = None, split = 0):
    MAX_DATE = 240
    DATE_INDEX = [5, 10, 30, 60, 120, 240]
    dstart = datetime.datetime.strptime(start, "%Y%m%d")
    dend = datetime.datetime.strptime(end, "%Y%m%d")
    dateseq = None
    tmpstart = datetime.datetime.strftime(dstart, "%Y-%m-%d")
    tmpend = datetime.datetime.strftime(dend, "%Y-%m-%d")
    if(seq == None):
        dateseq = []
        tmp = datetime.datetime.strftime(dstart, "%Y-%m-%d")
        cnt = 0
        flag = 0
        while(flag == 0 and cnt < MAX_DATE):
            query = session.query(func.max(Tradedate.date)).filter(Tradedate.date < tmp)
            if(query.all()[0][0] != None):
                dateseq.append(datetime.datetime.strftime(query.all()[0][0], "%Y-%m-%d"))
                tmp = datetime.datetime.strftime(query.all()[0][0], "%Y-%m-%d")
            else:
                flag = 1
            cnt += 1
        dateseq.reverse()
        split = len(dateseq)
        dstart = datetime.datetime.strptime(start, "%Y%m%d")
        query = session.query(Tradedate).filter(Tradedate.date <= tmpend, Tradedate.date >= tmpstart).all()
        query.sort(lambda x,y: cmp(x.date, y.date))
        for item in query:
            dateseq.append(datetime.datetime.strftime(item.date, "%Y-%m-%d"))
    else:
        dateseq = seq
    if(len(dateseq) < DATE_INDEX[0]):
        print "Error: Dataset is too small!"
        return
    #Next, to calculate the benefit according to dateseq
    data = session.query(Market).filter(Market.trade_date <= dateseq[-1], Market.trade_date >= dateseq[0], Market.sec_codes == sec_codes).all()
    data.sort(lambda x, y: cmp(x.trade_date, y.trade_date))
    dateseq_dict = {}
    for i in range(0, len(dateseq)):
        dateseq_dict[dateseq[i]] = i
    #calculate 5-day change
    info = []
    for item in data:
        tmp = datetime.datetime.strftime(item.trade_date, "%Y-%m-%d")
        info.append(dateseq_dict[tmp])
    info_dict = {}
    for i in range(0, len(info)):
        info_dict[info[i]] = i
    data_exist = [False for i in range(0, len(dateseq))]
    for i in info:
        data_exist[i] = True
    chng5 = [None for i in range(0, 5)]
    change_p = 1.0
    for i in range(1, 6):
        change_p *= ((data[info_dict[i]].chng_pct * 0.01 + 1.0) if data_exist[i] else 1.0)
    chng5.append(change_p)
    for i in range(6, len(dateseq)):
        change_p *= ((data[info_dict[i]].chng_pct * 0.01 + 1.0) if data_exist[i] else 1.0)
        change_p /= ((data[info_dict[i - 5]].chng_pct * 0.01 + 1.0) if data_exist[i - 5] else 1.0)
        chng5.append(change_p)
    chng_seq = []
    chng_seq.append(chng5)
    for i in range(1, len(DATE_INDEX)):
        chng_tmp = []
        for j in range(0, len(dateseq)):
            if(j - DATE_INDEX[i] >= 0):
                chng = 1.0
                for k in range(0, DATE_INDEX[i] / DATE_INDEX[i-1]):
                    chng *= chng_seq[i-1][j - k * DATE_INDEX[i-1]]
                chng_tmp.append(chng)
            else:
                chng_tmp.append(None)
        chng_seq.append(chng_tmp)
    session.query(Change).filter(Change.sec_codes == sec_codes, Change.trade_date >= tmpstart, Change.trade_date <= tmpend).delete()
    for i in range(split, len(dateseq)):
        session.add(Change(sec_codes=sec_codes, trade_date=dateseq[i], fiveDchng=chng_seq[0][i], \
                tenDchng=chng_seq[1][i], thirtyDchng=chng_seq[2][i], sixtyDchng=chng_seq[3][i], \
                ohtwentyDchng=chng_seq[4][i], thfortyDchng=chng_seq[5][i]))
    session.commit()
    return [dateseq, split]

def calcChangeAll(start, end):
    query = session.query(Market.sec_codes).group_by(Market.sec_codes).all()
    [dateseq, split] = calcChange(query[0][0], start, end)
    for i in range(1, len(query)):
        if(i % 20 == 0):
            view_bar(i, len(query))
        calcChange(query[i][0], start, end, dateseq, split)

def getStockInfo():
    session.query(StockInfo).delete()
    res = ts.get_stock_basics().iloc[:, :3]
    inx = res.index
    for i in range(0, res.shape[0]):
        session.add(StockInfo(sec_codes=inx[i], name=res.iloc[i]['name'],\
                industry=res.iloc[i]['industry'], area=res.iloc[i]['area']))
    session.commit()

if __name__ == "__main__":
    if(sys.argv[1] == "-init"):
        init_db()
    elif(sys.argv[1] == "-drop"):
        drop_db()
    elif(sys.argv[1] == "-add"):
        getData(sys.argv[2])
    elif(sys.argv[1] == "-addall"):
        getPeriodData(sys.argv[2], sys.argv[3])
    elif(sys.argv[1] == "-del"):
        deleteData(sys.argv[2])
    elif(sys.argv[1] == "-delall"):
        deletePeriodData(sys.argv[2], sys.argv[3])
    elif(sys.argv[1] == "-maxdate"):
        maxDate()
    elif(sys.argv[1] == "-addtradedate"):
        addTradeDate(sys.argv[2], sys.argv[3])
    elif(sys.argv[1] == "-calcchange"):
        calcChange(sys.argv[2], sys.argv[3], sys.argv[4])
    elif(sys.argv[1] == "-calcchangeall"):
        calcChangeAll(sys.argv[2], sys.argv[3])
    elif(sys.argv[1] == "-getstockinfo"):
        getStockInfo()
    elif(sys.argv[1] == "-getindex"):
        getIndexPeriodData(sys.argv[2], sys.argv[3])
