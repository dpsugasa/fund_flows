# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 16:40:07 2018

@author: dpsugasa
"""

"""
Created on Thu Dec 15 15:18:02 2016

Flow of funds analysis; starting with credit

@author: dsugasa
"""

import pandas as pd
from tia.bbg import LocalTerminal
import numpy as np
import matplotlib as plt
from datetime import datetime
from operator import itemgetter
import plotly
import plotly.plotly as py #for plotting
import plotly.graph_objs as go
import plotly.dashboard_objs as dashboard
import plotly.tools as tls
import plotly.figure_factory as ff
import credentials #plotly API details

#set the script start time
start_time = datetime.now()

# set dates, securities, and fields
start_date = '01/01/2012'
end_date = "{:%m/%d/%Y}".format(datetime.now())

#read fund names from .csv
oe = pd.read_csv(r'C:\Users\dpsugasa\WorkFiles\fund_flows\financials_fund_flows\open_end_all_curr.csv',
                   parse_dates=True, infer_datetime_format=True)
oe = oe['Ticker'].values.tolist()
 
etf = 4                
assets = ['open_end']
fields = ['FUND_TOTAL_ASSETS'] #'FUND_TOTAL_ASSETS_CRNCY']


d = {} #dict of original dataframes per asset class
m = {} #list of lists for data matrix
n = {} #list of lists for data matrix 2

for i in assets:
    d[i] = LocalTerminal.get_historical(oe, fields, start_date, end_date, period = 'DAILY',
                                         non_trading_day_fill_option = 'ALL_CALENDAR_DAYS',
                                         non_trading_day_fill_method = 'PREVIOUS_VALUE').as_frame()
    d[nam].columns = d[name].columns.droplevel()
                                   #non_trading_day_fill_option = days,
                                   #non_trading_day_fill_method = fill)