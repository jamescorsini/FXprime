# FXprime
FOREX backtester and live trader using Oanda

## How to Run
1. Download and install fxprime
2. Run main.py

Note: For more/ different functionality edit variables in main.py
pairs, backtest, plot, and verbose

pairs = currency pair (ex. 'EUR_USD')
backtest = boolean, if true runs backtest else runs live trader
plot = boolean, plots output
verbose = boolean, more detailed trade execution reporting

## Output Example
#### Backtest 


#### Live Trading
'----------- ADRIAN FX Trading Algo has started ------------
       Open     High      Low    Close                Date
0   1.05944  1.05952  1.05937  1.05952 2016-12-01 01:46:00
1   1.05949  1.05949  1.05929  1.05929 2016-12-01 01:47:00
2   1.05925  1.05925  1.05917  1.05919 2016-12-01 01:48:00
3   1.05923  1.05926  1.05923  1.05923 2016-12-01 01:49:00
4   1.05921  1.05921  1.05906  1.05916 2016-12-01 01:50:00'

... ticks for every second

'58  1.05964  1.05968  1.05961  1.05963 2016-12-01 02:46:00
59  1.05966  1.05970  1.05966  1.05970 2016-12-01 02:47:00
close: 1.05985 fit: 1.05989181988 buy: 3 sell: 2 score: 0.431592395751'

Executes trades and lists algorithm parameters


Sources:
Oandapy (https://github.com/oanda/oandapy)

