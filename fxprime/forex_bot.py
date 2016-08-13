# -*- coding: utf-8 -*-
"""
Created on Mon May 30 13:54:58 2016

@author: james
"""

import logging
logging.basicConfig(filename='log.log',level=logging.DEBUG)
logger = logging.getLogger('SMA_Log')

import dateutil.parser

import plotly.plotly as py  
import plotly.tools as tls   
import plotly.graph_objs as go

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

import talib
import pytz


##############    Streaming plot functions   ###############

def init_stream_plot():

    stream_ids = tls.get_credentials_file()['stream_ids']
    # Get stream id from stream id list 
    stream_id = stream_ids[0]

    # Make instance of stream id object 
    stream_1 = go.Stream(
        token=stream_id,  # link stream id to 'token' key
        maxpoints=80      # keep a max of 80 pts on screen
    )

    # Initialize trace of streaming plot by embedding the unique stream_id
    trace1 = go.Scatter(
        x=[],
        y=[],
        mode='lines+markers',
        stream=stream_1         # (!) embed stream id, 1 per trace
    )

    data = go.Data([trace1])

    # Add title to layout object
    layout = go.Layout(title='Time Series')

    # Make a figure object
    fig = go.Figure(data=data, layout=layout)

    # Send fig to Plotly, initialize streaming plot, open new tab
    return py.iplot(fig, filename='python-streaming')
    
def stream_plot(y, x):

    stream_ids = tls.get_credentials_file()['stream_ids']
    # We will provide the stream link object the same token that's associated with the trace we wish to stream to
    s = py.Stream(stream_ids[0])

    # We then open a connection
    s.open()

    # Send data to your plot
    s.write(dict(x=x, y=y))  
 
    # Close the stream when done plotting
    s.close() 
    
    
######################     Candlestick plot function    ###################
    
    
def candle_chart(hist_df, hist_pair, hist_grain):
    
    fig = FF.create_candlestick(hist_df.openBid, hist_df.highAsk, hist_df.lowBid, hist_df.closeBid, dates= hist_df.index)
    # Update the fig - all options here: https://plot.ly/python/reference/#Layout
    fig['layout'].update({
        'title': '',
        'yaxis': {'title': hist_pair}
        #'shapes': [{
        #    'x0': '2007-12-01', 'x1': '2007-12-01',
        #    'y0': 0, 'y1': 1, 'xref': 'x', 'yref': 'paper',
        #    'line': {'color': 'rgb(30,30,30)', 'width': 1}
        #}],
        #'annotations': [{
        #    'x': '2007-12-01', 'y': 0.05, 'xref': 'x', 'yref': 'paper',
        #    'showarrow': False, 'xanchor': 'left',
        #    'text': 'Official start of the recession'
        #}]
    })
    return py.iplot(fig, filename='finance/aapl-candlestick', validate=False)
    
    
    
######################### OANDA Helper functions     ########################
    
def convert_hist_to_df(hist):
    ''' this converts json history data from Oanda's API into a useable df
        # this will be for backtesting strategies
        hist = oanda.get_history(
            instrument='EUR_USD',
            granularity='M1',
            count=500,
            end = (datetime.utcnow()).isoformat("T") + "Z" #(datetime.utcnow() - timedelta(days=7)).isoformat("T") + "Z",
            #includeFirst='true'
        )    
    '''
    df = pd.DataFrame()
    for key in hist['candles'][0].keys():
        df[key] = pd.Series(
            [hist['candles'][i][key] for i in range(len(hist['candles']))], 
            index=[dateutil.parser.parse(hist['candles'][i]['time']) for i in range(len(hist['candles']))]
        )
    del df['time']
    return df, hist['instrument'], hist['granularity']


# convert values to pips (brings it out to the 4th decimal digit)
def pips(val):
    return float(float(val)/10000);
    
    
# Function to call to setup the trade parameters
def setup_trade(oanda, pair, direction, stoploss=400, takeprofit=400):
    
    # set the trade to expire after one day
    trade_expire = datetime.utcnow() + timedelta(days=1)
    trade_expire = trade_expire.isoformat("T") + "Z"
    
    response = oanda.get_prices(instruments=pair)
    price = response.get("prices")[0]

    if direction == 'sell':
        # auto stop loss and take profit marks
        stop_loss = price['ask'] + pips(stoploss)
        take_profit = price['bid'] - pips(takeprofit)
    
        # determining limit order price
        limit_price = price['bid'] - pips(5)
    else:
        # auto stop loss and take profit marks
        stop_loss = price['ask'] - pips(stoploss)
        take_profit = price['bid'] + pips(takeprofit)
    
        # determining limit order price
        limit_price = price['bid'] + pips(5)        
    
    return [stop_loss, take_profit, limit_price, trade_expire]
    
    
