"""
Leverages BACKTRADER FRAMEWORK, MYSQL DATABASE, and INTERACTIVE BROKERS - Backtester and Live trading framework
Can use multiple symbols, multiple timeframes, multiple indicators, and different start/end dates and analytics.
1 primary data feed (5 min timeframe) is sourced from mysql (but can be sourced elsewhere), and then 2 additional data feeds(resampled datafeeds for higher timeframes)
can optionally be available.  Data feeds are as follows:  data0 = 5min, data1= 15min, data2 = 60min, data3 = 1day.
Each symbol can be accessed in each timeframe.  For example, MSFT and XOM would be appear as:
data0 MSFT (base timeframe), data0 XOM(base timeframe), data1 MSFT(next higher timeframe), data1 XOM, data2 MSFT, data2 XOM, data3 MSFT(highest timeframe), data3 XOM - a total of 8 'datas'.
Each data produces a "line" of data that includes everything from the data feed, i.e. Open, high, low, close etc.  System iterates over each line via next() function to produce its results.
For live trading, can leverage IB market scanners to come up with tickers to trade every day - Toggle live trading true or false
"""

#IMPORT MODULES
#python -m cProfile "C:\Program Files\Python38\Lib\site-packages\backtrader\myscripts\Trading Package\Working Trading Modelv172_pairs.py"  #Type this in at command prompt to profile code, make sure to cd\ first
import backtrader as bt
import backtrader.indicators as btind
from backtrader.feeds import mysql
from datetime import date, time, datetime
from collections import defaultdict
import time as t
import math
import itertools
from scipy import stats
import numpy as np
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import matplotlib.pyplot as plt
from numba import jit


class UserInputs():

	def datalist(data_req):
		"""
		Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		"""
		#XLF and XRE a problem
		#Define baskets of stocks with sensible pair relationships for pairs trading - etfs for sector (leader) listed first
		sector1 = ('ATVI','CHTR','CMCSA','DIS','EA','FB','GOOG','NFLX','T','TMUS','TTWO','VZ')
		sector2 = ('XRT','AMZN','AZO','BKNG','DG','DLTR','EBAY','EXPE','GM','HAS','HD','LOW','MAR','MCD','NKE','ORLY','ROST','SBUX','TGT','TJX','ULTA','WYNN','YUM')
		sector3 = ('CL','CLX','COST','EL','GIS','KHC','KMB','KO','KR','MDLZ','MNST','MO','PEP','PG','PM','STZ','SYY','WBA','WMT')
		sector4 = ('COP','CVX','KMI','PSX','XOM')
		sector5 = ('AFL','ALL','AON','AXP','BAC','BK','BLK','C','CB','CME','COF','GS','ICE','JPM','MCO','MET','MMC','MS','MSCI','PGR','PNC','SCHW','SPGI','TFC','TROW','TRV','USB','WFC','WLTW')
		sector6 = ('XLV','A','ABBV','ABT','ALGN','ALXN','AMGN','ANTM','BAX','BDX','BIIB','BMY','BSX','CERN','CI','CNC','CVS','DHR','EW','GILD','HCA','HSIC','HUM','IDXX','ILMN','INCY','ISRG','JNJ','LLY','MDT','MRK','MYL','PFE','REGN','RMD','SYK','TMO','UNH','VRTX','ZTS')
		sector7 = ('AAL','BA','CAT','CSX','CTAS','DE','EMR','ETN','FAST','FDX','GD','GE','HON','INFO','ITW','JBHT','LHX','LMT','MMM','NOC','NSC','PCAR','ROP','RTX','UNP','UPS','VRSK','WM')
		sector8 = ('XLK','AAPL','ACN','ADBE','ADI','ADP','ADSK','AMAT','APH','AVGO','CDNS','CRM','CSCO','CTSH','CTXS','FIS','FISV','GPN','HPQ','IBM','INTC','INTU','KLAC','LRCX','MA','MCHP','MSFT','MSI','MU','MXIM','NLOK','NOW','NTAP','NVDA','ORCL','PAYX','PYPL','QCOM','SNPS','SWKS','TXN','V','VRSN','WDC','XLNX')
		sector9 = ('APD','DD','ECL','NEM','SHW')
		sector10 = ('XHB','AMT','CCI','DLR','EQIX','EQR','PLD','PSA','SBAC')
		sector11 = ('XLU','AEP','AWK','D','DUK','ED','ES','EXC','FE','NEE','PEG','SO','SRE','WEC')
		datalist = sector1+sector2+sector3+sector4+sector5+sector6+sector7+sector8+sector9+sector10+sector11  #load all sectors into one list so all data can be loaded into system at once
		
		#IB DATA REQUEST - Can not make more than 60 requests in a 10 minute period
		#ibdatalist = ('MCD','AAPL','SPY')  #'AAPL-STK-SMART-USD
		#ibdatalist = ('SPY','AAPL','MCD','A', 'AAL','ABBV','ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM','CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS')  #'AAPL-STK-SMART-USD'
		#STOCKS REMOVED DUE TO NOT LOADING: AGN - aquired by ABBV,
		#ibdatalist = ('SPY','A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG','ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS')		
		
		ibforex_datalist = () #'EUR','GBP','AUD'
		#ibdatalist = ('EUR.USD','GBP.USD') #Make sure not to include comma after last ticker or program won't read in live trading
		
		if data_req == 'ib':
			return ibdatalist
		elif data_req == 'hist':
			return datalist
		elif data_req == 'forex': 
			return ibforex_datalist
		elif data_req == 'sector1': 
			return sector1
		elif data_req == 'sector2': 
			return sector2
		elif data_req == 'sector3': 
			return sector3
		elif data_req == 'sector4': 
			return sector4
		elif data_req == 'sector5': 
			return sector5
		elif data_req == 'sector6': 
			return sector6
		elif data_req == 'sector7': 
			return sector7
		elif data_req == 'sector8': 
			return sector8
		elif data_req == 'sector9': 
			return sector9
		elif data_req == 'sector10': 
			return sector10
		elif data_req == 'sector11': 
			return sector11
			

	def model_params():
		params = dict(
			live_status = False,  #Flip between live trading (True) and backtesting (False)
			start_date = datetime(2018,6,1), #Dates for backtesting
			end_date = datetime(2018,6,12),
			t0_on = True,
			t1_on = False,
			t2_on = False,
			plot = False,
			timeframe0 = 5, #MINUTES
			timeframe1 = 15, #MINUTES
			timeframe2 = 60, #MINUTES 
			sessionstart = time(8,30),
			sessionend = time(14,55),
			ib_open_time = time(8,15),
			nysetick_on = False,  #for LIVE trading only
			forex_on = False, #for LIVE trading only
			start_cash=100000,  #For backtesting only, live trading calls broker for available cash
			)
		return params		
				
class Strategy(bt.Strategy):
	"""Class to initialize indicators, code trading strategies, determine trade entry and trade exit criteria """
	
	params = dict(
			dollars_risked_per_trade = 300,
			total_dollars_risked = 20000,
			target = 3,  #multiple of dollars risks per trade, to determine profit target per trade.  "2" represents target that is double dollars risked
			min_touches = 2,#Support/Resistance - # of times price has to hit expected levels
			tol_perc = 20, #how far most recent high(low) can be from period maximum(minimum) - if this spread is within this tolerance, represents a "touch".  Expressed as % of total max-min move range over period
			bounce_perc = 0,#Keep at 0 - use only if you want to influence when support/resistance is calculated, as opposed to always calculating when touchpoints are hit (preferable)
			writer = 'off', #export results to CSV output report 'on' or 'off'
			sma1 = 5,
			sma2 = 3,
			ema1 = 5,  #8
			ema2 = 10, #20
			z_entry = 5,  #significance level required to enter pairs trade
			z_stop = .5,  #stop loss range measured as z-statistic (i.e. if z-entry is 3, and z-stop is .5, stop is z value 3.5)
			signif = .01, #(.10, .05, and .01 available) for statistical tests: .01 ideal
			pairs_lookback = 234,
			obv = 10,
			atrper = 5,
			atrdist = 2,   
			slope_per = 5,
			breakout_per = 5, 
			avg_per = 5,
			rsi = 10,
			adx = 10,
			stoch_per = 5,
			stoch_fast = 3,
			boll_per = 10,
			boll_dist = 2,
			lookback = 10,
			correl_per = 312, #4 days is 312 periods
			rank = 5, #How many tickers to select from ticker list
			)
			
	def __init__(self):		
	
		"""initialize parameters and variables for Strategy Class"""
		#ib = IB_Scan()
		#print(ib.ticker_list_gain)
		#print(ib.ib_gainers())
		#self.ibdatalist = ibdatalist_gainers + ibdatalist_losers
		
		#Set program start time
		self.start_time=datetime.now().time()
		print(f'Program start at {self.start_time}')
		print(f'Program time period: {UserInputs.model_params().get("start_date")} to {UserInputs.model_params().get("end_date")}')
		print(self.getdatanames())
		#print(f'Program Parameters: {self.params._getitems()}')
		
		#-----------------------------------------------------------------
		#CRITICAL CODE FOR LOOPING THROUGH DATA
		#Get number corresponding to data name, i.e. SPY0 = self.data0, SPY1 = self.data1, etc.  Needed to iterate by data name later
		self.datas_dic = {}
		for num in range(0,len(self.getdatanames())):
			sym_name = self.datas[num]._name
			
			if not sym_name in self.datas_dic:
				self.datas_dic[sym_name] = eval('self.data%s' % num)
		
		#-----------------------------------------------------------------		
		#initialize variables and dicts
		self.trade_end = time(14,50)
	
		self.nextcounter = 0
		self.cor_counter = 0		
		self.prenext_done = False
		self.pos = 0
		self.cash_avail = 0
		self.data_live = False
		self.tick_close = 0
		self.sortflag = 0
		self.ticker_list = []
		
		self.inds = dict()
		self.rtop_dict = dict()
		self.rbot_dict = dict()
		self.merged_dict = defaultdict(list)
		self.long_stop_dict = defaultdict(list)
		self.short_stop_dict = defaultdict(list)
		self.gap_dict = defaultdict(list)
		self.perc_chg_dict = defaultdict(list)
		self.still_in_dict = defaultdict(list)
		self.correl_dict = defaultdict(list)
		self.eps_dict=defaultdict(lambda: defaultdict(list))
		
		#Create/Instantiate objects to access UserInputs class
		self.modelp = UserInputs.model_params()

		self.initialize_pairs()
		
		#from sqlalchemy import *
		#self.sql_fund()
	
		#---------------------------------------------------------------------------------------------------------------------------
		#Initialize dictionary's
		for i, d in enumerate(self.datas):	
			#Initialize dictionaries by appending 0 value
			self.inds[d._name] = dict()  #Dict for all indicators
			
			#Instantiate exact data references (can't loop or will only spit out last value)
			if d._name == 'TICK-NYSE0':
				self.tick_close = d.close
				
			if d._name =='SPY0':
				self.spy_close = d.close
				
			if d._name =='VIX':
				self.vix_close = d.close
			
			if d._name[:-1] != 'TICK-NYSE':
