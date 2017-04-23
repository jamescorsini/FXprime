# -*- coding: utf-8 -*-
"""
Created on Sun Jun 05 21:04:56 2016

@author: james
"""

from matplotlib.dates import date2num

import plotly.plotly as py  
import plotly.tools as tls   
import plotly.graph_objs as go
from settings import *

import logging

import os

from plotly.tools import FigureFactory as FF
from datetime import datetime

import matplotlib.pyplot as plt
plt.ion()
import matplotlib.dates as mdates
from matplotlib.finance import candlestick_ohlc

pyplot_candle = datetime.now()
def pyplot_candles(candles_df):
    global pyplot_candle
    
    df_copy = candles_df.copy()
    
    if (pyplot_candle != df_copy.iloc[-1]['Date']):
        
        fig, ax = plt.subplots()
        #fig.subplots_adjust(bottom=0.2)
        
        #plot_day_summary(ax, quotes, ticksize=3)
        print df_copy
        #candlestick2_ohlc(ax, candles_df.Open, candles_df.High, candles_df.Low, candles_df.Close, width=0.6)
        
        #ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.title("EUR_USD")
        
        df_copy['Date2'] = df_copy['Date'].apply(lambda d: mdates.date2num(d.to_pydatetime()))
        candlestick_ohlc(ax, df_copy[['Date2','Open','High','Low','Close']].values, width=.0005, colorup='g', colordown='r', alpha=0.95)
        
        ax.xaxis_date()
        ax.autoscale_view()
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        
        fig.set_size_inches(18,12)
        
        #plt.show()
                
        out_dir = OUTPUT_RESULTS_DIR+'\\pics\\'
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)       
        
        plt.savefig(out_dir+'Adrian_candle'+'.png')         
        
        #logging.info('Strategy image saved')
        
        pyplot_candle = df_copy.iloc[-1].Date
        #plt.show()

plotly_count = 0
plotly_candle = datetime.now()
def candlestick_plot(candles_df):

    global plotly_count
    global plotly_candle
    plotly_max_count = 30 #can plot 30 per hour
    print (plotly_candle != candles_df.iloc[-1]['Date'])
    if not (plotly_count > plotly_max_count) and (plotly_candle != candles_df.iloc[-1]['Date']):
        fig = FF.create_candlestick(candles_df.Open, candles_df.High, candles_df.Low, candles_df.Close, dates=candles_df.Date)
        # Update the fig - all options here: https://plot.ly/python/reference/#Layout
        fig['layout'].update({
            'title': 'Adrian Candlestick',
            'yaxis': {'title': 'EUR_USD'},
            #Draws line on plot and annotates plot        
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
        py.iplot(fig, filename='Adrian_Candlestick', validate=False) 
        
        plotly_candle = candles_df.iloc[-1]['Date']
        plotly_count += 1
        

def init_stream_plot():

    stream_ids = tls.get_credentials_file()['stream_ids']
    # Get stream id from stream id list 
    stream_id = stream_ids[0]

    # Make instance of stream id object 
    stream_1 = go.Stream(
        token=stream_id,  # link stream id to 'token' key
        maxpoints=80      # keep a max of 80 pts on screen
    )

    # TODO: change this to candlesticks
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



import warnings
# import matplotlib.finance as fin

# http://stackoverflow.com/questions/10944621/dynamically-updating-plot-in-matplotlib

plt.ion()
class DynamicUpdate:
    def __init__(self):
        pass

    def on_launch(self, min_x, max_x):
        #Set up plot
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot_date([],[], 'o-')
        self.events, = self.ax.plot_date([],[],'r*')
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True)
        # self.ax.set_xlim(date2num(min_x), date2num(max_x))
        #Other stuff
        self.ax.grid()
        self.event_xdata = []
        self.event_ydata = []

    def on_running(self, xdata, ydata, event_trig=False):
        # try:
        xdata_strp = [date2num(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.000000Z")
                                       ) for date in xdata]
        #Update data (with the new _and_ the old points)
        # self.lines.set_xdata(xdata_strp)
        # self.lines.set_ydata(ydata)
        self.lines.set_data(xdata_strp, ydata)
        #Update events
        if event_trig:
            self.event_xdata.append(xdata_strp[-1])
            self.event_ydata.append(ydata[-1])
            self.events.set_xdata(self.event_xdata)
            self.events.set_ydata(self.event_ydata)
        #Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        #We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()


        # except:
        #     warnings.warn("TKinter Error: Plot closed before finished")

    def save_plot(self, save_dir):

        plt.savefig(save_dir)

