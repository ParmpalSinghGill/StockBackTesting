import pandas as pd
import numpy as np

def detect_trend(stock_data, min_days=5, max_reversal_pct=0.02):
	"""
	Detect trends in stock data.

	Parameters:
	stock_data (pd.DataFrame): A DataFrame with 'Close' prices and 'Date' as index.
	min_days (int): Minimum number of days for a trend.
	max_reversal_pct (float): Maximum percentage change allowed for small reversals.

	Returns:
	list: A list of trends detected with each entry as a dictionary containing:
		  'start_date', 'end_date', and 'trend' (UP or DOWN).
	"""

	trends = []
	trend_start = None
	trend_direction = None
	last_close = stock_data['Close'].iloc[0]

	reversal_count = 0

	for i in range(1, len(stock_data)):
		current_close = stock_data['Close'].iloc[i]
		pct_change = (current_close - last_close) / last_close

		# Check if we need to initialize a new trend
		if trend_direction is None:
			trend_direction = 'UP' if current_close > last_close else 'DOWN'
			trend_start = stock_data.index[i - 1]

		# Check if the current day's movement is within reversal limits
		if trend_direction == 'UP':
			if current_close < last_close:
				reversal_count += 1
				if reversal_count > 2 or pct_change < -max_reversal_pct:
					# Break trend if reversal is too large
					if i - stock_data.index.get_loc(trend_start) >= min_days:
						trends.append({
							'start_date': trend_start,
							'end_date': stock_data.index[i - 1],
							'trend': 'UP'
						})
					trend_direction = 'DOWN'
					trend_start = stock_data.index[i - 1]
					reversal_count = 0
			else:
				reversal_count = 0  # reset reversal count when trend resumes
		elif trend_direction == 'DOWN':
			if current_close > last_close:
				reversal_count += 1
				if reversal_count > 2 or pct_change > max_reversal_pct:
					if i - stock_data.index.get_loc(trend_start) >= min_days:
						trends.append({
							'start_date': trend_start,
							'end_date': stock_data.index[i - 1],
							'trend': 'DOWN'
						})
					trend_direction = 'UP'
					trend_start = stock_data.index[i - 1]
					reversal_count = 0
			else:
				reversal_count = 0

		last_close = current_close

	# Capture the final trend
	if trend_start and i - stock_data.index.get_loc(trend_start) >= min_days:
		trends.append({
			'start_date': trend_start,
			'end_date': stock_data.index[-1],
			'trend': trend_direction
		})

	return trends


def calculate_indicators(stock_data, short_window=20, long_window=50, atr_window=14, adx_window=14):
	"""
	Add technical indicators to the stock data:
	- Moving Averages (SMA)
	- ATR (Average True Range)
	- ADX (Average Directional Index)
	- Bollinger Bands

	Parameters:
	stock_data (pd.DataFrame): DataFrame with 'Close', 'High', and 'Low' prices.
	short_window (int): Window for the short moving average.
	long_window (int): Window for the long moving average.
	atr_window (int): Window for calculating ATR.
	adx_window (int): Window for calculating ADX.

	Returns:
	pd.DataFrame: Stock data with added technical indicators.
	"""

	stock_data['SMA_short'] = stock_data['Close'].rolling(window=short_window).mean()
	stock_data['SMA_long']  = stock_data['Close'].rolling(window=long_window).mean()

	# ATR Calculation
	stock_data['TR'] = np.maximum(stock_data['High'] - stock_data['Low'],
	                              np.maximum(abs(stock_data['High'] - stock_data['Close'].shift(1)),
	                                         abs(stock_data['Low'] - stock_data['Close'].shift(1))))
	stock_data['ATR'] = stock_data['TR'].rolling(window=atr_window).mean()

	# Bollinger Bands
	stock_data['SMA_20'] = stock_data['Close'].rolling(window=20).mean()
	stock_data['BB_upper'] = stock_data['SMA_20'] + 2 * stock_data['Close'].rolling(window=20).std()
	stock_data['BB_lower'] = stock_data['SMA_20'] - 2 * stock_data['Close'].rolling(window=20).std()

	# ADX Calculation
	plus_dm = stock_data['High'].diff()
	minus_dm = stock_data['Low'].diff()
	plus_dm[plus_dm < 0] = 0
	minus_dm[minus_dm > 0] = 0

	stock_data['+DI'] = 100 * (plus_dm.ewm(span=adx_window).mean() / stock_data['ATR'])
	stock_data['-DI'] = 100 * (abs(minus_dm).ewm(span=adx_window).mean() / stock_data['ATR'])

	dx = (abs(stock_data['+DI'] - stock_data['-DI']) / abs(stock_data['+DI'] + stock_data['-DI'])) * 100
	stock_data['ADX'] = dx.ewm(span=adx_window).mean()

	return stock_data