#*********************************************INITITIALIZE INDICATORS*********************************************************				
				#self.inds[d._name]['spy'] = btind.ticker(d,self.spy_close,plot=True)
				self.inds[d._name]['close'] = btind.close(d.close,period=self.p.pairs_lookback,plot=False)	#history of closing prices
				#self.inds[d._name]['slope'] = btind.Slope(d,period=self.p.slope,plot=False)							
				#self.inds[d._name]['slope_of_slope'] = btind.Slope(self.inds[d._name]['slope'],period=self.p.slope_per,plot=False)
				#self.inds[d._name]['obv'] = btind.obv(d,period=self.p.obv,plot=True)
				#self.inds[d._name]['slope_obv'] = btind.Slope(self.inds[d._name]['obv'],period=self.p.obv,plot=False)
				#self.inds[d._name]['vwap'] = btind.vwap(d,plot=True)
				#self.inds[d._name]['atr'] = btind.ATR(d,period=self.p.atrper,plot=False)
				#self.inds[d._name]['perc_chg'] = btind.PercentChange(d.open,period=5,plot=False)
				#self.inds[d._name]['atr_stop'] = btind.atr_stop(d,self.inds[d._name]['atr'],live = self.modelp.get('live_status'),atrdist = self.p.atrdist,dollars_risked = self.p.total_dollars_risked,dollars_per_trade = self.p.dollars_risked_per_trade,plot=False)
				#self.inds[d._name]['gap'] = btind.gap(d,period=self.p.breakout_per,plot=False)
				#self.inds[d._name]['zigzag'] = btind.zigzag(d,plot=True)
				#self.inds[d._name]['prior_day'] = btind.priorday(d,period=79,plot=False)
				#self.inds[d._name]['hammer'] = btind.HammerCandles(d)											
				#self.inds[d._name]['three_line_strike'] = btind.three_line_strike(d)										
				#self.inds[d._name]['ema1'] = btind.EMA(d,period=self.p.ema1,plot=True)
				#self.inds[d._name]['ema2'] = btind.EMA(d,period=self.p.ema2,plot=True)
				#self.inds[d._name]['adx'] = btind.ADX(d,period=self.p.adx,plot=True)	
				#self.inds[d._name]['slope_adx'] = 	btind.Slope(self.inds[d._name]['adx'],period=self.p.slope_per,plot=False)																		
				#self.inds[d._name]['bollinger'] = btind.BollingerBands(d.close,period=self.p.boll_per,devfactor = self.p.boll_dist,plot=True)						
				#self.inds[d._name]['slope_ema1'] = btind.Slope(self.inds[d._name]['ema1'],period=self.p.slope_per,plot=False)	
				#self.inds[d._name]['slope_ema2'] = btind.Slope(self.inds[d._name]['ema2'],period=self.p.slope_per,plot=False)			
				#self.inds[d._name]['slope_ema_width'] = btind.Slope(self.inds[d._name]['ema1']-self.inds[d._name]['ema2'],period=self.p.slope_per,plot=False)											
				#self.inds[d._name]['rsi']= btind.RSI(d,period=self.p.rsi,safediv=True,plot=False)								
				#self.inds[d._name]['stochastic'] = btind.StochasticSlow(d,period=self.p.stoch_per,period_dfast= self.p.stoch_fast,safediv=True,plot=True)
				#self.inds[d._name]['adx'].plotinfo.plotmaster = self.inds[d._name]['rsi']   #Plot ADX on same subplot as RSI
				#self.inds[d._name]['support'] = btind.Support(d,period=self.p.lookback,min_touches = self.p.min_touches,tol_perc = self.p.tol_perc,bounce_perc = self.p.bounce_perc,plot=True)
				#self.inds[d._name]['resistance'] = btind.Resistance(d,period=self.p.lookback,min_touches = self.p.min_touches,tol_perc = self.p.tol_perc,bounce_perc = self.p.bounce_perc,plot=True)	
				#self.inds[d._name]['engulfing'] = btind.EngulfingCandles(d)	
											
				#Initialize target size, target long, and target short prices
				#self.inds[d._name]['target_size'] = self.inds[d._name]['atr_stop'].lines.size			
				#self.inds[d._name]['target_long'] = d.open +(self.p.dollars_risked_per_trade*self.p.target)/self.inds[d._name]['target_size']																	
				#self.inds[d._name]['target_short'] = d.open -(self.p.dollars_risked_per_trade*self.p.target)/self.inds[d._name]['target_size']																		
		
		print('Start preloading data to meet minimum data requirements')	
		
