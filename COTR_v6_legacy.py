# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 16:14:55 2018

@author: dsugasa

#updating COTR to use legacy format; simplified version of futures positioning. Computes Z-scores,
publishes a PLOTLY dashboard, and creates PLOTLY 1y and 3y historical Z-score graphs.

"""

import pandas as pd
import numpy as np
from datetime import datetime #for dates
import quandl #for data
quandl.ApiConfig.api_key = '#####' #insert personal API Key
import plotly
import plotly.plotly as py #for plotting
import plotly.graph_objs as go
import plotly.dashboard_objs as dashboard
plotly.tools.set_credentials_file(username='#####', api_key='#####') #insert personal plotly credentials
import plotly.tools as tls
import plotly.figure_factory as ff
tls.embed('https://plot.ly/######/1/') #insert personal username


#set the script start time
start_time = datetime.now()

#set CFTC futures contracts

# __________ FUTURES quandlcode:
#Related to fut_dict and fut_decode() for code slang.
#

IDs ={
'fed'   :       '045741',           #  CME 30 day Fed Funds
'1meu'  :       '032741',           #  CME 1mth Eurodollars
'3meu'  :       '132741',           #  CME 3mth Eurodollars
'us10y' :       '043602',           #  CBT 10yr Treasury
'us2y'  :       '042601',           #  CBT 2yr Treasury
'us5y'  :       '044601',           #  CBT 5yr Treasury
'yc1030':       '531601',           #  UST Yield Curve 30_10
'yc0230':       '532601',           #  UST Yield Curve 30_2
'ust'   :       '020601',           #  CME/UST
'spx'   :       '13874P',           #  CME S&P 500 Consolidated; combines SPX and e-mini
'cad'   :       '090741',           #  CME
'aud'   :       '232741',           #  CME
'mxn'   :       '095741',           #  CME
'gbp'   :       '096742',           #  CME
'eur'   :       '099741',           #  CME
'chf'   :       '092741',           #  CME
'jpy'   :       '097741',           #  CME
'nzd'   :       '112741',           #  CME
'rub'   :       '089741',           #  CME
'brl'   :       '102741',           #  CME
'zar'   :       '122741',           #  CME
'xau'   :       '088691',           #  CME/COMEX Gold
'xag'   :       '084691',           #  CME/COMEX Silver
'wti'   :       '067651',           #  NYME WTI Crude Oil 
'ngas'  :       '023651',           #  NYME Natural Gas
'rbob'  :       '11165J',           #  NYME RBOB Gasoline 
'plat'  :       '076651',           #  NYME Platinum
#'alum'  :       '191691',           #  NYME Aluminum
'sug'   :       '080732',           #  ICUS Sugar No. 11
'choc'  :       '073732',           #  ICUS Cocoa
'coff'  :       '083731',           #  ICUS Coffee
'corn'  :       '002602',           #  CBT Corn
'catt'  :       '057642',           #  CME Live Cattle
'hogs'  :       '054642',           #  CME Lean Hogs
'oj'    :       '040701',           #  ICUS Frozen Conc OJ
'nk$'   :       '240741',           #  CME/Nikkei $
'nky'   :       '240743',           #  CME/Nikkei Yen
'rus'   :       '239742',           #  Russell 2000
'dow'   :       '12460P',           #  CBOT/DJIA Consolidated; combines the full contract and mini
'ndx'   :       '20974P',           #  CBOT/Nasdaq-100 Consolidated; combines full contract and mini
'usd'   :       '098662',           #  ICE/DXY
'cop'   :       '085692',           #  Copper
'vix'   :       '1170E1',           #  VX
}


quandl = quandl.get

def cotr_get( futures, type='FO' ):
     '''Get CFTC Commitment of Traders Report COTR.'''
     #  Report for futures only requested by type "F".
     #  Report for both futures and options requested by type "FO".
     #  e.g. 'CFTC/GC_FO_ALL' for CFTC COTR: Gold futures and options.
     #
     #  Traders' option positions are computed on a futures-equivalent basis
     #  using delta factors supplied by the exchanges.
     quandlcode = 'CFTC/' + futures + '_' + type + '_L_ALL' #L denotes legacy format
     return quandl( quandlcode )
 
def cotr_length_legacy( futures ):
     '''Extract market position from CFTC Commitment of Traders Report.'''
     cotr = cotr_get( futures )
     #  Report for both futures and options requested by implicit "FO".
     #
     #  For directionality we use these categories:
     
     longs = cotr['Noncommercial Long']
     shorts = cotr['Noncommercial Short']
         
     return ( longs - shorts )

###Add futures z_scores for various macro futures contracts

d = {} #dict of original dataframes per ID
m = {} #list of lists for data matrix
  
#calculate Z-Scores for various durations      
for name, code in IDs.items():     
    d[name] = cotr_get(str(code))
    d[name]['length'] = cotr_length_legacy(code)
    d[name]['scr_ltd'] = (d[name]['length'] - d[name]['length'].mean())/d[name]['length'].std()
    d[name]['scr_1y'] = (d[name]['length'] - d[name]['length'].rolling('365d').mean())/d[name]['length'].rolling('365d').std()
    d[name]['scr_3y'] = (d[name]['length'] - d[name]['length'].rolling('1095d').mean())/d[name]['length'].rolling('1095d').std()
    
    m[name] = [name, np.round(d[name]['scr_1y'].tail(1).item(),4), np.round(d[name]['scr_1y'].iloc[-2].item(),4), np.round(d[name]['scr_1y'].iloc[-5].item(),4)]
    
#build data matrix
data_matrix = [['COTR','Z_score_1y', '1y Z - 1 week ago', '1y Z - 1 month ago' ]]
for i, j in m.items():
    data_matrix.append(j)

                       
colorscale = [[0, '#2E4053'],[.5,  '#ccccff'],[1, '#ffffff']]
table = ff.create_table(data_matrix, height_constant = 20, colorscale=colorscale)
py.iplot(table, filename='COTR/Analytics_Dashboard/Analytics_Legacy')

dboard = dashboard.Dashboard()

box_1 = {
        'type' : 'box',
        'boxType':'plot',
        'fileId': 'dpsugasa:888',
        'shareKey': None,
        'title': 'COTR Positioning Z-Scores'
}

dboard.insert(box_1)
dboard['settings']['title'] = 'COTR_Z-Scores - Legacy Methodology'
py.dashboard_ops.upload(dboard, 'COTR_Z_Scores - Legacy Methodology')

#graph individual names (1y and 3y) with 1 year Z-scores greater than 2 sds
date_now =  "{:%m_%d_%Y}".format(d[name].last_valid_index())
for i in d.keys():
    if d[i]['scr_1y'].tail(1).item() >= 2.0 or d[i]['scr_1y'].tail(1).item() <= -2.0:
        #plot the historical 1 year z-score
        trace1 = go.Scatter(
                x = d[i]['scr_1y'].index,
                y = d[i]['scr_1y'].values,
                name = 'Z-scores',
                line = dict(
                        color = ('#4155f4'),
                        width = 1.5))        
        
        layout  = {'title' : f'{i} COTR 1 Year Z-Score - {date_now}',
                   'xaxis' : {'title' : 'Date', 'type': 'date'},
                   'yaxis' : {'title' : 'Z-Score'},
                   'shapes': [{'type': 'rect',
                              'x0': d[i]['scr_1y'].index[0],
                              'y0': -2,
                              'x1': d[i]['scr_1y'].index[-1],
                              'y1': 2,
                              'name': 'Z-range',
                              'line': {
                                      'color': '#f48641',
                                      'width': 2,},
                                      'fillcolor': '#f4ad42',
                                      'opacity': 0.25,
                                      },]
                   }
    
        data = [trace1]
        figure = go.Figure(data=data, layout=layout)
        py.iplot(figure, filename = f'COTR/{date_now}/1 Year Scores/{i}')
        #plot the historical 3 year z-score
        trace2 = go.Scatter(
                x = d[i]['scr_3y'].index,
                y = d[i]['scr_3y'].values,
                name = 'Z-scores',
                line = dict(
                        color = ('#4155f4'),
                        width = 1.5))        
        
        layout  = {'title' : f'{i} COTR 3 Year Z-Score - {date_now}',
                   'xaxis' : {'title' : 'Date', 'type': 'date'},
                   'yaxis' : {'title' : 'Z-Score'},
                   'shapes': [{'type': 'rect',
                              'x0': d[i]['scr_3y'].index[0],
                              'y0': -2,
                              'x1': d[i]['scr_3y'].index[-1],
                              'y1': 2,
                              'name': 'Z-range',
                              'line': {
                                      'color': '#f48641',
                                      'width': 2,},
                                      'fillcolor': '#f4ad42',
                                      'opacity': 0.25,
                                      },]
                   }
    
        data = [trace2]
        figure = go.Figure(data=data, layout=layout)       
        py.iplot(figure, filename = f'COTR/{date_now}/3 Year Scores/{i}')
        

        print(i, 'scr_1y:', np.round(d[i]['scr_1y'].tail(1).item(), 4),
              'scr_3y:', np.round(d[i]['scr_3y'].tail(1).item(),4))
            
print ("Time to complete:", datetime.now() - start_time)


