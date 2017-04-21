# -*- coding: utf-8 -*-
"""
Created on Sat Jun 04 23:22:38 2016

@author: james
"""

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

class Backtester:
    """
    Encapsulates the settings and components for carrying out
    an event-driven backtest on the foreign exchange markets.
    """
    def __init__(
        self, pairs, strategy, oanda, grainularity='M1', duration=50000, 
        equity=100000.0, max_iters=10000000000, plots=False
    ):
        
        """
        Initialises the backtest.
        """
        self.equity = equity
        # TODO: Pass list of pairs
        self.pairs = pairs
        self.strategy = strategy
        self.oanda = oanda
        self.max_iters = max_iters
        self.candles = self._get_hist(duration)

        import csv
        with open('candle_dump.csv', 'w') as csvfile:
            fieldnames = [u'highAsk',
                             u'lowAsk',
                             u'complete',
                             u'openBid',
                             u'closeAsk',
                             u'closeBid',
                             u'volume',
                             u'openAsk',
                             u'time',
                             u'lowBid',
                             u'highBid']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(self.candles)

        self.candle_ind = 0
        self.plots = plots
        
        
    # TODO: Add margin calculations   
        
        
    def _get_hist(self, candles=10000):
        count = 5000; # max count is 5000
        hist_vals = []
        time_now = datetime.utcnow()
        time_temp = (time_now).isoformat("T") + "Z"
        
        for i in range(candles/count):
          
            hist_temp = self.oanda.get_history(
                instrument=self.pairs,
                granularity='M1',
                count=count,
                #start = (time_now - timedelta(minutes=count*(i+1))).isoformat("T") + "Z",
                end = time_temp, #(time_now - timedelta(minutes=count*i)).isoformat("T") + "Z",
                #includeFirst='true'
            )
            
            #print hist_temp['candles'][0]['time']
            #print hist_temp['candles'][-1]['time']
            time_temp = hist_temp['candles'][0]['time']
            hist_vals = hist_temp['candles'] + hist_vals
            
        return hist_vals
        
    def run_backtest(self, portfolio, args):
        """
        Carries out an infinite while loop that loops through the 
        given candles and recalculates the portfolio stats
        """
        print "Running Backtest..."
        iters = 0
        
        while iters < self.max_iters and self.candle_ind != len(self.candles):

            event = self.strategy.tick(self.candles[self.candle_ind], params=args, plot=False)

            # Pulled out of the if statement below to generate CSV that will show every tick
            # This will run a lot slower now!
            self.equity = portfolio.update_portfolio(event, self.candles[self.candle_ind], plots=False)

            if event['type'] is not None:
                # Run command to create plots
                if False: # This will change based off of function input in the future
                    plot_success = self.strategy.create_plot() # Additional plots for strategy analysis
                else:
                    plot_success = False
            
                #self.equity = portfolio.update_portfolio(event, self.candles[self.candle_ind], plots=plot_success)
            
            print 'Candle: ' + str(self.candle_ind) + '/' + str(len(self.candles)) + '   Equity: ' + str(self.equity)
            self.candle_ind += 1
            iters += 1
    
        print 'Equity: ' + str(self.equity)
        print "Backtest complete."
        