#**************************************************************************************************************************************
	""" def start
	def start(self):
		for i, d in enumerate(self.datas): 
			if self.modelp.get('live_status') and d.contractdetails is not None:
				print(f'ContractDetails: {d.contractdetails.m_longName} {d.contractdetails.m_marketName} {d.contractdetails.m_timeZoneId}')
	"""
	
	def notify_order(self, order):
		if order.status == order.Completed: 
			if order.isbuy() and self.pos==0:
				print(f"{order.data._name} ENTER LONG POSITION, Date: {self.dt} Price: {order.executed.price}, Cost: {order.executed.value}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.isbuy() and self.pos < 0:
				print(f"{order.data._name} EXIT SHORT POSITION, Date: {self.dt} Price: {order.executed.price}, Cost: {order.executed.value}, Size {order.executed.size}, Type {order.getordername()} Cash: {self.broker.getcash()} Acct: {self.broker.getvalue()}")
			
			if order.issell() and self.pos==0:
				print(f"{order.data._name} ENTER SHORT POSITION, Date: {self.dt} Price: {order.executed.price}, Cost: {order.executed.value}, Size {order.executed.size}, Type {order.getordername()} ")
			
			if order.issell() and self.pos > 0:
				print(f"{order.data._name} EXIT LONG POSITION, Date: {self.dt}  Price: {order.executed.price}, Cost: {order.executed.value}, Size {order.executed.size}, Type {order.getordername()} Cash: {self.broker.getcash()} Acct: {self.broker.getvalue()}")
		
		
	def notify_store(self, msg, *args, **kwargs):
		print('*' * 5, 'STORE NOTIF:', msg)


	def notify_trade(self, trade):
		if trade.isclosed:
			print(f"{trade.data._name} POSITION CLOSED {self.dt} Price: {trade.price}, Profit: {trade.pnl} Profit w/Comm:{trade.pnlcomm} Cash: {self.broker.getcash()} Acct: {self.broker.getvalue(datas=None, mkt=False, lever=False)}")
		
	
	def notify_data(self, data, status):
		#To notify us when delayed backfilled data becomes live data during live trading
		print('*' * 5, 'DATA NOTIF:', data._getstatusname(status))
		if status == self.data.LIVE:
			self.data_live = True

			
	def prenext(self):
		pass
		#pre-loads all indicator data for all timeframes before strategy starts executing
		#print(f"Prenext len {len(self)}")
		

	def nextstart(self):
		#There is a nextstart method which is called exactly once, to mark the switch from prenext to next. 
		self.prenext_done = True
		print('---------------------------------------------------------------------------------------------------------------')	
		print(f'NEXTSTART called with strategy length {len(self)} - Pre Data has loaded, backtesting can start')
		print('---------------------------------------------------------------------------------------------------------------')
		super(Strategy, self).nextstart()		

	#*****************************************************************************************************************************
	def next(self):
		"""Iterates over each "line" of data (date and ohlcv) provided by data feed"""

		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		if self.modelp.get('live_status'):
			self.dt = self.data.num2date()
		else:
			self.dt = self.datetime.datetime()
		
		#print(self.dt)
		self.hour = self.dt.hour
		self.minute = self.dt.minute
		self.hourmin = time(self.dt.hour,self.dt.minute)
		
		#-----------------------------------------------------------------------------------------------------
		#FOR PAIRS TRADING - Get correlations, rank them, and store correlations pairs and value in dctionary
		if self.hour==8 and self.minute==30:
			self.pairs_exit()  #in case market closed early and there are outstanding positions
			#Pairs Trading Strategy
			self.clear_pairs()
			self.create_pairs(self.data,self.p.signif)  #get initial pairs list using Johansen test
			self.calc_spread_zscore()
			self.pairs_entry(self.p.z_entry)
		#-------------------------------------------------------------------------------------------------------
		
		if self.hourmin > time(8,45) and self.hourmin <= self.trade_end:
			self.pairs_exit()
			
		#if self.hour==8 and self.minute==35:
			#self.plot_pair()
			#self.plot_spread()
			#self.plot_zscore()	
		
			#--------------------- --------------------------------------------------------------------------------------
	
	#*********************************************************************************************************************
	def initialize_pairs(self):
		#FOR PAIRS Trading 
		
		self.first_run_complete = False
		self.pair_count = 0
		self.cointegrating_pairs = []
		self.adfpval = []
		self.all_tickers = []
		self.pair_spread = defaultdict(list)
		self.pair_zscore= defaultdict(list)
		self.pair_close_dict = defaultdict(list)
		self.pair_spread_dict = defaultdict(list)
		self.pair_zscore_dict = defaultdict(list)
		self.long_pair_dict = defaultdict(list)
		self.short_pair_dict = defaultdict(list)
		self.exit_pair_dict = defaultdict(list)
		self.hratio_close_dict = defaultdict(list)
		self.plotdict = defaultdict(list)
		self.inorder_dict = defaultdict(list)
		self.size_dict = defaultdict(lambda: defaultdict(list))
		self.zscore_dict = defaultdict(list)
		self.inorder_dict = defaultdict(list)#allows you to keep nesting lists within dictionary
		self.pos_dict = defaultdict(list)
		self.zscore_set = defaultdict(list)
		self.plot_track = defaultdict(lambda: defaultdict(list))

		#Get pair combinations within each basket of stocks
		self.sector1 = list(itertools.combinations(UserInputs.datalist('sector1'), 2)) 
		self.sector2 = list(itertools.combinations(UserInputs.datalist('sector2'), 2))
		self.sector3 = list(itertools.combinations(UserInputs.datalist('sector3'), 2))
		self.sector4 = list(itertools.combinations(UserInputs.datalist('sector4'), 2))
		self.sector5 = list(itertools.combinations(UserInputs.datalist('sector5'), 2))
		self.sector6 = list(itertools.combinations(UserInputs.datalist('sector6'), 2))
		self.sector7 = list(itertools.combinations(UserInputs.datalist('sector7'), 2))
		self.sector8 = list(itertools.combinations(UserInputs.datalist('sector8'), 2))
		self.sector9 = list(itertools.combinations(UserInputs.datalist('sector9'), 2))
		self.sector10 = list(itertools.combinations(UserInputs.datalist('sector10'), 2))
		self.sector11 = list(itertools.combinations(UserInputs.datalist('sector11'), 2))
	
	
	def create_pairs(self,d,signif):
		"""
		Get list of all tickers defined, perform Johansen test for cointigration and cointegrated stocks
		Cointegration test helps to establish the presence of a statistically significant connection 
		between two or more time series.  Order of integration(d) is the number of differencing required 
		to make a non-stationary time series stationary.  Now, when you have two or more time series, 
		and there exists a linear combination of them that has an order of integration (d) less than that of 
		the individual series, then the collection of series is said to be cointegrated.  When two or more 
		time series are cointegrated, it means they have a long run, statistically significant relationship.
		"""	
		
		if len(d) > self.p.pairs_lookback * (self.modelp.get('timeframe0')/self.modelp.get('timeframe0')) * 2:  #ensure enough data has loaded for lookback period
		#Loop through all pairs, run Johansen test, and pick out cointegrated stocks
			append = self.adfpval.append
			for (a,b,c,d,e,f,g,h,i,j,k) in itertools.zip_longest(self.sector1, self.sector2, self.sector3,self.sector4,self.sector5,self.sector6,self.sector7,self.sector8,self.sector9,self.sector10,self.sector11):  #iterates through multiple lists at same time - if you have 3 lists, then (a,b,c) in.. (sector1,2,3).  if you have 4 lists, then (a,b,c,d) in ..(sector 1,2,3,4)
				for n in (a,b,c,d,e,f,g,h,i,j,k):  #each iteration(it) produces pairs from each list
					if n is not None:  #remove any iterations yielding none values (for shorter lists)
						t1 = f'{n[0]}0'
						t2 = f'{n[-1]}0'
						name = f'{t1}/{t2}'
						
						t1_data = np.array(self.inds.get(t1).get('close').get(size=self.p.pairs_lookback)) 	#Y variable
						t2_data = np.array(self.inds.get(t2).get('close').get(size=self.p.pairs_lookback))	#X variable
						combined_data = np.vstack((t1_data, t2_data)).T
						
						# The second and third parameters indicate constant term, with a lag of 1. 
						result = coint_johansen(combined_data, 0, 1)  #Inputted as Y Variable first, X Var second.  testing only 2 tickers at a time.  Can not conduct test with more than 12 tickers
						hedge_ratio = result.evec[:, 0]	#The first column of eigenvectors contains the best weights (shortest half life for mean reversion).  This determine shares of each instrument.
						hedge_ratio_t1 = hedge_ratio[0]
						hedge_ratio_t2 = hedge_ratio[1]
										
						# the 90%, 95%, and 99% confidence levels for the trace statistic and maximum eigenvalue statistic are stored in the first, second, and third column of cvt and cvm, respectively
						confidence_level_cols = {90: 0, 95: 1,99: 2}
						confidence_level_col = confidence_level_cols[(1-signif)*100]
						trace_crit_value = result.cvt[:, confidence_level_col]
						eigen_crit_value = result.cvm[:, confidence_level_col]  #t1_trace = trace_crit_value[0] #t2_trace = trace_crit_value[1] #t1_eigen = eigen_crit_value[0] #t2_eigen = eigen_crit_value[1] t1_lr1 = result.lr1[0] #t2_lr1 = result.lr1[1] #t1_lr2 = result.lr2[0] #t2_lr2 = result.lr2[1]
						
						# The trace statistic and maximum eigenvalue statistic are stored in lr1 and lr2 - see if they exceeded the confidence threshold
						if np.all(result.lr1 >= trace_crit_value) and np.all(result.lr2 >= eigen_crit_value):			
							#self.cointegrating_pairs.append(dict(t1=ticker1,t2=ticker2,hratio_t1=hedge_ratio_t1,hratio_t2=hedge_ratio_t2))
							#print(f'{self.dt} {self.hour} {self.minute} Johansen: Pair:{ticker1}/{ticker2} , {ticker1} - Trace Stat: {t1_lr1} is > Crit Val {t1_trace} Max Eigen Stat {t1_lr2} > {t1_eigen} Crit Val, Hedge: {hedge_ratio[0]}')
							#print(f'{self.dt} {self.hour} {self.minute} Johansen: Pair:{ticker1}/{ticker2} , {ticker2} - Trace Stat: {t2_lr1} is > Crit Val {t2_trace} Max Eigen Stat {t2_lr2} > {t2_eigen} Crit Val, Hedge: {hedge_ratio[1]}')
							#self.adfpval['t1'].append(t1)
							#self.adfpval['t2'].append(t2)
							#self.adfpval['hratio1'].append(hedge_ratio_t1)
							#self.adfpval['hratio2'].append(hedge_ratio_t2)
							append(dict(name=name,t1=t1,t2=t2,hratio1 = hedge_ratio_t1,hratio2=hedge_ratio_t2))
						
							"""
							#Perform regression on pairs
							beta_set = np.array(t2_data)
							beta = beta_set.reshape((len(beta_set), 1))
							Y_set = np.array(t1_data)
							Y = Y_set.reshape((len(Y_set), 1))
							(m, c, rvalue, pvalue, stderr) = stats.mstats.linregress(beta, Y)  #input as linregress(x,y)
					
							#Create residual series for ADF test (i.e. errors)
							coef_price = np.multiply(m,beta_set)
							projected = np.add(coef_price,c) #vector approach to solve project = m * beta[n][0] + c
							error = np.subtract(Y_set,projected)  #error = value - projected for n,value in enumberate(Y)
							
							#Perform ADF test on pairs
							r = ts.adfuller(error, autolag='AIC')
							#output = {'test_statistic':round(r[0], 4), 'pvalue':round(r[1], 4), 'n_lags':round(r[2], 4), 'n_obs':r[3]}
							p_value = r[1]	
							
							if p_value <= signif and self.pair_count <= 10:
								self.adfpval.append(dict(t1=ticker1,t2=ticker2,hratio1 = hedge_ratio_t1,hratio2=hedge_ratio_t2))
								self.pair_count += 1	
								#self.pval_dict[f'{t1}/{t2}'].append(p_value)			
								print(f" ADF Test => P-Value {p_value} <= Significance Level {signif}. Rejecting Null Hypothesis that Data has unit root (non-stationary).")
								#print(f" ADF Test => Series is Stationary.")
							else:
								print(f" ADF Test => P-Value {p_value} > Significance Level {signif}. Weak evidence to reject the Null Hypothesis.")
								#print(f" ADF Test => Series is Non-Stationary.") 
							"""
					
	def calc_spread_zscore(self):
		"""Get initial zscore of spread for each pair"""
		print (f'Number of ADF PAIRS: {len(self.adfpval)}')	

		for i in self.adfpval:	
			t1 = i['t1'] 	#Y Variable
			t2 = i['t2']	#X Variable
			name = f'{t1}/{t2}'
			hratio_t1 = i['hratio1']
			hratio_t2 = i['hratio2']
			t1_data = self.inds.get(t1).get('close').get(size=self.p.pairs_lookback)
			t2_data = self.inds.get(t2).get('close').get(size=self.p.pairs_lookback)
			pos_t1 = self.getpositionbyname(t1).size
			pos_t2 = self.getpositionbyname(t2).size
			
			arrt1 = np.multiply(hratio_t1,np.array(t1_data)) #create array of hedge ratio * close price
			arrt2 = np.multiply(hratio_t2,np.array(t2_data)) 
			spread = np.add(arrt1,arrt2)
			zscore = stats.zscore(spread)
			i['zscore']= abs(zscore[-1])  #add new zscore key to adfpval dict
			self.pair_zscore_dict[f'{name}'] = [x for x in zscore]	#unpack numpy array vales
			self.pair_spread_dict[f'{name}'] = [x for x in spread]	#unpack numpy array vales			
			self.inorder_dict[f'{name}'].append(False) #initialize inorder dictionary
			self.zscore_dict[name].append(0)
			self.pos_dict[t1].append(False)
			self.pos_dict[t2].append(False)
				
		#Sort advpval dict by zscore
		self.zscore_sort = sorted(self.adfpval, key=lambda k: k['zscore'], reverse=True)
		#print(self.zscore_sort)
		
		self.first_run_complete = True


	def pairs_exit(self,z_exit_threshold=.1):
		for i, pair in enumerate(self.plot_track):
			t1 = self.plot_track[pair].get('t1')[0]
			t2 =  self.plot_track[pair].get('t2')[0]
			name = f'{t1}/{t2}'
			d1 = self.datas_dic.get(t1)
			d2 = self.datas_dic.get(t2)
			hratio_t1 = self.zscore_sort[0].get('hratio1')
			hratio_t2 = self.zscore_sort[0].get('hratio2')
			t1_close = d1.close[0]
			t2_close = d2.close[0]
			
			#Get cash available and positions
			cash_avail = self.broker.getvalue()
			
			#Get current zscores, entry, exit, and stop signals
			spread_now = hratio_t1 * t1_close + hratio_t2 * t2_close #create array of hedge ratio * close price
			self.pair_spread_dict[f'{name}'].append(spread_now)
			self.pair_spread_dict[f'{name}'].pop(0)	#remove first item in dictionary (keep length to lookback period)
			zscores = stats.zscore(self.pair_spread_dict.get(f'{t1}/{t2}')[-self.p.pairs_lookback:])
			zscore_now = zscores[-1]
			zscore_last = zscores[-2]
			exit_signal = abs(zscore_now) <= z_exit_threshold
			stop_signal = abs(zscore_now) >= self.zscore_dict.get(f'{name}')[-1]
			
			#Exit position
			if self.inorder_dict.get(f'{name}')[-1] and (exit_signal or stop_signal or self.hourmin==self.trade_end):
				self.close(t1,size=self.size_dict.get(name).get(t1)[-1])	#exit on 5 min bar	
				self.close(t2,size=self.size_dict.get(name).get(t2)[-1])	#exit on 5 min bar				
				
				if exit_signal:
					print(f"!!!PROFIT TARGET HIT!!! - EXIT pair {name} zscore: {zscore_now}  Acct {self.broker.getvalue()}")
				if stop_signal:
					print(f"{self.dt} {name}**********STOPPED OUT********** zscore: {zscore_now} {self.zscore_dict.get(f'{name}')[-1]} Acct {self.broker.getvalue()}")
				else:
					self.eod_exit(self.data)
					print(f'{self.dt} {name} END OF DAY - EXIT POSITION  Acct {self.broker.getvalue()}')
				
				self.inorder_dict[f'{name}'].append(False)
				self.pos_dict[f'{t1}'].append(False)  #Need separate position tracking since backtrader getpos doesn't detect multiple positions in same instrument executed at same time
				self.pos_dict[f'{t2}'].append(False)
			
					
	def pairs_entry(self,z_entry_threshold):
		"""Create the entry signals based on the exceeding of 
		z_enter_threshold for entering a position and falling below"""	
		for i in self.zscore_sort:
			#Extract invidual tickers from pair, and get close prices for each ticker
			t1 = i['t1'] 	#Y Variable
			t2 = i['t2']	#X Variable
			d1 = self.datas_dic.get(t1)
			d2 = self.datas_dic.get(t2)
			name = f'{t1}/{t2}'
			hratio_t1 = i['hratio1']
			hratio_t2 = i['hratio2']
			t1_close = d1.close[0]
			t2_close = d2.close[0]
			
			#Get cash available and positions
			cash_avail = self.broker.getvalue()
			
			#Get current zscores, entry, exit, and stop signals
			spread_now = hratio_t1 * t1_close + hratio_t2 * t2_close #create array of hedge ratio * close price
			self.pair_spread_dict[f'{name}'].append(spread_now)
			self.pair_spread_dict[f'{name}'].pop(0)	#remove first item in dictionary (keep length to lookback period)
			zscores = stats.zscore(self.pair_spread_dict.get(f'{t1}/{t2}')[-self.p.pairs_lookback:])
			zscore_now = zscores[-1]
			zscore_last = zscores[-2]
			long_signal = zscore_now <= -z_entry_threshold
			short_signal = -1*(zscore_now >= z_entry_threshold)
			total_entry_signals = long_signal + short_signal
			
			#Enter position
			if total_entry_signals !=0 and not self.inorder_dict.get(f'{name}')[-1] and self.pos_dict.get(t1)[-1]==False and self.pos_dict.get(t2)[-1]==False and cash_avail > self.p.total_dollars_risked:
				# Calculate weights and position size
				hratio_weights_t1 = hratio_t1 * t1_close
				hratio_weights_t2 = hratio_t2 * t2_close
				weights_t1_set = total_entry_signals * hratio_weights_t1
				weights_t2_set = total_entry_signals * hratio_weights_t2
				total_weights = abs(weights_t1_set) + abs(weights_t2_set)
				weights_t1 = weights_t1_set/total_weights
				weights_t2 = weights_t2_set/total_weights
				cash_size_t1 = self.p.total_dollars_risked * weights_t1
				cash_size_t2 = self.p.total_dollars_risked * weights_t2
				size_t1 = int(cash_size_t1/t1_close)
				size_t2 = int(cash_size_t2/t2_close)
				
				if weights_t1>0:
					#long stock 1 of pair
					long_name = f'For Pair {name}: - Enter LONG Trade for leg {t1}'
					self.long_ord = self.buy(data=t1,
					size= size_t1,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t1].append(size_t1)
					print(f"{self.dt} {self.hour} {self.minute} For Pair {name} - Enter LONG Trade leg {t1} price {t1_close} size {size_t1} zscore_now:{zscore_now} z-score last:{zscore_last}")
				if weights_t2>0:
					#long stock 2 of pair
					long_name = f'For Pair {name}: - Enter LONG Trade for leg {t2}'
					self.long_ord = self.buy(data=t2,
					size= size_t2,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t2].append(size_t2)
					print(f"{self.dt} {self.hour} {self.minute} For Pair {name} - Enter LONG Trade leg {t2} price {t2_close} size {size_t2} zscore_now:{zscore_now} z-score last:{zscore_last}")
				if weights_t1<0:
					#Short stock 1 of pair
					short_name = f'For Pair {name}: - Enter SHORT Trade for leg {t1}'
					self.short_ord = self.sell(data=t1,
					size= size_t1,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t1].append(size_t1)
					print(f"{self.dt} {self.hour} {self.minute} For Pair {name} - Enter SHORT Trade leg {t1} price {t1_close} size {size_t1} zscore_now:{zscore_now} z-score last:{zscore_last}")
				if weights_t2<0:
					#Short stock 2 of pair
					short_name = f'For Pair {name}: - Enter SHORT Trade for leg {t2}'
					self.short_ord = self.sell(data=t2,
					size= size_t2,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t2].append(size_t2)
					print(f"{self.dt} {self.hour} {self.minute}  For Pair {name} - Enter Short Trade leg {t2} price {t2_close} size {size_t2} zscore: {zscore_now} z-score last:{zscore_last}")
				
				#Track inorder status and stop prices
				self.inorder_dict[f'{name}'].append(True)
				self.pos_dict[f'{t1}'].append(True)
				self.pos_dict[f'{t2}'].append(True)
				self.zscore_dict[f'{name}'].append(abs(zscore_now)+self.p.z_stop)
				self.plot_track[f'{name}'][f't1'].append(t1)
				self.plot_track[f'{name}'][f't2'].append(t2)
					

	def clear_pairs(self):
		self.adfpval.clear()
		self.cointegrating_pairs.clear()
		self.pair_close_dict.clear()
		self.pair_spread_dict.clear()
		self.pair_zscore_dict.clear()
		self.long_pair_dict.clear()
		self.short_pair_dict.clear()
		self.exit_pair_dict.clear()
		self.hratio_close_dict.clear()
		self.first_run_complete = False
		self.inorder_dict.clear()
		self.size_dict.clear()
		self.zscore_dict.clear()
		self.pos_dict.clear()
		self.zscore_set.clear()
		self.plot_track.clear()
		
		
	def plot_pair(self):
		if self.plot_track:
			fig = plt.figure()
			cols = 2
			myrows = int(len(self.plot_track)/cols)	#define number of rows in multi-chart plot
			
			if myrows > 0:
				rows=myrows
			else:
				rows=1

			for i, pair in enumerate(self.plot_track):
				if i <= (rows*cols)-1 or i==1:
			
					t1_name = self.plot_track[pair].get('t1')[0]
					t2_name =  self.plot_track[pair].get('t2')[0]
					
					t1_data= self.inds.get(t1_name).get('close').get(size=self.p.pairs_lookback)
					t2_data = self.inds.get(t2_name).get('close').get(size=self.p.pairs_lookback)

					ax = fig.add_subplot(rows, cols, i+1)
					ax2 = ax.twinx()
					ax.plot(t1_data,'r-')
					ax2.plot(t2_data, 'b-')
					#ax.set_ylabel(f'{t1_name} data', color='g')
					#ax2.set_ylabel(f'{t2_name} data', color='b')
					ax.set_title(f'{t1_name} and {t2_name} Close Prices')
			
			plt.tight_layout()			
			plt.show()

				
	def plot_spread(self):
		if self.plot_track:
			fig = plt.figure()
			cols = 2

			myrows = int(len(self.plot_track)/cols)
			if myrows > 0:
				rows=myrows
			else:
				rows=1

			for i, pair in enumerate(self.plot_track):
				if i <= (rows*cols)-1:
					t1_name = self.plot_track[pair].get('t1')[0]
					t2_name =  self.plot_track[pair].get('t2')[0]
					spread_data= self.pair_spread_dict.get(f'{t1_name}/{t2_name}')
					
					ax = fig.add_subplot(rows, cols, i+1)
					ax.plot(spread_data, 'b-')
					#ax.set_ylabel(f'{t1_name}/{t2_name} spread', color='b')
					ax.set_title(f'{t1_name}/{t2_name} spread')
			
			plt.tight_layout()		
			plt.show()
	
	
	def plot_zscore(self):
		if self.plot_track:
			fig = plt.figure()
			cols = 2
			myrows = int(len(self.plot_track)/cols)	#define number of rows in multi-chart plot
			
			if myrows > 0:
				rows=myrows
			else:
				rows=1

			for i, pair in enumerate(self.plot_track):
				if i <= (rows*cols)-1:
					t1 = self.plot_track[pair].get('t1')[0]
					t2 =  self.plot_track[pair].get('t2')[0]
					name = f'{t1}/{t2}'

					spread_data=self.pair_zscore_dict[f'{name}']
					ax = fig.add_subplot(rows, cols, i+1)
					ax.plot(spread_data,'g-')
					ax.axhline(y=0, color='r', linestyle='-')
					#ax.set_ylabel(f'{t1}/{t2} zscore', color='r')
					ax.set_title(f'{t1}/{t2} zscore')
			
			plt.tight_layout()		
			plt.show()
	
	
	def clear_dicts(self):
		self.short_stop_dict.clear()
		self.long_stop_dict.clear()
		self.perc_chg_dict.clear()
		self.correl_dict.clear()
	
				
	def exit_multiday(self):
		#Exit trades if multi-day position
		if self.hour==8 and self.minute==30:
			for i, d in enumerate(self.datas):
				still_in = self.getposition(d).size
				if still_in>0:
					if d._name in self.still_in_dict.keys():
						self.still_in_dict[d._name].pop(0)
						self.still_in_dict[d._name].append(still_in)
					else:
						self.still_in_dict[d._name].append(still_in)
		
		for i in list(self.still_in_dict.keys()):  #need to do list(dict) to avoid changed dictionary size error 
			d = self.datas_dic.get(i)
			if self.tick_close[0]>=800:
				self.exit_trade(d,'long')
				del self.still_in_dict[d._name] 
			elif self.tick_close[0]<=-800:
				self.exit_trade(d,'short')
				del self.still_in_dict[d._name]
			
	
	def sellorder(self,d):
		"""Places sell order and apends size and stops to dictionary"""
		#Calculate Size
		target_size = int(self.inds.get(d._name).get('target_size')[0])
		
		#Calculate STOP (ATR BASED)
		self.short_stop = self.inds.get(d._name).get('atr_stop').lines.short_stop[0]
		
		#Calculate Target Price
		if target_size:
			self.target_short = self.inds.get(d._name).get('target_short')[0]
		
		#SHORT ENTRY ORDER
		#Create Short Entry Order
		short_name = f'{d._name} - Enter Short Trade'
		self.short_ord = self.sell(data=d._name,
					 size=target_size,
					 exectype=bt.Order.Market,
					 transmit=False,
					 )
											
		#Create Fixed Short Stop Loss	 
		short_stop_name = f'{d._name} - Submit STOP for Short Entry'
		self.short_stop_ord = self.buy(data=d._name,
					size=target_size,
					exectype=bt.Order.Stop,
					price = self.short_stop,
					transmit=True,
					parent=self.short_ord,
					)
		
		self.short_stop_dict[d._name].append(self.short_stop_ord)
		print(f'{self.dt} {self.hour} {self.minute} SELL SELL SELL {d._name} - {target_size} shares at {d.close[0]}.  Stop price @ {self.short_stop}')


	def buyorder(self,d):
		"""Places buy order and apends size and stops to dictionary"""		
		#Calculate Size
		target_size = int(self.inds.get(d._name).get('target_size')[0])
		
		#Calculate STOP (ATR BASED) - **** NEEDS TO BE MULTIPLE OF $.005 for IB to accepts
		self.long_stop = self.inds.get(d._name).get('atr_stop').lines.long_stop[0]

		#Create Target Price
		if target_size:
			self.target_long = self.inds.get(d._name).get('target_long')[0]
			
		#CREATE LONG ORDER
		long_name = f'{d._name} - Enter Long Trade'
		self.long_ord = self.buy(data=d._name,
							size=target_size,
							exectype=bt.Order.Market,
							transmit=False,
							)
		
		#Create Fixed Long Stop Loss
		long_stop_name = f'{d._name} - Submit STOP for Long Entry'
		self.long_stop_ord = self.sell(data=d._name,
							size=target_size,
							exectype=bt.Order.Stop,
							price = self.long_stop,
							transmit=True,
							parent=self.long_ord,
							)
								
		#Track if currently in an order or not
		self.long_stop_dict[d._name].append(self.long_stop_ord)
		print(f'{self.dt} {self.hour} {self.minute} BUY BUY BUY {d._name} - {target_size} shares at {d.close[0]}.  Stop price @ {self.long_stop}')
	
	
	def exit_trade(self,d,direction):
		
		#EXIT LOGIC FOR INTRADAY SHORTS
		if direction == 'short':
			#CANCEL ASSOCIATED STOP AND TARGET ORDERS
			if self.short_stop_dict.get(d._name) is not None:
				self.cancel(self.short_stop_dict.get(d._name)[-1])
				print(f'{d._name} {self.dt} {self.hour} {self.minute} Short Stop Order CANCELLED - Exit Criteria Met')
				#self.cancel(self.target_short_dict.get(d._name)[-1])
				
			#SHORT EXIT ORDER - closes existing position and cancels outstanding stop-loss ord	
			print(f'{d._name} {self.dt} {self.hour} {self.minute} EXIT Criteria Met - Exit Short Trade')       
			self.exit_short = self.close(d._name)
			
			#print(f'{self.dt} {self.hour} {self.minute} EXIT SHORT {d._name} - {self.pos} shares at {d.close[0]}')
				
		elif direction == 'long':
			#CANCEL ASSOCIATED STOP AND TARGET ORDERS
			if self.long_stop_dict.get(d._name) is not None:
				self.cancel(self.long_stop_dict.get(d._name)[-1])
				print(f'{d._name} {self.dt} {self.hour} {self.minute} Long Stop Order CANCELLED - Exit Criteria Met')
			
			#LONG EXIT ORDER - closes existing position and cancels outstanding stop-loss order
			print(f'{d._name} {self.dt} {self.hour} {self.minute} EXIT Criteria Met - Exit Long Trade')
			self.exit_long = self.close(d._name)
			
			
	def eod_exit(self,d):
		#EXIT LOGIC FOR EOD EXITS
		#CANCEL ALL ORDERS AT END OF DAY (STOPS AND TARGETS)
		if self.long_stop_dict.get(d._name) is not None:
			self.cancel(self.long_stop_dict.get(d._name)[-1])
			print(f'{d._name} All Stop Orders Cancelled EOD')
		
		if self.short_stop_dict.get(d._name) is not None:
			self.cancel(self.short_stop_dict.get(d._name)[-1])
			#self.cancel(self.target_short_dict.get(d._name)[-1])
		
		self.eod_name = f'{d._name} - EXIT ALL TRADES AT EOD'
		self.eod_close = self.close(d._name,
									name=self.eod_name)

		
	def entry_rules(self,d):	
		#Get available cash
		self.cash_avail = self.broker.getcash()
		
		if not self.modelp.get('live_status'):	
			if (self.cash_avail > self.p.total_dollars_risked
				and self.prenext_done 	#start trading after all prenext data loads
				and self.sortflag == 1	#start trading after sort has happened and stocks have been selected
				):
				return True
			else:
				return False
				
		elif self.modelp.get('live_status'):
			self.cash_avail = self.broker.getcash()
			print(d._name,self.dt,self.hour,self.minute)	
			
			if (self.cash_avail > self.p.total_dollars_risked
				and self.prenext_done #Start trading after all prenext data loads
				and self.data_live
				):
				return True
			else:
				return False	
		
		#print(d._name,self.dt,self.hour,self.minute,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0],self.cash_avail,self.pos)
	
	def rank_perc(self,d):
		"""Create % change ranking across stock universe and return top X and bottom Y as per paramaters"""
		sorted_res = sorted(self.perc_chg_dict.items(), key = lambda x: x[1], reverse=True)  #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
		self.rtop_dict = dict(sorted_res[:self.p.rank])  #Choose subset of tickers with highest rank (i.e. top 3)
		self.rbot_dict = dict(sorted_res[-self.p.rank:])  #Choose subset of tickers with lowest rank (i.e. bottom 3)
		self.merged_dict = {**self.rtop_dict, **self.rbot_dict}
	
		self.sortflag = 1
		#print(f'{d._name} {self.dt} {self.hour} {self.minute}  Top Sort: {self.rtop_dict}, Bottom Sort: {self.rbot_dict}')
	

	def rank_gap(self,d):
		"""Create gap ranks across stock universe and return top X and bottom Y as per paramaters"""
		sorted_res = sorted(self.gap_dict.items(), key = lambda x: x[1], reverse=True) #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
		self.rtop_dict = dict(sorted_res[:self.p.rank])  #Choose subset of tickers with highest rank (i.e. top 3)
		self.rbot_dict = dict(sorted_res[-self.p.rank:])  #Choose subset of tickers with lowest rank (i.e. bottom 3)
		self.merged_dict = {**self.rtop_dict, **self.rbot_dict} 
		
		self.sortflag = 1
		#print(f'{d._name} {self.dt} {self.hour} {self.minute}  Top Sort: {self.rtop_dict}, Bottom Sort: {self.rbot_dict}')
		
	
	def regime_early_bull(self,d):
		#Trend underway, getting stronger
		#Get timeframe 0 values
		self.percK_t0 = self.inds.get(d._name).get('stochastic').lines.percK[0]
		
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 20,
				 self.adx_t2 > 20,
				 self.slope_adx_t1 > 0,
				 self.slope_adx_t2 > 0,
				 self.ema1_t1 > self.ema2_t1,
				 self.ema1_t2 > self.ema2_t2,
				 self.slope_ema1_t1 > 0,
				 self.slope_ema2_t1 > 0,
				 self.slope_ema_width_t1 > 0,
				 self.slope_ema_width_t2 > 0,
				 self.slope_t1 > 0,
				 self.slope_t2 > 0,
				 self.slope_of_slope_t1 > 0,
				 self.slope_of_slope_t2 > 0,
				 self.slope_obv_t1 > 0,
				 self.slope_obv_t2 > 0,
				 d.close[0] > self.boll_mid_t1,
				 d.close[0] > self.boll_mid_t2,
				 #self.percK_t0 < 30,
				 ]
		
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
		
		
	def regime_late_bull(self,d):
		#Late in trend, starting to top out - look to exit long position or initiate short position
		#Vix has -.43 correlation to SPY over last 5 years - use as indicator (Vix sloping down good for trend?)
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		self.rsi_t1 = self.inds.get(d._name[:-1]+'1').get('rsi')[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]
		self.rsi_2 = self.inds.get(d._name[:-1]+'2').get('rsi')[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 35,
				 self.adx_t2 > 35,
				 self.slope_adx_t1 < 0,
				 self.slope_adx_t2 < 0,
				 self.ema1_t1 > self.ema2_t1,
				 self.ema1_t2 > self.ema2_t2,
				 self.slope_ema1_t1 > 0,
				 self.slope_ema2_t1 > 0,
				 self.slope_ema_width_t1 < 0,
				 self.slope_ema_width_t2 < 0,
				 self.slope_t1 > 0,
				 self.slope_t2 > 0,
				 self.slope_of_slope_t1 < 0,
				 self.slope_of_slope_t2 < 0,
				 self.slope_obv_t1 < 0,
				 self.slope_obv_t2 < 0,
				 d.close[0] > self.boll_mid_t1,
				 d.close[0] > self.boll_mid_t2,
				 self.rsi_t1 < 70,
				 self.rsi_t2 < 70,
				 ]
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
	
	
	def mean_revert(self,d,direction):
		self.boll_top_t0 = self.inds.get(d._name[:-1]+'0').get('bollinger').lines.top[0]
		self.boll_bot_t0 = self.inds.get(d._name[:-1]+'0').get('bollinger').lines.bot[0]
		#self.boll_top_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.top[0]
		#self.boll_bot_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.bot[0]
		self.adx_t0 = self.inds.get(d._name).get('adx')[0]
		self.rsi_t0 = round(self.inds.get(d._name).get('rsi')[0],2)
		

	def regime_neutral(self,d):
		#Define Variables
		
		#Calculate timeframe 1
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.rsi_t1 = self.inds.get(d._name[:-1]+'1').get('rsi')[0]
		self.resistance_t1 = self.inds.get(d._name[:-1]+'1').get('resistance')[0]
		self.support_t1 = self.inds.get(d._name[:-1]+'1').get('support')[0]
		
		#Calculate timeframe 2
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.rsi_t2 = self.inds.get(d._name[:-1]+'2').get('rsi')[0]
		self.resistance_t2 = self.inds.get(d._name[:-1]+'2').get('resistance')[0]
		self.support_t2 = self.inds.get(d._name[:-1]+'2').get('support')[0]

		#Define signal criteria
		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 < 20,
				 self.adx_t2 < 20,
				 self.rsi_t1 < 70,
				 self.rsi_t1 > 30,
				 self.rsi_t2 < 70,
				 self.rsi_t2 > 30,
				 d.close[0] < self.resistance_t1,
				 d.close[0] > self.support_t1,
				 d.close[0] < self.resistance_t2,
				 d.close[0] > self.support_t2,
				 ]
				 
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
		
	
	def regime_early_bear(self,d):
		#Trend underway, getting stronger
		#Get timeframe 0 values
		self.percK_t0 = self.inds.get(d._name).get('stochastic').lines.percK[0]
		
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 20,
				 self.adx_t2 > 20,
				 self.slope_adx_t1 < 0,
				 self.slope_adx_t2 < 0,
				 self.ema1_t1 < self.ema2_t1,
				 self.ema1_t2 < self.ema2_t2,
				 self.slope_ema1_t1 < 0,
				 self.slope_ema2_t1 < 0,
				 self.slope_ema_width_t1 < 0,
				 self.slope_ema_width_t2 < 0,
				 self.slope_t1 < 0,
				 self.slope_t2 < 0,
				 self.slope_of_slope_t1 < 0,
				 self.slope_of_slope_t2 < 0,
				 self.slope_obv_t1 < 0,
				 self.slope_obv_t2 < 0,
				 d.close[0] < self.boll_mid_t1,
				 d.close[0] < self.boll_mid_t2,
				 #self.percK_t0 > 70,
				 ]
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
	
	
	def regime_late_bear(self,d):
		#Late in trend, starting to top out - look to exit short position or initiate long position
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		self.rsi_t1 = self.inds.get(d._name[:-1]+'1').get('rsi')[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]
		self.rsi_t2 = self.inds.get(d._name[:-1]+'2').get('rsi')[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 35,
				 self.adx_t2 > 35,
				 self.slope_adx_t1 < 0,
				 self.slope_adx_t2 < 0,
				 self.ema1_t1 < self.ema2_t1,
				 self.ema1_t2 < self.ema2_t2,
				 self.slope_ema1_t1 < 0,
				 self.slope_ema2_t1 < 0,
				 self.slope_ema_width_t1 > 0,
				 self.slope_ema_width_t2 > 0,
				 self.slope_t1 < 0,
				 self.slope_t2 < 0,
				 self.slope_of_slope_t1 > 0,
				 self.slope_of_slope_t2 > 0,
				 self.slope_obv_t1 > 0,
				 self.slope_obv_t2 > 0,
				 d.close[0] < self.boll_mid_t1,
				 d.close[0] < self.boll_mid_t2,
				 self.rsi_t1 < 30,
				 self.rsi_t2 < 30,
				 ]
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
	
	
	def rank_correl(self,d,df):
		"""Returns most highly correlated pairs of stocks, and correlation value, from ticker list via 2 key, 1 value dict"""
		mycorr = df.corr(method='pearson')
		np.fill_diagonal(mycorr.values, np.nan)  #replace 1's with NA's in correlations matrix
		spy_ranked = mycorr["SPY1"].sort_values(ascending=False).dropna() #get just SPY column in dataframe, then sort
		print(f'Top Positive Correlations to SPY: {spy_ranked.nlargest(self.p.rank)} Top Negative: {spy_ranked.nsmallest(self.p.rank)}')
		print(f'Return just ticker names of top SPY correlations: {spy_ranked.nlargest(self.p.rank).index}')	#returns ticker pair list of highest ranked correlations
		"""
		rank_all = mycorr.unstack().sort_values(kind="quicksort",ascending=False).dropna().drop_duplicates()	#returns all correlations, ranked hishest to lowest
		#print(rank_all)
		print(f'Top Positive Correlations: {rank_all.nlargest(3)} Top Negative: {rank_all.nsmallest(3)}')
		print(f'Return just ticker names of top correlations: {rank_all.nlargest(3).index}')	#returns ticker pair list of highest ranked correlations
		"""
		
			
	def sql_fund(self):
		#PULL FUNDAMENTALS SQL TABLE INTO A DICTIONARY
		#Define connection configuration
		startd = UserInputs.model_params().get("start_date")
		endd = UserInputs.model_params().get("end_date")

		host = '127.0.0.1'
		user = 'root'
		password = 'EptL@Rl!1'
		database = 'Stock_Prices'
		table = 'fundamentals'
		start_date = startd.strftime("%Y-%m-%d")
		end_date = endd.strftime("%Y-%m-%d")

		#Establish SQL connection
		engine = create_engine('mysql+pymysql://'+user+':'+ password +'@'+ host +'/'+ database +'?charset=utf8mb4', echo=False)
		conn = engine.connect()
		
		#Get data from SQL DB
		mytest = conn.execute(f"SELECT * FROM {table} where datetime >= '{start_date}' and datetime <= '{end_date}'")
		eps_set = mytest.fetchall()

		#Get dictionary from SQL results
		d, a = {}, []
		for rowproxy in eps_set:
			# rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
			for column, value in rowproxy.items():
				# build up the dictionary
				d = {**d, **{column: str(value)}}
			a.append(d)
		
		for i in a:
			self.eps_dict[f"{i['ticker']}"]['date'] = i['datetime']
			if i['eps_estimate'] != 'None':
				self.eps_dict[f"{i['ticker']}"]['eps_estimate'] = float(i['eps_estimate'])
			if i['eps_actual'] != 'None':
				self.eps_dict[f"{i['ticker']}"]['eps_actual'] = float(i['eps_actual'])
			if i['eps_diff'] != 'None':
				self.eps_dict[f"{i['ticker']}"]['eps_diff%'] = float(i['eps_diff'])

		#Close DB connection
		conn.close()
		engine.dispose()
		

	def grangers_causation_matrix(self,data, variables, test='ssr_chi2test', verbose=True):    
		"""Check Granger Causality of all possible combinations of the Time series.
		Y is the response variable, X are predictors. The values in the table 
		are the P-Values. P-Values lesser than the significance level (0.05), implies 
		the Null Hypothesis that the coefficients of the corresponding past values is 
		zero, that is, the X does not cause Y can be rejected.

		data      : pandas dataframe containing the time series variables
		variables : list containing names of the time series variables.
		
		Output Example:
		Y = SPY1, X = SPY1, P Values = [1.0, 1.0, 1.0, 1.0, 1.0]
		Y = XLU1, X = SPY1, P Values = [0.5009, 0.4085, 0.3347, 0.105, 0.006]
		Y = XHB1, X = SPY1, P Values = [0.7069, 0.7361, 0.304, 0.0065, 0.0063]
		
		if you look at row 2, it refers to the p-value of SPY1(X) causing XLU1(Y). 
		If a given p-value is < significance level (0.05), then, the corresponding X series causes the Y.
		Looking at the P-Values in the above table, you can pretty much observe that all the variables (time series) in the system are interchangeably causing each other.
		if most pvalues in output are less than significance level, then system good candidate for using Vector Auto Regression models to forecast. 
		"""
		
		df = pd.DataFrame(np.zeros((len(variables), len(variables))), columns=variables, index=variables)
		maxlag=len(variables)
		for c in df.columns:
			for r in df.index:
				test_result = ts.grangercausalitytests(data[[r, c]], maxlag=maxlag, verbose=False)
				p_values = [test_result[i+1][0][test][1] for i in range(maxlag)]
				if verbose: print(f'Y = {r}, X = {c}, P Values = {p_values}')
				min_p_value = np.min(p_values)
				df.loc[r, c] = min_p_value
		df.columns = [var + '_x' for var in variables]
		df.index = [var + '_y' for var in variables]
		return df
		#self.grangers_causation_matrix(self.df_closes, variables = self.df_closes.columns)


