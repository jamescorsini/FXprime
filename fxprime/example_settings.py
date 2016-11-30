# -*- coding: utf-8 -*-
"""
Created on Sat Jun 04 23:14:00 2016


@author: james
"""

#import os
import plotly.tools as tls

# Directory locations
#CSV_DATA_DIR = os.environ.get('QSFOREX_CSV_DATA_DIR', None)
OUTPUT_RESULTS_DIR = 'results_images'

# Plotly Settings 
tls.set_credentials_file(username='',
                         api_key='',
                         stream_ids=['', ''])

# OANDA Settings
ENVIRONMENT = "practice"

#==============================================================================
# # TODO: Make environment variable?
# ACCESS_TOKEN = os.environ.get('OANDA_API_ACCESS_TOKEN', None)
# ACCOUNT_ID = os.environ.get('OANDA_API_ACCOUNT_ID', None)
#==============================================================================

ACCESS_TOKEN = ''
ACCOUNT_ID = ''

# Personal Settings
BASE_CURRENCY = "USD"
