#!/usr/bin/env python
# encoding: utf-8

from util import *
from macro import Stock
import tushare as ts
from sqlalchemy import Column, Integer, Float, String, DateTime, BIGINT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime
import argparse
import time
import sys
import numpy as np
from util import *
from algorithm import *
sys.path.append("..")
from data_collection.basic_classes import *
from data_collection.const import *

if __name__ == '__main__':
    engine = create_engine(DB_CONNECT_STRING % (USERNAME, PASSWORD), encoding="utf8", convert_unicode=True)
    DB_Session = sessionmaker(bind=engine)
    session = DB_Session()
    hs300_list = ts.get_hs300s()['code']
    p = Pearson_GGR(hs300_list, '20130701', '20151231', '20160101', '20170601')
    p_list = p.interface(session)