class IB_Scan():
	"""This Class requests market scanner data from Interactive Brokers and returns ticker list of scan results"""
	def __init__(self):
		self.gapup = []
		self.gapdown = []
		self.orderid = []
		self.gapup.clear()
		self.gapdown.clear()
		self.orderid.clear()
	
	def get_valid_order_id(self, msg):
		#Get next order id from IB 
		#print(f'Next Order ID: {msg.orderId}')  
		self.orderid.append(msg.orderId)
				
	def scan_results(self,msg):
		#print (f'Server Response: {msg.typeName}, {msg}')
		#Retrieve scanner results
		if msg.reqId == self.gappingup_id:
			self.gapup.append(msg.contractDetails.m_summary.m_symbol)
		else:
			self.gapdown.append(msg.contractDetails.m_summary.m_symbol)

	def error_handler(self,msg):
		"""Handles the capturing of error messages"""
		print (f'Server Error: {msg}')
	
	def run_prog(self):
		#Make connection to IB
		con = ibConnection(host='127.0.0.1', port=7497, clientId=100)
		con.connect()
			
		# Assign the error handling function defined above to the TWS connection
		con.register(self.error_handler, 'Error')

		# Assign all of the server reply messages to the reply_handler function defined above
		con.register(self.scan_results, message.scannerData)
		
		#Generage next order_id
		con.register(self.get_valid_order_id,'NextValidId')
		#con.reqIds(-1) 
		t.sleep(60)  #Allow for time to get order id from IB

		#Define scanner parameters
		self.gappingup_id = self.orderid[0]
		gappingup = ScannerSubscription()
		gappingup.numberOfRows(5)
		gappingup.m_scanCode = 'HIGH_OPEN_GAP'
		gappingup.m_instrument = 'STK'
		gappingup.m_abovePrice = '20'
		gappingup.m_aboveVolume = '1000000'

		self.gappingdown_id = self.gappingup_id + 1
		gappingdown = ScannerSubscription()
		gappingdown.numberOfRows(5)
		gappingdown.m_scanCode = 'LOW_OPEN_GAP'
		gappingdown.m_instrument = 'STK'
		gappingdown.m_abovePrice = '20'
		gappingdown.m_aboveVolume = '1000000'
				
		#Request subscription to scanner
		con.reqScannerSubscription(self.gappingup_id,gappingup)
		t.sleep(3)
		con.reqScannerSubscription(self.gappingdown_id,gappingdown)
		t.sleep(3)
		
		#Cancel scaneer subscription when finished
		con.cancelScannerSubscription(self.gappingup_id)
		con.cancelScannerSubscription(self.gappingdown_id)
		t.sleep(3)
		
		#Disconnect from IB when done
		con.disconnect()
		
		#Return ticker_list that meets scanner defined criteria
		ticker_list = self.gapup + self.gapdown
		print(f'Scan results: Gap Up{self.gapup} Gap Down{self.gapdown}')
		print(f'All scan results: {ticker_list}')
		print (f'IB Scan subscription DISCONNECTED')
		
		return ticker_list
				
