# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 12:05:28 2016

@author: james
"""

import logging
from fxprime import scripts
from fxprime import output
import dateutil.parser

#############    Trading Algo   ################

class trading_algo():
    ''' Trading algorithm, this will be the only thing changing with 
        differnt strategies
        It outputs and event, such as buy, sell, close, or None 
        candle = {u'highAsk': 1.13446, u'lowAsk': 1.13444, u'complete': True, 
        u'openBid': 1.13432, u'closeAsk': 1.13444, u'closeBid': 1.13429, 
        u'volume': 2, u'openAsk': 1.13446, u'time': u'2016-06-03T19:16:00.000000Z', 
        u'lowBid': 1.13429, u'highBid': 1.13432}
    '''    
    def __init__(self, oanda, account_id, pair, verbose=False):
        # this is going to be one algorithm per currancy pair
        print '----------- ADRIAN FX Trading Algo has started ------------'
        logging.info('----------- ADRIAN FX Trading Algo has started ------------')
        self.pair = pair;
        self.oanda = oanda;
        self.account_id = account_id;
        self.verbose = verbose;
        self.high_bit = 0;
        self.candles = [];
    
    def tick(self, tick_data, plot=True):
        
        event = {'pair': self.pair, 'type': None};
        # For every successful datapoint grab this tick function is executed
        
        # Add new candle to history
        #print self.candles
        self.candles.append(tick_data)
        end_time = tick_data['time']

        if plot:
            output.stream_plot(tick_data['closeAsk'], dateutil.parser.parse(tick_data['time']))
        
        if self.verbose:
            print tick_data
              
        # Main part of the algorithm
        # This is a common SMA crossover trader
        if len(self.candles) >= 50:
            # Grab SMA from existing history
            candles_hist = self.candles[-50:]    
            sma50 = scripts.simpleMA_backtest(self.oanda, self.pair, end_time, time_period=50, candles=candles_hist) 
        else:
            # Grab SMA from API call   
            sma50 = scripts.simpleMA_backtest(self.oanda, self.pair, end_time, time_period=50)             
                
        if len(self.candles) >= 200:
            # Grab SMA from existing history
            candles_hist = self.candles[-200:]            
            sma200 = scripts.simpleMA_backtest(self.oanda, self.pair, end_time, time_period=200, candles=candles_hist) 
        else:
            # Grab SMA from API call
            sma200 = scripts.simpleMA_backtest(self.oanda, self.pair, end_time, time_period=200)
                

        
        if (sma200[-1] < sma50[-1] and self.high_bit == 0):
            
            print 'Crossover Point: Long'
            print tick_data
            logging.info('Crossover Point: Long')
            logging.info(tick_data)
            
            self.high_bit = 1;
            event['type'] = 'buy'
            
            '''if scripts.check_open_trades(self.oanda, self.account_id, self.pair, 'buy') == 0:                 
                event['type'] = 'buy'
            else:
                logging.warning("Trade not executed, existing buy already open")
                print "Trade not executed, existing buy already open"'''
                
        elif (sma200[-1] > sma50[-1] and self.high_bit == 1):

            print 'Crossover Point: Short'
            print tick_data
            logging.info('Crossover Point: Short')
            logging.info(tick_data)
            
            self.high_bit = 0;
            event['type'] = 'sell'
            
            '''# if active long trade is open then close it out
            trades = self.oanda.get_trades(self.account_id)['trades'];
            if scripts.check_open_trades(self.oanda, self.account_id, self.pair, 'sell') == 0:
                event['type'] = 'sell'
            else:
                logging.warning("Trade not executed, existing buy already open")
                print "Trade not executed, existing sell already open"'''
        
        return event
        
        
'''
import numpy as np
import matplotlib.pyplot as plt
from sklearn import neighbors

np.random.seed(0)
X = np.sort(5 * np.random.rand(40, 1), axis=0)
T = np.linspace(0, 5, 500)[:, np.newaxis]
y = np.sin(X).ravel()

# Add noise to targets
y[::5] += 1 * (0.5 - np.random.rand(8))

###############################################################################
# Fit regression model
n_neighbors = 5

for i, weights in enumerate(['uniform', 'distance']):
    knn = neighbors.KNeighborsRegressor(n_neighbors, weights=weights)
    y_ = knn.fit(X, y).predict(T)

    plt.subplot(2, 1, i + 1)
    plt.scatter(X, y, c='k', label='data')
    plt.plot(T, y_, c='g', label='prediction')
    plt.axis('tight')
    plt.legend()
    plt.title("KNeighborsRegressor (k = %i, weights = '%s')" % (n_neighbors,
                                                                weights))

plt.show()
'''
        
        
