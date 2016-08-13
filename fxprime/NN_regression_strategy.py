# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 12:05:28 2016

@author: james
"""

import logging
#from fxprime import scripts

import matplotlib
matplotlib.use('agg')

from fxprime import output

from settings import *
import os

import dateutil.parser
from sklearn import svm

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#from sklearn import neighbors

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
        self.candle_df = pd.DataFrame(columns=['Open','High','Low','Close','Date'])
        self.buy_me = 3  
        self.sell_me = 2
        
        
    def start_date(self):
        return self.candles[0]['time']
        
    def end_date(self):
        return self.candles[-1]['time']

        
    def create_plot(self):
        # Create whatever plot is wanted in conjuction with the 
        # event taking place
    
        try:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.scatter(self.X,self.y)
            ax.autoscale(enable=True, axis='both', tight=True)
            ax.plot(self.T, self.fitted, 'r')
            #ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.6e'))
            
            ymin = min(np.append(self.y,self.fitted))
            ymax = max(np.append(self.y,self.fitted))
            ax.set_ylim([ymin,ymax]);
            
            ax.set_ylabel('Price EUR/USD')
            ax.set_xlabel('Candlestick increment')
            
            ax.grid(True)
            
            ax.text(0.01, 0.01, 'SCORE: '+str(self.score),
            verticalalignment='bottom', horizontalalignment='left',
            transform=ax.transAxes,
            color='green', fontsize=15)
            
            fig.set_size_inches(18,12)
            
            out_dir = OUTPUT_RESULTS_DIR+'\\pics\\'
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)       
            
            date_name = dateutil.parser.parse(self.candles[-1]['time'])
            date_save = str(date_name.date())+'T'+str(date_name.hour)+str(date_name.minute)+str(date_name.second)
            plt.savefig(out_dir+date_save+'.png')         
            
            #logging.info('Strategy image saved')
    
            return True
        
        except:
            logging.error('Strategy image NOT saved')

            return False
        
    
    def tick(self, tick_data, new_candles, params, plot=True):
        
        event = {'pair': self.pair, 'type': None};
        # For every successful datapoint grab this tick function is executed
        
        if params['C'] == None:
            params['C'] = 1e1;
        if params['n_train'] == None:
            params['n_train'] = 10;
        if params['score'] == None:
            params['score'] = 0.9;
        if params['wait'] == None:
            params['wait'] = 5;
        if params['kernel'] == None:
            params['kernel'] = 'rbf'
        if params['degree'] == None:
            params['degree'] = 1
        
        # Add new candle to history
        #print self.candles
        
        # Parses the new candles and adds any that were not already accounted for
        for q in range(len(new_candles)):
            
            if new_candles[q] not in self.candles:
            
                self.candle_df.loc[len(self.candles)] = [new_candles[q]['openBid'],
                                   new_candles[q]['highBid'], new_candles[q]['lowBid'],
                                   new_candles[q]['closeBid'], 
                                   dateutil.parser.parse(new_candles[q]['time'])]        
                
                
                # TODO Check to see if tick_data is already in candles
                self.candles.append(new_candles[q])

        
        end_time = tick_data['time']
        
        ''' -------------- Change strategy below this line ---------------- '''
        # Calculate strategy using stored candles when you can (optimizes 
        # the backtesting).  Change event type to 'buy' or 'sell'
        
        # -- Tuning variables --
        n_train = params['n_train'][0]

        if plot:
            # Create df of candles to pass to plots
            # df plots include open, high, low, close, date as index
            if len(self.candle_df) > 60:
                output.pyplot_candles(self.candle_df[-60:])
            else:
                output.pyplot_candles(self.candle_df)
        
        if self.verbose:
            print tick_data
        

        # Set up X and y for regression
        if len(self.candles) >= n_train:
            candles_hist = self.candles[-n_train:]  
            X = range(len(candles_hist))
            X = [[i] for i in X]
            X = np.array(X)
            y = [candles_hist[i]['closeAsk'] for i in range(len(candles_hist))]
            y = np.array(y)*10000
        else:
            # use API call or init at 0
            #X = np.zeros(n_train)
            #X = [[i] for i in X]
            #y = np.zeros(n_train)
            return event
            
        # X with one point more to predict the future
        T = np.append(X[:],[[X[-1][0]+1]])
        T = [[i] for i in T]
        T = np.array(T)
        
        # Regression
        # TOdO: Can use .score to detmine confidence level
        # TODO: Can average all of the fitted together to get a bettern 
        # general estimate like tree boosting
        clf = svm.SVR(kernel=params['kernel'][0], gamma=0.1, degree=params['degree'][0], C=params['C'][0])
        #clf = svm.SVR(kernel='poly', degree=3)
        clf.fit(X, y) 
        
        self.score = clf.score(X, y)
        
        self.X = X
        self.y = y/10000
        self.T = T

        self.fitted = clf.predict(T)/10000
        
        print "close: "+str(self.candles[-1]['closeAsk'])+" fit: "+str(self.fitted[-1])+" buy: "+str(self.buy_me)+" sell: "+str(self.sell_me)+" score: "+str(self.score)
        
        # filter the buy/sell event
        if self.score > params['score'][0]:
        
            if (self.fitted[-1] > self.candles[-1]['closeAsk']):# and self.high_bit == 0):
                
                self.buy_me += 1
                self.sell_me -= 1
                if (self.buy_me > 3):# and self.high_bit == 0):  
                    print 'Crossover Point: Long'
                    print tick_data
                    logging.info('Crossover Point: Long')
                    logging.info(tick_data)
                    self.high_bit = 1;
                    event['type'] = 'buy'
                    
            elif (self.fitted[-1] < self.candles[-1]['closeAsk']):# and self.high_bit == 1):
    
                self.buy_me -= 1
                self.sell_me += 1
                if (self.sell_me > 3):# and self.high_bit == 1):       
                    print 'Crossover Point: Short'
                    print tick_data
                    logging.info('Crossover Point: Short')
                    logging.info(tick_data)
                    self.high_bit = 0;
                    event['type'] = 'sell'
            
            if self.buy_me > params['wait'][0]:
                self.buy_me = params['wait'][0]
                self.sell_me = 0
            elif self.sell_me > params['wait'][0]:
                self.buy_me = 0
                self.sell_me = params['wait'][0]
                
            
        # Always end with returning event or code will break
        return event        
        