#####################   ALGO Helper functions   #####################
def simpleMA_instant(oanda, pair, time_period):
    # input: oanda is api 
    
    hist = oanda.get_history(
        instrument=pair,
        granularity='M1',
        count=time_period,
        end = (datetime.utcnow()).isoformat("T") + "Z" #(datetime.utcnow() - timedelta(days=7)).isoformat("T") + "Z",
        #includeFirst='true'
    )
    
    #val_time = [hist['candles'][i]['time'] for i in range(len(hist['candles']))]
    values = [hist['candles'][i]['closeBid'] for i in range(len(hist['candles']))]
    
    output = talib.SMA(np.array(values), timeperiod=time_period)
    return output
    
def find_index(oanda, account_id, trade_id):
    # Finds index of trade
    trades = oanda.get_trades(account_id)['trades']
    for i in range(len(trades)):
        if trades[i]['id'] == trade_id:
            return i
    return None


def check_FIFO(oanda, account_id, instrument, side):
    # looping through all open trades to find the one executed earliest
    # returns trade id for one that needs to close first
    # instrument is the targeted currecy pair
    # side is buy or sell
    trades = oanda.get_trades(account_id)['trades'];
    time_now = datetime.utcnow()
    check_time = time_now.replace(tzinfo=pytz.UTC)
    trade_id = None;
    for i in range(len(trades)):
        # first confirm instrument is the correct one (don't want to close good trades)
        if trades[i]['instrument'] != instrument:
            continue
        elif trades[i]['side'] != side:
            continue
        elif dateutil.parser.parse(trades[i]['time']) < check_time:
            trade_id = trades[i]['id']
    return trade_id

    
def check_open_trades(oanda, account_id, instrument, side):
    # Loops through all open trades to see if there is already a 'buy' or 'sell' open on that trade pair
    # Returns number of open trades
    # gets current active trades          
    trades = oanda.get_trades(account_id)['trades'];
    num_trades = 0;
    for i in range(len(trades)):
        if (trades[i]['side'] == side and trades[i]['instrument'] == instrument):
            num_trades = num_trades+1;
    return num_trades   
    
    
def close_all_open(oanda, account_id):
    # This closes all open trades
    # For convenience and emergencies
    
    trades = oanda.get_trades(account_id)['trades'];
    
    # Find the instruments used in the open trades
    inst_used = list(set([oanda.get_trades(account_id)['trades'][i]['instrument'] 
                          for i in range(len(oanda.get_trades(account_id)['trades']))]))

    direction_list = ['buy','sell']
    
    for direction in direction_list:
        for inst in inst_used:
            for k in range(len(trades)):

                # Gets trade id of trade to close first
                trade_id = check_FIFO(oanda, account_id, inst, direction)
                try:
                    # have this cycle through to find which trades to close out
                    # Finds index value for trade
                    ind = find_index(oanda, account_id, trade_id)
                    if ind != None:
                        response = oanda.close_trade(account_id, trades[ind]['id'])
                        # redo this line to get the new list of trades
                        trades = oanda.get_trades(account_id)['trades'];
                        print response

                except Exception as e:
                    logging.exception('Cannot close trade')
                    logging.exception(e)
                    print 'Cannot close trade'
                    print e

                    # For error code 28 'FIFO Error'
                    try:
                        if e.error_response['code'] == 28:
                            logging.error('FIFO Error')
                            print 'FIFO Error'
                    except:
                        # Other error codes can go here
                        pass
    
    
####################   Backup    #######################
class oanda_stream():
    # This class was made as an alternate to MyStreamer, not really needed
    def __init__(self, oanda):
        self.oanda = oanda;
        self.myalgo = trading_algo('EUR_USD')
        
    def stream_me(self):
        old_ask = 0;
        
        for i in range(1000):
            response = self.oanda.get_prices(instruments="EUR_USD")
            prices = response.get("prices")
            asking_price = prices[0].get("ask")
            if asking_price != old_ask:
                self.myalgo.tick(prices[0])
                time.sleep(1)
            old_ask = asking_price;
            