# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 19:50:22 2016

@author: james
"""

import logging
import dateutil.parser
from datetime import datetime, timedelta
import pytz
import talib
import numpy as np
import pandas as pd


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
                    ind = _find_index(oanda, account_id, trade_id)
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
                    
                    
def _find_index(oanda, account_id, trade_id):
    # Finds index of trade
    trades = oanda.get_trades(account_id)['trades']
    for i in range(len(trades)):
        if trades[i]['id'] == trade_id:
            return i
    return None


def check_FIFO(oanda, account_id, instrument, side, backtest=False, positions={}):
    # looping through all open trades to find the one executed earliest
    # returns trade id for one that needs to close first
    # instrument is the targeted currecy pair
    # side is buy or sell
    if not backtest:
        trades = oanda.get_trades(account_id)['trades'];
    else:
        trades = positions
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
    

def simpleMA_backtest(oanda, pair, end_time, time_period, candles=[]):
    ''' This takes the simple average for a certian time period, ending with
        end_time
    '''
    if len(candles)==time_period:
        # There are enough candles passed to function
        hist = candles
    else:
        # Not enough candles were passed, making API call
        logging.debug('Making API call: Grabing history data for MA')
        hist_vals = oanda.get_history(
            instrument=pair,
            granularity='M1',
            count=time_period,
            end = end_time #(datetime.utcnow() - timedelta(days=7)).isoformat("T") + "Z",
            #includeFirst='true'
        )
        hist = hist_vals['candles']

    #val_time = [hist['candles'][i]['time'] for i in range(len(hist['candles']))]
    values = [hist[i]['closeBid'] for i in range(len(hist))]
        
    output = talib.SMA(np.array(values), timeperiod=time_period)
    return output
    
    

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
    