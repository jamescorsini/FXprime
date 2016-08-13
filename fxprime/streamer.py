# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 12:06:04 2016

@author: james
"""

import logging
import time
from datetime import datetime, timedelta
from fxprime import scripts
from fxprime import executor
from fxprime import settings
from fxprime import oandapy

class MyStreamer():
    '''Finds the latest candle and executes the program based off of that
    '''   
    def __init__(self, oanda, account_id, pairs, strategy, params, plot=False, verbose=False):
        self.ticks = 0
        self.plot = plot
        self.oanda = oanda
        self.pairs = pairs
        self.args = params
        self.account_id = account_id
        self.strategy = strategy
        self.verbose = verbose
        self.executor = executor.executor(oanda)


    def on_success(self, prev_candle, new_candles):
        # Count how many times this has ticked
        self.ticks += 1

        # Get list of current trades
        trades = self.oanda.get_trades(settings.ACCOUNT_ID)
        
        if self.verbose:
            #logging.info(prev_candle['closeAsk'])
            pass
        
        # Calls algo tick function and returns event
        event = self.strategy.tick(prev_candle, new_candles, params=self.args, plot=self.plot)
        
        # Check to see what's already open and don't open a new one 
        if len(trades['trades']) == 0:
            self.executor.execute(event)
        else:
            for trade in trades['trades']:
                if trade['instrument'] == event['pair']:
                    if trade['side'] != event['type']:
                        # executes event
                        self.executor.execute(event)
        
        # uncomment to test and limit number of ticks
        #if self.ticks == 50:
        #    self.disconnect()


    def on_error(self, data):
        # Close out all open trades
        # TODO: Email?
        scripts.close_all_open(self.oanda, self.account_id)
        
        # Disconnect
        self.disconnect()
        
        
    def start(self, instruments, grainularity='M1'):
        
        while True:
            # Instruments is list of pairs
            # Grab previous candle of given duration
            time_now = datetime.utcnow()
            one_min = timedelta(minutes=1, seconds=0)
            time_now_mod = time_now-one_min
            time_temp = (time_now_mod).isoformat("T") + "Z"
            
            #for pair in instruments:
            
            # Get last candle 
            hist_temp = self.oanda.get_history(
                instrument=self.pairs,
                granularity=grainularity,
                count=60,
                #start = (time_now - timedelta(minutes=count*(i+1))).isoformat("T") + "Z",
                end = time_temp, #(time_now - timedelta(minutes=count*i)).isoformat("T") + "Z",
                #includeFirst='true'
            )
            
            time_temp = hist_temp['candles'][0]['time']
            
            if hist_temp['candles'][-1]['complete'] == True:
                self.on_success(hist_temp['candles'][-1], hist_temp['candles'])
            
            
            # Heartbeat
            #print '.'            
            
            # Change this sleep time depending upon grainularity
            # TODO this might cause there to be not enough time to calculate...
            # check on this
            time.sleep(1)
    