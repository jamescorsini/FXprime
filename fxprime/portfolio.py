# -*- coding: utf-8 -*-
"""
Created on Mon Jun 06 22:25:41 2016

@author: james
"""

'''

TODO: Add pip spread
TODO: add more stats to output, like max drawdrown


'''

import logging
from fxprime import backtester
from settings import *
import os
import pandas as pd

# TODO can make a function in scripts to get rid of this import
import dateutil.parser
import csv
    
class Portfolio:
    def __init__(
        self, pairs, strategy, oanda, leverage=20, backtest_name='backtest.csv',
        stats_name='stats.csv', equity=100000.00, risk_per_trade=0.02
    ):      
        
        self.strategy = strategy
        self.pairs = pairs
        self.leverage = leverage
        self.unrealized = 0
        self.start_equity = equity
        self.max_drawdown = 0
        self.equity = equity
        self.oanda = oanda
        self.backtest_name = backtest_name
        # Ex. {'EUR_USD':{'type':'buy','lot':10000, 'bid':1.3424, 'ask':1.32420}}
        self.positions = {}
        self.prev_equity = self.start_equity
    
    def run_backtest(self, portfolio, args, duration=50000):
        # Create results file
        # self.backtest_file_path
        self._create_equity_file()
        self.args = args
        
        # initialize backtester object
        backtest = backtester.Backtester(
                                         self.pairs[0], self.strategy, self.oanda, 
                                         grainularity='M1', duration=duration, 
                                         equity=100000.0, max_iters=10000000000,
                                         plots=True
                                         )
        # run backtester
        backtest.run_backtest(portfolio, args)
        
    
    def update_portfolio(self, event, candle, plots=False):
        """
        This updates all positions based upon the event that has transpired
        event = {'pair': self.pair, 'type': None};
        candle = {u'highAsk': 1.13446, u'lowAsk': 1.13444, u'complete': True, u'openBid': 1.13432, u'closeAsk': 1.13444, u'closeBid': 1.13429, u'volume': 2, u'openAsk': 1.13446, u'time': u'2016-06-03T19:16:00.000000Z', u'lowBid': 1.13429, u'highBid': 1.13432}
        """
        
        if event['type'] != None:

            if event['pair'] in self.positions:
                # Update position
                # Closes a FIFO violation
                closed = self._backtest_close(event, candle)
                if not closed:
                    logging.error('Failed to close simulated trade')
                else:
                    logging.info('FIFO closed')

            if event['type'] == 'buy':
                # Check for FIFO error
                # Updated unrealized PnL
                bought = self._backtest_buy(event, candle)
                if not bought:
                    logging.error('Failed to buy simulated trade')
                else:
                    logging.info('Bought')

            elif event['type'] == 'sell':
                # Check for FIFO error
                sold = self._backtest_sell(event, candle)
                if not sold:
                    logging.error('Failed to sell simulated trade')
                else:
                    logging.info('Sold')

            elif event['type'] == 'close':
                # Closing order
                closed = self._backtest_close(event, candle)
                if not closed:
                    logging.error('Failed to close simulated trade')
                else:
                    logging.info('Closed')
                        
        self._update_equity_file(event, candle, plots=False)#plots)

        # Recalculates max drawdown
        if self.start_equity-self.equity > self.max_drawdown:
            self.max_drawdown = self.start_equity-self.equity
                        
        return self.equity
        
        
    def _backtest_close(self, event, candle):
        # Closes order  
        realized = 0
        
        # Looks for pair in positions
        if event['pair'] in self.positions:
            # looks to see which direction it's going
            # closes order according to given candle      
            # http://www.forex.com/calculating-forex-profit-loss.html
            if self.positions[event['pair']]['type'] == 'buy' and event['type'] != 'buy':
                # Calculate realized PnL
                realized = candle['closeBid'] - self.positions[event['pair']]['ask']
                # Updates positions and equity
                self.equity = self.equity + self.positions[event['pair']]['lot']*realized
                
                try:
                    del self.positions[event['pair']]
                except:
                    logging.ERROR('Trying to remove position that does not exist')
                
            elif self.positions[event['pair']]['type'] == 'sell' and event['type'] != 'sell':
                realized = self.positions[event['pair']]['bid'] - candle['closeAsk']
                # Updates positions and equity
                self.equity = self.equity + self.positions[event['pair']]['lot']*realized

                try:
                    del self.positions[event['pair']]
                except:
                    logging.ERROR('Trying to remove position that does not exist')
                    
            # Returns true for close success
            return 1
        
        else:
            # Failed to close trade
            return 0
        
    def _backtest_buy(self, event, candle):
        # Opens buy order  
        # Looks for pair in positions
        if event['pair'] not in self.positions:
            self.positions[event['pair']] = {'type':'buy','lot':10000, 'bid':candle['closeBid'], 'ask':candle['closeAsk']}

            return 1
        
        else:
            # Failed to close trade
            return 0        
        
    def _backtest_sell(self, event, candle):
        # Opens buy order  
        # Looks for pair in positions
        if event['pair'] not in self.positions:
            self.positions[event['pair']] = {'type':'sell','lot':10000, 'bid':candle['closeBid'], 'ask':candle['closeAsk']}

            return 1
        
        else:
            # Failed to close trade
            return 0        
   

    def create_stats_file(self, stats_name='stats.csv',):
        filename = stats_name
        
        if not os.path.exists(OUTPUT_RESULTS_DIR):
            os.makedirs(OUTPUT_RESULTS_DIR)        
        
        self.stats_file_path = os.path.join(OUTPUT_RESULTS_DIR, filename)
        
        stat_parameters = ['Total Equity', 'Percent change', 'Start Date', 'End Date','Max drawdown', 'Max drawdown %', 'Parameters']   
        stat_values = [self.equity, 
                       (self.equity-self.start_equity)/self.start_equity,
                        self.strategy.start_date(),
                        self.strategy.end_date(),
                        self.max_drawdown,
                        self.max_drawdown/self.start_equity,
                        self.args]      
        
        stats_pd = pd.DataFrame([stat_parameters, stat_values]).T

        print stats_pd        
        
        stats_pd.to_csv(self.stats_file_path,header=False,index=False)
            

    def _create_equity_file(self):
        filename = self.backtest_name
        
        if not os.path.exists(OUTPUT_RESULTS_DIR):
            os.makedirs(OUTPUT_RESULTS_DIR)        
        
        self.backtest_file_path = os.path.join(OUTPUT_RESULTS_DIR, filename)

        #with open(self.backtest_file_path, "w") as f:
        f = open(self.backtest_file_path, "w")
        header = ["Timestamp", "Balance", "Event Type"]
        for pair in self.pairs:
            header.append(pair)
            header.append("Percent Change")
        #header += "\n"
        header.append("Strategy Info")
        self.writer = csv.DictWriter(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, fieldnames=header)

            
            
    def _update_equity_file(self, event, candle, plots=False):
        # This appends info to the equity file
        row = {}
        row['Timestamp'] = str(candle['time'])
        row['Balance'] = str(self.equity)

        # TODO move strategy_info into event dict so just one var is passed

        if event['type'] != None:
            if plots:
                # Broken because writing to CSV and it will not execute equations
                # also because ther is a comma in the hyperlinkn command                
                pass                
                # Then plot was created, insert hyperlink here
                #date_name = dateutil.parser.parse(candle['time'])
                #date_save = str(date_name.date())+'T'+str(date_name.hour)+str(date_name.minute)+str(date_name.second)
                #print "=HYPERLINK(\"pics\\"+str(date_save)+".png\",\""+str(event['type'])+"\")"
                #row += ",%s" % ("=HYPERLINK('\\pics\\"+date_save+".png','"+str(event['type'])+"')")
            else:
                row['Event Type'] = str(event['type'])
        
        for pair in self.pairs:
            if pair == event['pair']:
                row[pair] = candle['closeAsk']
                row['Percent Change'] = str((self.equity-self.prev_equity)/self.prev_equity)

        row['Strategy Info'] = event['strategy_info']

        #with open(self.backtest_file_path, "a") as f:
        self.writer.writerow(row)

        self.prev_equity = self.equity
            
        