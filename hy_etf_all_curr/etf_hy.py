# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 15:18:02 2016

Flow of funds analysis; starting with credit

@author: dsugasa
"""

import pandas as pd
from tia.bbg import LocalTerminal
import numpy as np
from scipy.stats.mstats import winsorize
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
date_now =  "{:%m_%d_%Y}".format(datetime.now())

def zscore(series, time='365d'):
    score =(series - series.rolling(window=time).mean())/series.rolling(window=time).std()
    return score

# set dates, securities, and fields
start_date = '01/01/2012'
end_date = "{:%m/%d/%Y}".format(datetime.now())

#read fund names from .csv
hy_etf = pd.read_csv(r'C:\Users\dpsugasa\WorkFiles\fund_flows\hy_etf_all_curr\hy_etf_all_curr.csv',
                   parse_dates=True, infer_datetime_format=True)
hy_etf = hy_etf['Ticker'].values.tolist()

fx = ['EURUSD Curncy',
      'GBPUSD Curncy',
      'CADUSD Curncy',
      'JPYUSD Curncy',
      'CHFUSD Curncy']

q = {'hy_etf': hy_etf,
     #'booty': oe
     
     }


fields_hist = ['FUND_TOTAL_ASSETS']
fields_ref = ['FUND_TOTAL_ASSETS_CRNCY']
fields_fx = ['LAST_PRICE']

d_fx = LocalTerminal.get_historical(fx, fields_fx, start_date, end_date, period = 'DAILY',
                                         non_trading_day_fill_option = 'ALL_CALENDAR_DAYS',
                                         non_trading_day_fill_method = 'PREVIOUS_VALUE').as_frame()
d_fx.columns = d_fx.columns.droplevel(-1)
d_fx = d_fx.rename(columns = {'EURUSD Curncy':'EUR',
                              'GBPUSD Curncy':'GBP',
                              'CADUSD Curncy':'CAD',
                              'JPYUSD Curncy':'JPY',
                              'CHFUSD Curncy':'CHF'})
d_fx['USD'] = 1.0


d = {} #dict of original dataframes per asset class
m = {} #dict of ref data
b = {} #list of lists for asset diffs
p = {} #list of list for $asset diffs
f = {} #simplified asset dicts
r = {} #daily rate of change dict
u = {} #weekly rate of change
pq = {} #monthly rate of change
ip = {} #quarterly rate of change
lp = {} #yearly rate of change


idx = pd.IndexSlice

for i, v in q.items():
    #get ref data and underlying currency
    m[i] = LocalTerminal.get_reference_data(v,fields_ref).as_frame()
    #get asset data and calculate $Assets on a daily basis
    d[i] = LocalTerminal.get_historical(v, fields_hist, start_date, end_date, period = 'DAILY',
                                         non_trading_day_fill_option = 'ALL_CALENDAR_DAYS',
                                         non_trading_day_fill_method = 'PREVIOUS_VALUE').as_frame()
    d[i].columns = d[i].columns.droplevel(-1)

    d[i] = d[i].unstack().to_frame()
    d[i].columns = d[i].columns.astype(str)
    d[i].columns = d[i].columns.str.replace('0','Assets')
    d[i]['fx'] = m[i]['FUND_TOTAL_ASSETS_CRNCY'].loc[d[i].index.get_level_values(0)].values
    d[i]['rate'] = d_fx.lookup(d[i].index.get_level_values(1), d[i]['fx'])
    d[i]['$Assets'] = d[i]['rate']*d[i]['Assets']
    
    f[i] = d[i].unstack(0)
    f[i] = f[i].swaplevel(1,0,axis=1)
    f[i] = f[i].drop(['fx', 'rate'], axis=1, level=1)
    f[i] = f[i].stack(0)
    
    b[i] = f[i]['$Assets'].unstack().fillna(0).apply(sum, axis=1).to_frame()
    b[i].columns = ['tot_$assets']
    b[i]['$assets_pct_chg'] = b[i]['tot_$assets'].pct_change()
    b[i]['$assets_log_chg'] = np.log(1 + b[i]['tot_$assets'].pct_change())
    b[i]['$assets_log_chg'] = winsorize(b[i]['$assets_log_chg'], limits = (0.01, 0.01))
    b[i]['$diff'] = b[i]['tot_$assets'].diff()
            
#    p['$assets_pct_chg'] = f[i]['$Assets'].unstack().pct_change()
#    f[i]['assets_pct_chg'] = b['assets_pct_chg'].stack()
#    f[i]['$assets_pct_chg'] = p['$assets_pct_chg'].stack()
      
    #daily changes with zscores
    r[i] = b[i][['$assets_log_chg', '$diff']]
    r[i]['scr_1y'] = zscore(r[i]['$assets_log_chg'])
    r[i]['scr_6m'] = zscore(r[i]['$assets_log_chg'], '180d')
     
    #create weekly changes
    u[i] = b[i][['$assets_log_chg', '$diff']].resample('W').sum()
    u[i]['scr_1y'] = zscore(u[i]['$assets_log_chg'])
    u[i]['scr_6m'] = zscore(u[i]['$assets_log_chg'], '180d') 
    
    #create monthly changes
    pq[i] = b[i][['$assets_log_chg', '$diff']].resample('BM').sum()
    pq[i]['scr_1y'] = zscore(pq[i]['$assets_log_chg'])
    pq[i]['scr_6m'] = zscore(pq[i]['$assets_log_chg'], '180d') 
    
    #create quaeterly changes
    ip[i] = b[i][['$assets_log_chg', '$diff']].resample('BQ').sum()
    ip[i]['scr_1y'] = zscore(ip[i]['$assets_log_chg'])
     
       
    #create business yearly changes
    lp[i] = b[i][['$assets_log_chg', '$diff']].resample('BY').sum()

    
                
#create plots
    #if j[i]['scr_1y'].tail(1).item() >= 2.0 or d[i]['scr_1y'].tail(1).item() <= -2.0:
        #plot the historical 1 year z-score
    trace1 = go.Bar(
                    x = r[i]['$assets_log_chg'].index,
                    y = r[i]['scr_1y'].values,
                    name = 'Daily Change',
                    #color = '#4155f4'
#                    line = dict(
#                                color = ('#4155f4'),
#                                width = 1.5)
                    ) 

    trace2 = go.Scatter(
                        x = b[i]['tot_$assets'].index,
                        y = b[i]['tot_$assets'].values,
                        name = 'Total Assets',
                        yaxis = 'y2',
                        line = dict(
                                    color = ('#ccccff'),
                                    width = 1.0,
                                    ),
                        fill = 'tonexty',
                        opacity = 0.05,
                       
                        
    
    )       
        
    layout  = {'title' : f'{i} daily change - {date_now}',
                   'xaxis' : {'title' : 'Date', 'type': 'date'},
                   'yaxis' : {'title' : 'Z-Score'},
                   'yaxis2' : {'title' : 'Assets',
                               'overlaying' : 'y',
                               'side'   : 'right'},
                   'shapes': [{'type': 'rect',
                              'x0': r[i]['scr_1y'].index[0],
                              'y0': -2,
                              'x1': r[i]['scr_1y'].index[-1],
                              'y1': 2,
                              'name': 'Z-range',
                              'line': {
                                      'color': '#f48641',
                                      'width': 2,},
                                      'fillcolor': '#f4ad42',
                                      'opacity': 0.25,
                                      },]
                   }
    
    data = [trace1, trace2]
    figure = go.Figure(data=data, layout=layout)
    py.iplot(figure, filename = f'fund_flow/{date_now}/{i}/Daily Change')

    trace1 = go.Bar(
                    x = u[i]['$assets_log_chg'].index,
                    y = u[i]['scr_1y'].values,
                    name = 'Weekly Change',
                    #color = '#4155f4'
#                    line = dict(
#                                color = ('#4155f4'),
#                                width = 1.5)
                    ) 

    trace2 = go.Scatter(
                        x = b[i]['tot_$assets'].index,
                        y = b[i]['tot_$assets'].values,
                        name = 'Total Assets',
                        yaxis = 'y2',
                        line = dict(
                                    color = ('#ccccff'),
                                    width = 1.0,
                                    ),
                        fill = 'tonexty',
                        opacity = 0.05,
                       
                        
    
    )       
        
    layout  = {'title' : f'{i} weekly change - {date_now}',
                   'xaxis' : {'title' : 'Date', 'type': 'date'},
                   'yaxis' : {'title' : 'Z-Score'},
                   'yaxis2' : {'title' : 'Assets',
                               'overlaying' : 'y',
                               'side'   : 'right'},
                   'shapes': [{'type': 'rect',
                              'x0': u[i]['scr_1y'].index[0],
                              'y0': -2,
                              'x1': u[i]['scr_1y'].index[-1],
                              'y1': 2,
                              'name': 'Z-range',
                              'line': {
                                      'color': '#f48641',
                                      'width': 2,},
                                      'fillcolor': '#f4ad42',
                                      'opacity': 0.25,
                                      },]
                   }
    
    data = [trace1, trace2]
    figure = go.Figure(data=data, layout=layout)
    py.iplot(figure, filename = f'fund_flow/{date_now}/{i}/Weekly Change')


    trace1 = go.Bar(
                    x = pq[i]['$assets_log_chg'].index,
                    y = pq[i]['scr_1y'].values,
                    name = 'Monthly Change',
                    #color = '#4155f4'
#                    line = dict(
#                                color = ('#4155f4'),
#                                width = 1.5)
                    ) 

    trace2 = go.Scatter(
                        x = b[i]['tot_$assets'].index,
                        y = b[i]['tot_$assets'].values,
                        name = 'Total Assets',
                        yaxis = 'y2',
                        line = dict(
                                    color = ('#ccccff'),
                                    width = 1.0,
                                    ),
                        fill = 'tonexty',
                        opacity = 0.05,
                       
                        
    
    )       
        
    layout  = {'title' : f'{i} monthly change - {date_now}',
                   'xaxis' : {'title' : 'Date', 'type': 'date'},
                   'yaxis' : {'title' : 'Z-Score'},
                   'yaxis2' : {'title' : 'Assets',
                               'overlaying' : 'y',
                               'side'   : 'right'},
                   'shapes': [{'type': 'rect',
                              'x0': pq[i]['scr_1y'].index[0],
                              'y0': -2,
                              'x1': pq[i]['scr_1y'].index[-1],
                              'y1': 2,
                              'name': 'Z-range',
                              'line': {
                                      'color': '#f48641',
                                      'width': 2,},
                                      'fillcolor': '#f4ad42',
                                      'opacity': 0.25,
                                      },]
                   }
    
    data = [trace1, trace2]
    figure = go.Figure(data=data, layout=layout)
    py.iplot(figure, filename = f'fund_flow/{date_now}/{i}/Monthly Change')






print ("Time to complete:", datetime.now() - start_time)


