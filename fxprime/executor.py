# -*- coding: utf-8 -*-
"""
Created on Wed Jun 08 20:32:43 2016

@author: james
"""

import logging
import os.path
from fxprime import scripts
from fxprime import settings

class executor:
    ''' Takes events (ex. buy, sell, close) and executes them on Oanda
    '''
    def __init__(self, oanda):
        self.oanda = oanda
        self.output_enable = True
        self.stream_out = 'Stream_Out.csv'
        # Check if it exists and then write header if not
        if not os.path.isfile(self.stream_out):
            header = 'Description'
            with open(self.stream_out,'wb') as file:
                file.write(header)
                file.write('\n')
    
    def execute(self, event):
        if event['type'] == 'buy':
            # Open long             
            self.buy(event)
        elif event['type'] == 'sell':
            # Open short 
            self.sell(event)
        elif event['type'] == 'close':
            # Close specific trade
            pass
        else:
            # Do nothing
            pass
    
    def buy(self, event):
        # Executes buy order
        # Note: Should always execute a limit order (preferably with a band of +-5 pips)

        # Closes all open sell orders to avoid FIFO
        self._conflict_close(event)
        
        [stop_loss, take_profit, limit_price, trade_expire] = scripts.setup_trade(self.oanda, event['pair'], event['type'])

        try:
            response = self.oanda.create_order(settings.ACCOUNT_ID,
                instrument=event['pair'],
                units=1000,
                side='buy',
                type='limit',
                price=limit_price,
                expiry=trade_expire,
                stopLoss = stop_loss,
                takeProfit = take_profit
            );
            print response
            logging.info(response)
            
            if self.output_enable:
                with open(self.stream_out,'wb') as file:
                    file.write(response)
                    file.write('\n')
                    
        except Exception as e:
            logging.exception('Buy trade order not executed')
            logging.exception(e)
            print 'Buy trade order not executed'
            print e
    
    
    def sell(self, event):
        # Executes sell order
        # Note: Should always execute a limit order (preferably with a band of +-5 pips)

        # Closes all open buy orders to avoid FIFO
        self._conflict_close(event)
        
        [stop_loss, take_profit, limit_price, trade_expire] = scripts.setup_trade(self.oanda, event['pair'], event['type'])

        try:
            response = self.oanda.create_order(settings.ACCOUNT_ID,
                instrument=event['pair'],
                units=1000,
                side='sell',
                type='limit',
                price=limit_price,
                expiry=trade_expire,
                stopLoss = stop_loss,
                takeProfit = take_profit
            );
            print response
            logging.info(response)
            
            if self.output_enable:
                with open(self.stream_out,'wb') as file:
                    file.write(response)
                    file.write('\n')
                    
        except Exception as e:
            logging.exception('Sell trade order not executed')
            logging.exception(e)
            print 'Sell trade order not executed'
            print e
            
    def close(self, event):
        # Executes close order
        # Note: Should always execute a limit order (preferably with a band of +-5 pips)
        
        try:
            response = self.oanda.create_order(settings.ACCOUNT_ID,
                instrument=event['pair'],
                units=1000,
                side='sell',
                type='limit',
                price=limit_price,
                expiry=trade_expire,
                stopLoss = stop_loss,
                takeProfit = take_profit
            );
            print response
            logging.info(response)
            
            if self.output_enable:
                with open(self.stream_out,'wb') as file:
                    file.write(response)
                    file.write('\n')
                    
        except Exception as e:
            logging.exception('Sell trade order not executed')
            logging.exception(e)
            print 'Sell trade order not executed'
            print e

    
    def _conflict_close(self, event):
        # this function closes open trades based on the algorithm
        # gets current active trades          
        trades = self.oanda.get_trades(settings.ACCOUNT_ID)['trades']
        
        for k in range(len(trades)):
            
            trade_id = scripts.check_FIFO(self.oanda, settings.ACCOUNT_ID, event['pair'], event['type'])
            try:
                # have this cycle through to find which trades to close out
                ind = scripts.find_index(self.oanda, self.account_id, trade_id)
                if ind != None:
                    response = self.oanda.close_trade(settings.ACCOUNT_ID, trades[ind]['id'])
                    logging.info(response)
                    print response
                    
                    if self.output_enable:
                        with open(self.stream_out,'wb') as file:
                            file.write(response)
                            file.write('\n')
                    
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
                            
                            if self.output_enable:
                                with open(self.stream_out,'wb') as file:
                                    file.write(response)
                                    file.write('\n')
    
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