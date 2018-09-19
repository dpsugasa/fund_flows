# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 15:18:02 2016

Flow of funds analysis; starting with credit

@author: dsugasa
"""

import pandas as pd
from tia.bbg import LocalTerminal
import numpy as np
import matplotlib as plt
from collections import OrderedDict
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
oe = pd.read_csv(r'C:\Users\dpsugasa\WorkFiles\fund_flows\financials_fund_flows\open_end_all_curr_mini.csv',
                   parse_dates=True, infer_datetime_format=True)
oe = oe['Ticker'].values.tolist()

fx = ['EURUSD Curncy', 'GBPUSD Curncy']

q = {'open_end': oe,
     
     }


fields_hist = ['FUND_TOTAL_ASSETS']
fields_ref = ['FUND_TOTAL_ASSETS_CRNCY']
fields_fx = ['LAST_PRICE']

d_fx = LocalTerminal.get_historical(fx, fields_fx, start_date, end_date, period = 'DAILY',
                                         non_trading_day_fill_option = 'ALL_CALENDAR_DAYS',
                                         non_trading_day_fill_method = 'PREVIOUS_VALUE').as_frame()
d_fx.columns = d_fx.columns.droplevel(-1)
d = {} #dict of original dataframes per asset class
m = {} #dict of ref data
n = {} #list of lists for data matrix 2

for i, v in q.items():
    d[i] = LocalTerminal.get_historical(v, fields_hist, start_date, end_date, period = 'DAILY',
                                         non_trading_day_fill_option = 'ALL_CALENDAR_DAYS',
                                         non_trading_day_fill_method = 'PREVIOUS_VALUE').as_frame()
    
    d[i].columns = d[i].columns.droplevel(-1)

    
    m[i] = LocalTerminal.get_reference_data(v,fields_ref).as_frame()
    
    
    
    
    d[i].columns = d[i].columns.droplevel()
    
print ("Time to complete:", datetime.now() - start_time)
                                   