#********************************************RUN STRATEGY FUNCTION*********************************************************************

def runstrat():	
	
	cerebro = bt.Cerebro(exactbars=-1) #Create an instance of cerebro.  exactbars True reduces memory usage significantly, but change to '-1' for partial memory savings (keeping indicators in memory) or 'false' to turn off completely if having trouble accessing bars beyond max indicator paramaters.  
	cerebro.broker.set_shortcash(False) #False means decrease cash available when you short, True means increase it
	cerebro.addstrategy(Strategy)	#Add our strategy to cerebro

	#Determine data and time range to run
	modelp = UserInputs.model_params()
	start_date = modelp.get('start_date')
	end_date = modelp.get('end_date')
	session_start = modelp.get('sessionstart')
	session_end = modelp.get('sessionend')	

	#Add analysis to cerebro
	add_analysis(cerebro) #get all the result analysis

	#Add data
	if modelp.get('live_status'):
		data_live(cerebro,session_start,session_end,modelp)
		results = cerebro.run(preload=False,
						stdstats=False, #enables some additional chart information like profit/loss, buy/sell, etc, but tends to clutter chart
						runonce=False)
	else:
		data_backtest(cerebro,start_date,end_date,session_start,session_end,modelp)
		results = cerebro.run(preload=True,
						stdstats=False, #enables some additional chart information like profit/loss, buy/sell, etc, but tends to clutter chart
						runonce=False)

	#Print analyzers from results			
	for n in results[0].analyzers:
		n.print()
	
	print(f'{start_date} to {end_date}')	
	print(f'ENDING ACCT VALUE: {round(cerebro.broker.getvalue(),2)}, ENDING CASH: {round(cerebro.broker.getcash(),2)}')
	
	
	"""
	#Access Results(strategy dictionaries, parameters, etc. after program runs)
	#print(dir(results[0]))  #returns list of all attributes and methods associated with results object
	for i,d in enumerate(results[0].datas):
		#print(d._name,results[0].sorted_dict)
		#print(d.open.array)
	"""
	#csv_output(cerebro)  #output to csv
	
	#print(cerebro.broker.getvalue(), cerebro.broker.getcash())  #getvalue gets your total account position at any time (includes changes when you are in a position, and also when you close positions)
	
	#Get number of timeframes so plot can iterate correctly
	datacount = modelp.get('t0_on') + modelp.get('t1_on') + modelp.get('t2_on')
	
	if modelp.get('plot')==True:
		#Plot data, timeframe 0 for each stock, one by one
		for i in range (0,len(results[0].datas),datacount):
			for j, d in enumerate(results[0].datas):
				d.plotinfo.plot = i ==j
			cerebro.plot(barup='olive', bardown='lightpink',volume=True)

