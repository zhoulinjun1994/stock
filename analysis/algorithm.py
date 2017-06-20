#!/usr/bin/env python
# encoding: utf-8
import copy
from macro import Stock
from scipy.stats import pearsonr
from util import *
import numpy as np
from heapq import nlargest
import statsmodels.api as sm
import math
import datetime
import time

class Algorithm:
    stock_list = []
    training_sdate = ''
    training_edate = ''
    backtest_sdate = ''
    backtest_edate = ''

    def __init__(self, st_list, t_sdate, t_edate, b_sdate, b_edate):
        t_days = (datetime.datetime.strptime(t_edate, '%Y%m%d') - \
                datetime.datetime.strptime(t_sdate, '%Y%m%d')).days
        b_days = (datetime.datetime.strptime(b_edate, '%Y%m%d') - \
                datetime.datetime.strptime(b_sdate, '%Y%m%d')).days
        for index, code in enumerate(st_list):
            print 'Loading Stock %d: #%s...' % (index, code)
            s = Stock(code, 'stock')
            if s.df.shape[0] > (t_days + b_days) / 2: # If too little data, delete it.
                self.stock_list.append(s)
        print len(self.stock_list)
        self.training_sdate = t_sdate
        self.training_edate = t_edate
        self.backtest_sdate = b_sdate
        self.backtest_edate = b_edate

    def interface(self):
        pass

class Pearson_GGR(Algorithm):
    def calc_corr(self, session):
        # Construct the correlation matrix
        week_start_end = getCompWeekStartEnd(session, self.training_sdate, self.training_edate)
        data = []
        for i in range(len(self.stock_list)):
            data1 = []
            for w_start, w_end in week_start_end:
                w_start = str(w_start.strftime('%Y-%m-%d'))
                w_end = str(w_end.strftime('%Y-%m-%d'))
                if not getStockStop(self.stock_list[i], w_start, w_end):
                    data1.append(getPeriodChange(self.stock_list[i], w_start, w_end))
                else:
                    data1.append(np.nan)
            data.append(data1)
        info = pd.DataFrame(np.array(data).T)
        corr = info.corr()
        return info, corr.values

    def construct_pairs(self, corr, sim_stocks=10):
        pair_list = []
        for i in range(len(self.stock_list)):
            corr[i][i] = 0.0
            pair_list.append(nlargest(sim_stocks, range(len(corr[i])), corr[i].__getitem__))
        return pair_list

    def calc_beta(self, p_chng, pair_list):
        beta = np.zeros(len(self.stock_list))
        for i in range(len(self.stock_list)):
            tmp_df = pd.DataFrame(p_chng, columns = [i]).copy()
            tmp_df.insert(1, 'pair', p_chng[pair_list[i]].mean(axis=1))
            tmp_df['intercept'] = 1.0
            beta[i] = sm.OLS(tmp_df.iloc[:,[1]], tmp_df.iloc[:,[0,2]], missing='drop').fit().params[0]
            del tmp_df
        return beta

    def backtest(self, session, pair_list, beta, decile=10):
        # Collect Backtest Data
        week_start_end = getWeekStartEnd(session, self.backtest_sdate, self.backtest_edate)
        data = []
        for i in range(len(self.stock_list)):
            data1 = []
            for w_start, w_end in week_start_end:
                w_start = str(w_start.strftime('%Y-%m-%d'))
                w_end = str(w_end.strftime('%Y-%m-%d'))
                if not getStockStop(self.stock_list[i], w_start, w_end):
                    data1.append(getPeriodChange(self.stock_list[i], w_start, w_end))
                else:
                    data1.append(np.nan)
            data.append(data1)
        p_chng = pd.DataFrame(np.array(data).T)

        # Execute Strategy - Construct return divergence
        benefit = np.zeros(decile)
        pair_df = pd.DataFrame() # Dijt
        for i in range(len(self.stock_list)):
            tmp_df = beta[i] * p_chng[i] - p_chng[pair_list[i]].mean(axis=1)
            pair_df[i] = tmp_df

        # Execute Strategy - Consturct perfect portfolio as time flows
        for i in range(1, pair_df.shape[0]):
            benefit_per_week = np.zeros(decile)
            week_div = pair_df.iloc[i-1][:]
            mapping = []
            for index, value in enumerate(week_div):
                if not math.isnan(value):
                    mapping.append(index)
            res = pd.Series.argsort(week_div)
            group_num = (max(res) + 1) / decile
            cnt = 0
            has_value_cnt = 0
            group = 0
            for index in res:
                if cnt == group_num:
                    benefit_per_week[group] = benefit_per_week[group] / float(has_value_cnt)
                    cnt = 0
                    has_value_cnt = 0
                    group += 1
                if group == decile:
                    break
                if index != -1:
                    if not math.isnan(pair_df.iloc[i][mapping[index]]):
                        benefit_per_week[group] += pair_df.iloc[i][mapping[index]]
                        has_value_cnt += 1
                    cnt += 1
            benefit = benefit + benefit_per_week
        benefit = benefit / (pair_df.shape[0] - 1)
        return benefit

    def interface(self, session):
        p_chng, corr = self.calc_corr(session)
        #corr = np.load('../mid_data/corr_hs300.npy')
        pair_list = self.construct_pairs(corr, 20)
        beta = self.calc_beta(p_chng, pair_list)
        benefit = self.backtest(session, pair_list, beta, 10)
        print benefit