def detect_trend_with_indicators(stock_data, min_days=5, max_reversal_pct=0.02, adx_threshold=20):
	"""
	Detect trends based on indicators.

	Parameters:
	stock_data (pd.DataFrame): A DataFrame with 'Close', 'High', 'Low' prices and technical indicators.
	min_days (int): Minimum number of days for a trend.
	max_reversal_pct (float): Maximum percentage change allowed for small reversals.
	adx_threshold (int): Threshold for ADX to confirm a strong trend.

	Returns:
	list: A list of detected trends.
	"""

	trends = []
	trend_start = None
	trend_direction = None
	reversal_count = 0
	last_close = stock_data['Close'].iloc[0]

	for i in range(1, len(stock_data)):
		current_close = stock_data['Close'].iloc[i]
		pct_change = (current_close - last_close) / last_close
		adx = stock_data['ADX'].iloc[i]

		# Check if there's a strong trend based on ADX
		if adx < adx_threshold:
			last_close = current_close
			continue

		# Check for initial trend based on moving averages
		if trend_direction is None:
			if stock_data['SMA_short'].iloc[i] > stock_data['SMA_long'].iloc[i]:
				trend_direction = 'UP'
			elif stock_data['SMA_short'].iloc[i] < stock_data['SMA_long'].iloc[i]:
				trend_direction = 'DOWN'
			trend_start = stock_data.index[i - 1]

		# Handle trend continuation or reversal
		if trend_direction == 'UP':
			if current_close < last_close and pct_change < -max_reversal_pct * stock_data['ATR'].iloc[i]:
				# Handle reversal
				reversal_count += 1
				if reversal_count > 2:
					if i - stock_data.index.get_loc(trend_start) >= min_days:
						trends.append({
							'start_date': trend_start,
							'end_date': stock_data.index[i - 1],
							'trend': 'UP'
						})
					trend_direction = 'DOWN'
					trend_start = stock_data.index[i - 1]
					reversal_count = 0
			else:
				reversal_count = 0
		elif trend_direction == 'DOWN':
			if current_close > last_close and pct_change > max_reversal_pct * stock_data['ATR'].iloc[i]:
				# Handle reversal
				reversal_count += 1
				if reversal_count > 2:
					if i - stock_data.index.get_loc(trend_start) >= min_days:
						trends.append({
							'start_date': trend_start,
							'end_date': stock_data.index[i - 1],
							'trend': 'DOWN'
						})
					trend_direction = 'UP'
					trend_start = stock_data.index[i - 1]
					reversal_count = 0
			else:
				reversal_count = 0

		last_close = current_close

	# Capture the final trend
	if trend_start and i - stock_data.index.get_loc(trend_start) >= min_days:
		trends.append({
			'start_date': trend_start,
			'end_date': stock_data.index[-1],
			'trend': trend_direction
		})

	return trends

def FindMyTrend(stock_data, min_days=5, max_reversal_pct=0.02,n=10, lastNDays=2):
	# detected_trends = detect_trend(stock_data[-2*n:], min_days=min_days, max_reversal_pct=max_reversal_pct)
	stock_data = calculate_indicators(stock_data)
	print(stock_data.columns)
	detected_trends=detect_trend_with_indicators(stock_data[-2*n:], min_days=5, max_reversal_pct=0.02, adx_threshold=20)
	lastNthdate=stock_data.index[-lastNDays]
	for trend in detected_trends:
		if trend["start_date"]<lastNthdate and lastNthdate<=trend["end_date"]:
			# print(type(trend["start_date"]))
			# print(type(stock_data.index))
			absdiff=abs(stock_data.loc[trend["start_date"]]["Close"]-stock_data.loc[trend["end_date"]]["Close"])/stock_data.loc[trend["start_date"]]["Close"]*100
			if absdiff>5:
				return trend["trend"],trend["start_date"],trend["end_date"]
	return None,None,None

# Example usage
if __name__ == "__main__":
	# Create example stock data
	data = {
		'Close': [100, 102, 101, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 96, 97, 99, 101, 103, 102, 101, 104, 106,
		          105, 104, 106, 108, 109, 110, 112, 113],
		'High': [101, 103, 102, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 97, 98, 100, 102, 104, 103, 102, 105, 107,
		         106, 105, 107, 109, 110, 111, 113, 114],
		'Low': [99, 101, 100, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 95, 96, 98, 100, 102, 101, 100, 103, 105, 104,
		        103, 105, 107, 108, 109, 111, 112]
	}

	stock_data = pd.DataFrame(data,index=pd.date_range(start='2023-01-01', periods=30))

	# # Detect trends
	# detected_trends = detect_trend(stock_data, min_days=5, max_reversal_pct=0.02)
	#
	# for trend in detected_trends:
	# 	print(trend)
	print(FindMyTrend(stock_data))