#************************************************************************************************************************************			

def data_live(cerebro,session_start,session_end,modelp):
	
	print(f'Subscribing to IB Market Scanner - determining stocks to trade')
	ib = IB_Scan()  #Create object "IB" from IB_Scan class	
	ibdatalist = ib.run_prog()  #get ticker list
	
	#Ensure stock lists have no duplicates - duplicates will BREAK program
	if len(ibdatalist) != len(set(ibdatalist)):
		print("*****You have duplicates in stock list - FIX LIST*****")
	
	#Determine configuration to connect to Interactive Brokers
	store = bt.stores.IBStore(host='127.0.0.1',
							port=7497,
							clientId = 100,
							indcash = True)

	for i,j in enumerate(ibdatalist):
		#Data for live IB trading
		
		data = store.getdata(dataname=j,
							sectype='STK',
							exchange='SMART',
							currency='USD',
							timeframe=bt.TimeFrame.Minutes,
							tz = pytz.timezone('US/Central'),
							sessionstart = session_start,
							sessionend = session_end,
							debug = False,
							useRTH = True,
							)


		if modelp.get('t0_on'):												
			cerebro.resampledata(data, name="{}0".format(j),timeframe=bt.TimeFrame.Minutes, compression=modelp.get('timeframe0'))

		#Apply resamplings
		if modelp.get('t1_on'):
			data_Timeframe1 = cerebro.resampledata(data,name="{}1".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe1'))
		
		if modelp.get('t2_on'):
			data_Timeframe2 = cerebro.resampledata(data,name="{}2".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe2'))
						
		
	#*****************************************************************************************************											
	cerebro.broker = store.getbroker()  #Critical line of code to access broker so you can trade
	#*****************************************************************************************************


def data_backtest(cerebro,start_date,end_date,session_start,session_end,modelp):

	datalist = UserInputs.datalist('hist')
	if len(datalist) != len(set(datalist)):
		print("*****You have duplicates in stock list - FIX LIST*****")
	
	#define mysql configuration items for connection
	host = '127.0.0.1'
	user = 'root'
	password = 'EptL@Rl!1'
	database = 'Stock_Prices'
	table = '5_min_prices'
	
	for i,j in enumerate(datalist):
		#Get data from mysql and add data to Cerebro
		data = mysql.MySQLData(dbHost = host,
								dbUser = user,
								dbPWD = password,
								dbName = database,
								table = table,
								symbol = j,  
								fromdate = start_date,
								todate= end_date,
								sessionstart = session_start,
								sessionend = session_end,
								compression = modelp.get('timeframe0'),
								)
		if modelp.get('t0_on'):	
			cerebro.adddata(data, name="{}0".format(j))

		if modelp.get('t1_on'):
			#Apply resamplings			
			data_Timeframe1 = cerebro.resampledata(data,
									name="{}1".format(j),
									timeframe=bt.TimeFrame.Minutes,
									compression = modelp.get('timeframe1'),
									)

		if modelp.get('t2_on'):
			data_Timeframe2 = cerebro.resampledata(data,
									name="{}2".format(j),
									timeframe=bt.TimeFrame.Minutes,
									compression = modelp.get('timeframe2'),
									)

	# Set our desired cash start
	cerebro.broker.setcash(modelp.get('start_cash'))
	
	# Set the commission.  IB charges $.005 per share
	cerebro.broker.setcommission(commission=.005,
								commtype=bt.CommInfoBase.COMM_FIXED,
								stocklike=True)
	
	"""
	#Set the slippage
	cerebro.broker.set_slippage_perc(0.001,
									slip_open=True, 
									slip_limit=True,
									slip_match=True,
									slip_out=False)
	"""
	
def add_analysis(cerebro):
	
	#cerebro.addanalyzer(bt.analyzers.SharpeRatio)
	#cerebro.addanalyzer(bt.analyzers.AcctStats)  #report trade statistics in command window at end of program run
	#cerebro.addanalyzer(bt.analyzers.DrawDown)
	# Add TradeAnalyzer to output trade statistics - THESE ARE THE TRADE NOTIFICATIONS THAT ARE PRINTED WHEN PROGRAM IS RUN
	cerebro.addanalyzer(bt.analyzers.Transactions)
	cerebro.addobservermulti(bt.observers.BuySell)
	cerebro.addobserver(bt.observers.AcctValue) #reports account value in graph at top
	cerebro.addanalyzer(bt.analyzers.BasicTradeStats)
	# Add SQN to qualify the trades (rating to analyze quality of trading system: 2.5-3 good, above 3 excellent.  SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit).  Need at least 30 trades to be reliable
	cerebro.addanalyzer(bt.analyzers.SQN)
	#cerebro.addobserver(bt.observers.OrderObserver) #reports trades in output window when program is run
	#cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')  #Can see account balances throughout strategy execution
	

def csv_output(cerebro):
	#Generate output report in csv format
	if UserInputs.model_params().get('writer')=='on':
		current_time = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.csv") 
		csv_file = 'C:/Program Files/Python38/Lib/site-packages/backtrader/out/'
		csv_file += 'Strategy'
		csv_file += current_time
		cerebro.addwriter(bt.WriterFile, csv = True, out=csv_file)
		print("Writer CSV Report On and report generated")
		

def open_IB():
	"""Automatically Opens TWS IB application and logs in"""
	dt = datetime.now()
	current_time = time(datetime.now().hour,datetime.now().minute)
	target_time = time(UserInputs.model_params().get('ib_open_time').hour,UserInputs.model_params().get('ib_open_time').minute)
	hourmin = time(target_time.hour,target_time.minute)
	
	#while current_time < hourmin:
	while current_time < hourmin or (current_time > time(15,0) and current_time <= time(23,59,59)):
		current_time = time(datetime.now().hour,datetime.now().minute,datetime.now().second)
		print(f'{current_time} - Waiting to open Interactive Brokers @ {target_time}')
		t.sleep(60)  #Wait 1 minute after open to allow prices to populate
	
	subprocess.Popen('C:\\Jts\\tws.exe')

	#Wait for App to open
	t.sleep(30)  #Allow for installation updates upon open if necessary
	pyautogui.typewrite('esond9648')
	pyautogui.press('tab')
	pyautogui.write('Ep2LatRl1Interactive')
	pyautogui.press('enter')
	t.sleep(30)  #Allow for application to open after login
	pyautogui.press('enter')
	print(f'IB Open Complete - IB Now Available')


def profile():
	#Profiles code to see where time bottlenecks are
	import cProfile
	import pstats
	import io
	
	pr = cProfile.Profile()
	pr.enable()

	my_result = runstrat()

	pr.disable()
	s = io.StringIO()
	ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
	ps.print_stats()

	with open('C:\\Users\\Erik\\Desktop\\profile.txt', 'w+') as f:
		f.write(s.getvalue())


#**********************************************RUN ENTIRE PROGRAM**********************************************************************						
if __name__ == '__main__':
	if UserInputs.model_params().get('live_status'):
		#Import modules for live trading
		import pytz
		import time as t
		import subprocess  	#to open/login to interactive brokers
		import pyautogui	#to open/login to interactive brokers
		import threading    #to open/login to interactive brokers
		from backtrader.utils import flushfile  # win32 quick stdout flushing
		from ib.ext.Contract import Contract
		from ib.opt import ibConnection, message
		from ib.ext.ScannerSubscription import ScannerSubscription
		
		#Auto Open IB TWS Application
		thread = threading.Thread(target=open_IB)
		thread.start()  #start thread (rest of program remains idle until thread complete)
		thread.join()#wait here for the result to be available before continuing
		
		#Run strategy
		runstrat()
	else:
		#Run strategy
		profile()
		#runstrat()

"""
Guid to Trade Statistics outputted:

Win Factor = number of wins / number of losses. e.g. 106 / 17 = 6.235
Profit Factor = total profit from wins / total profit from losses
Reward : Risk - also called Risk Reward Ratio = average win / average loss
Expectancy % - this is the expectancy from system. e.g. for every unit risked what % can you expect to make. e.g. 28.7% means for every $1 you risked, your return was 28.7 cents.
[Technically the risk was not known, but we can estimate it from the losses. The more trades the more representative this figure will be.]
Kelly % - the optimal percentage (in hindsight) to have risked on your system per trade -> to make the maximum amount of profit.
Z-Score - If system has a significant Z score (less than -2, greater than 2) then it is potentially possible to exploit the system for extra profit.
        A negative Z score means that there are fewer streaks in the trading
        system than would be expected statistically. This means that winning
        trades tend to follow winning trades and that losing trades tend to
        follower losers.

        A positive Z score means that there are more streaks in the trading
        system than would be expected. This means that winners tend to follow
        losers and vice versa."""
