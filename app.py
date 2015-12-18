#!/usr/bin/env python
# encoding: utf-8

from flask import Flask
from sqlalchemy import Column, Integer, Float, String, DateTime, BIGINT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
import const
import json
from model import Market, Change
from datetime import datetime

app = Flask(__name__)
engine = create_engine(const.DB_CONNECT_STRING % (const.USERNAME, const.PASSWORD), encoding="utf8", convert_unicode=True)
DB_Session = sessionmaker(bind=engine)
session = DB_Session()

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    if isinstance(data, datetime):
                        data = data.strftime('%Y-%m-%d %H:%M:%S')
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

@app.route('/')
def hello():
    return 'hello'

@app.route('/<codes>/<starttime>/<endtime>')
def search(codes, starttime, endtime):
    query = session.query(Market)
    result = query.filter(Market.sec_codes == codes, Market.trade_date >= starttime, Market.trade_date <= endtime).all()
    return json.dumps(result, cls=AlchemyEncoder)

@app.route('/change/<codes>/<starttime>/<endtime>')
def chng(codes, starttime, endtime):
    query = session.query(Change)
    result = query.filter(Change.sec_codes == codes, Change.trade_date >= starttime, Change.trade_date <= endtime).all()
    return json.dumps(result, cls=AlchemyEncoder)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
