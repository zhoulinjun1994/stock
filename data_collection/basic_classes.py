#!/usr/bin/env python
# encoding: utf-8

from sqlalchemy import Column, Integer, Float, String, DateTime, BIGINT, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func

BaseModel = declarative_base()

class Market(BaseModel):
    __tablename__ = 'market'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    rid = Column(Integer, primary_key=True)
    sec_codes = Column(String(6))
    trade_date = Column(DateTime)
    topen = Column(Float)
    tclose = Column(Float)
    thigh = Column(Float)
    tlow = Column(Float)
    tvolume = Column(BIGINT)
    tvalue = Column(Float)
    chng = Column(Float)
    chng_pct = Column(Float)

class Index(BaseModel):
    __tablename__ = 'marketindex'
    __table_args__ = {
        'mysql_charset': 'utf8'
    }

    rid = Column(Integer, primary_key=True)
    sec_codes = Column(String(6))
    trade_date = Column(DateTime)
    topen = Column(Float)
    tclose = Column(Float)
    thigh = Column(Float)
    tlow = Column(Float)
    tvolume = Column(BIGINT)
    tvalue = Column(Float)
    chng = Column(Float)
    chng_pct = Column(Float)

class Change(BaseModel):
    __tablename__ = "pricechange"
    __table_args__ = {
        'mysql_charset' : "utf8"
    }
    rid = Column(Integer, primary_key = True)
    sec_codes = Column(String(6))
    trade_date = Column(DateTime)
    fiveDchng = Column(Float)
    tenDchng = Column(Float)
    thirtyDchng = Column(Float)
    sixtyDchng = Column(Float)
    ohtwentyDchng = Column(Float)
    thfortyDchng = Column(Float)

class Tradedate(BaseModel):
    __tablename__ = "tradedate"
    __table_args__ = {
        'mysql_charset' : 'utf8'
    }
    date = Column(DateTime, primary_key = True)

class StockInfo(BaseModel):
    __tablename__ = "stockinfo"
    __table_args__ = {
        'mysql_charset' : "utf8"
    }
    sec_codes = Column(String(6), primary_key = True)
    name = Column(String(20))
    industry = Column(String(20))
    area = Column(String(20))
