# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 12:06:04 2016

@author: james
"""

import oandapy
import logging
from fxprime import scripts
from fxprime import executor

class MyStreamer(oandapy.Streamer):
    '''Takes the oandapy streamer and wraps MyStreamer class around it
    '''
    
    def __init__(self, oanda, account_id, pair, strategy, params, verbose=False, *args, **kwargs):
        oandapy.Streamer.__init__(self, *args, **kwargs)
        self.ticks = 0
        self.oanda = oanda
        self.args = params
        self.account_id = account_id
        # Initialize trading algo
        self.strategy = strategy
        self.verbose = verbose
        self.executor = executor.executor(oanda)

    def on_success(self, data):
        self.ticks += 1
        
        if self.verbose:
            logging.info(data['tick'])
        
        # Calls algo tick function and returns event
        event = self.strategy.tick(data['tick'], args=self.args, plot=False)
        # executes event
        self.executor.execute(event);
        
        # uncomment to test and limit number of ticks
        #if self.ticks == 50:
        #    self.disconnect()

    def on_error(self, data):
        # Close out all open trades
        # TODO: Email?
        scripts.close_all_open(self.oanda, self.account_id)
        
        # Disconnect
        self.disconnect()