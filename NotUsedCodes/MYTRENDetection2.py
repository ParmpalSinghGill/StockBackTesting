import datetime
import os

import pandas as pd
import numpy as np
import yfinance as yf


from Prediction.Startegy import getData


# Load stock data (e.g., using Yahoo Finance)

def findTrend(data,MinDays=10):
	# Calculate Moving Averages
	short_window = 20  # Short-term window
	long_window = 50   # Long-term window
	data['SMA20'] = data['Close'].rolling(window=short_window).mean()
	data['SMA50'] = data['Close'].rolling(window=long_window).mean()

	# Calculate MACD
	data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
	data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
	data['MACD'] = data['EMA12'] - data['EMA26']
	data['Signal Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

	# Calculate RSI
	delta = data['Close'].diff(1)
	gain = delta.where(delta > 0, 0)
	loss = -delta.where(delta < 0, 0)
	average_gain = gain.rolling(window=14).mean()
	average_loss = loss.rolling(window=14).mean()
	rs = average_gain / average_loss
	data['RSI'] = 100 - (100 / (1 + rs))

	# Trend Detection Logic
	trends = []
	current_trend = None
	start_date = None

	for i in range(1, len(data)):
		# Trend detection conditions
		sma_condition = data['SMA20'][i] > data['SMA50'][i]
		macd_condition = data['MACD'][i] > data['Signal Line'][i]
		rsi_condition = data['RSI'][i] < 30  # Oversold condition for uptrend
		down_rsi_condition = data['RSI'][i] > 70  # Overbought condition for downtrend

		# Determine trend
		if sma_condition and macd_condition and data['RSI'][i] < 70:
			trend = 'UP'
		elif not sma_condition and not macd_condition and data['RSI'][i] > 30:
			trend = 'DOWN'
		else:
			trend = 'SIDEWAYS'

		# Record start and end of trend
		if trend != current_trend:
			if current_trend:
				if data.index[i-1]-start_date>datetime.timedelta(days=MinDays):
					trends.append({
						'Trend': current_trend,
						'Start Date': start_date,
						'End Date': data.index[i-1]
					})
			current_trend = trend
			start_date = data.index[i]

	# Add the last trend
	if current_trend:
		trends.append({
	        'Trend': current_trend,
	        'Start Date': start_date,
	        'End Date': data.index[-1]
		})
	return pd.DataFrame(trends)


def findTrend2(data,minTrendDays=30):
	# Calculate Moving Averages
	data['SMA20'] = data['Close'].rolling(window=20).mean()
	data['SMA50'] = data['Close'].rolling(window=50).mean()

	# Parameters
	interval = 5  # Interval of days to check consistency of trend
	min_periods = 5  # Minimum number of intervals to confirm trend

	# Initialize variables
	trend = None
	start_date = None
	trend_duration = 0

	# Check for consistent trend in the latest data
	for i in range(len(data) - interval, -1, -interval):
		sma_20 = data['SMA20'][i]
		sma_50 = data['SMA50'][i]

		# Uptrend condition: SMA20 consistently above SMA50
		if sma_20 > sma_50:
			if trend == "UP" or trend is None:
				trend = "UP"
				if start_date is None:
					start_date = data.index[i]
				trend_duration += interval
			else:
				# If trend changed, stop counting
				break

		# Downtrend condition: SMA20 consistently below SMA50
		elif sma_20 < sma_50:
			if trend == "DOWN" or trend is None:
				trend = "DOWN"
				if start_date is None:
					start_date = data.index[i]
				trend_duration += interval
			else:
				# If trend changed, stop counting
				break
		else:
			# If SMA20 crosses SMA50 at any interval, trend is broken
			trend = None
			trend_duration = 0
			start_date = None
			break
	if trend_duration>minTrendDays:
		print(trend_duration)
		return trend,start_date,data.index[-1]
	return None,None,None


def PlotTrend(df,key,n=100):
	for i in range(n,len(df)):
		pastdata=df[:i]
		trend,startdate,enddate=findTrend2(pastdata)
		if trend:
			print(startdate,enddate)
			PlotChart(pastdata[:],Trend=f"{key} {trend}",TrendBox=(startdate,enddate))


os.chdir("../")
from PlotCode.PlotCandles import PlotChart
	# Convert trends to DataFrame
if __name__ == '__main__':
	key="HDFCBANK"
	df=getData("HDFCBANK")
	PlotTrend(df,key)
	# for i,row in findTrend(df).iterrows():
	# 	if row["Trend"]=="UP" or row["Trend"]=="DOWN":
	# 		partdf=df[row["Start Date"]-datetime.timedelta(days=50):row["End Date"]]
	# 		PlotChart(partdf,Trend=f"{key} {row['Trend']}",TrendBox=(row["Start Date"],row["End Date"]))
