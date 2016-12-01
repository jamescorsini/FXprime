# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 20:35:20 2016

@author: james
"""

import os
import logging
import time
import matplotlib
matplotlib.use('agg')

from fxprime import settings
from fxprime import streamer
#from fxprime import output
from fxprime import oandapy
from fxprime import scripts
from fxprime import portfolio as fxprime_portfolio
from fxprime import NN_regression_strategy as fxprime_strategy
#from fxprime import SMA_Xover_strategy as strategy

from sklearn.grid_search import ParameterGrid


def main(oanda):
        
    # Set up logging
    logging.basicConfig(filename=os.getcwd()+'\\adrian.log', 
                        level=logging.INFO,  
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    # Declare variables
    pairs = ['EUR_USD']
    backtest = True
    plot = True
    verbose = False


    # Create the strategy object
    strategy = fxprime_strategy.trading_algo(
                        oanda, settings.ACCOUNT_ID, pairs[0], verbose=verbose)
                
    args = {'C': [10], 'n_train': [10], 'score': [0.9], 'wait': [5], 'kernel': ['poly'], 'degree': [2]}

    if not backtest:
        # Run streamer object to run strategy in real time
        # https://plot.ly/8/~Vedrfolnir/
    
        #output.init_stream_plot()
        
        stream = streamer.MyStreamer(oanda, 
                                     settings.ACCOUNT_ID, 
                                     pairs[0], 
                                     strategy,
                                     verbose=verbose,
                                     params=args,
                                     plot=plot,
                                    )
                                    
        stream.start(instruments=pairs[0], grainularity='M1')
        
    else:
        
        #args = {'C': [10,100,1000], 'n_train': [10,15,20], 'score': [0.9,0.5,0.75], 'wait': [5,10,15], 'kernel': ['poly','rbf'], 'degree': [2]}
        args = {'C': [10], 'n_train': [10,15,20], 'score': [0.9], 'wait': [5,10,15], 'kernel': ['poly'], 'degree': [2]}
        
        # list of all possibilities, itterate through    
        param_grid = list(ParameterGrid(args))    
        
        for (i, params) in enumerate(param_grid): 
            
            print 'Parameter Grid: '+str(i)+'/'+str(len(param_grid))            
        
            # Create the portfolio object for strategy documentation and backtesting
            portfolio = fxprime_portfolio.Portfolio(
                                pairs, strategy, oanda, leverage=20, 
                                backtest_name='backtest_'+str(i)+'.csv',
                                equity=10000.00, risk_per_trade=0.02)
            portfolio.run_backtest(portfolio, params, duration=100000)
            portfolio.create_stats_file(stats_name='stats_'+str(i)+'.csv')
    
    print '--------------- FXPRIME Finished ---------------'
    
    
if __name__ == "__main__":
    
    # Log total run time
    start_time = time.time()    
    
    # Initialize the API env
    oanda = oandapy.API(environment=settings.ENVIRONMENT, 
                        access_token=settings.ACCESS_TOKEN)
    
    try:
        main(oanda)
    except KeyboardInterrupt:        
        print "Keyboard Interrupt"
    except:
        print "Unknown Error"
    finally:
        scripts.close_all_open(oanda, settings.ACCOUNT_ID)
        
    print 'Total run time: ' + str((time.time()-start_time)/60) + ' min'


    