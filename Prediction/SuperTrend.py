import ccxt
import warnings
from matplotlib.pyplot import fill_between
import pandas as pd
import numpy as np
import pandas_ta as ta
import mplfinance as mpf
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')


def generate_signals(df):
	# Intiate a signals list
	signals = [0]

	# Loop through the dataframe
	for i in range(1, len(df)):
		if df['Close'][i] > df['upperband'][i]:
			signals.append(1)
		elif df['Close'][i] < df['lowerband'][i]:
			signals.append(-1)
		else:
			# signals.append(signals[-1])
			signals.append(signals[-1])

	# Add the signals list as a new column in the dataframe
	df['signals'] = signals
	# df['signals'] = df["signals"].shift(1)  # Remove look ahead bias
	return df

def create_positions(df):
	# We need to shut off (np.nan) data points in the upperband where the signal is not 1
	df['upperband'][df['signals'] == 1] = np.nan
	# We need to shut off (np.nan) data points in the lowerband where the signal is not -1
	df['lowerband'][df['signals'] == -1] = np.nan

	# Create a positions list
	buy_positions = [np.nan]
	sell_positions = [np.nan]
	signals=[0]

	# Loop through the dataframe
	for i in range(1, len(df)):
		# If the current signal is a 1 (Buy) & the it's not equal to the previous signal
		# Then that is a trend reversal, so we BUY at that current market price
		# We take note of the upperband value
		if df['signals'][i] == 1 and df['signals'][i] != df['signals'][i - 1]:
			buy_positions.append(df['Close'][i])
			sell_positions.append(np.nan)
			signals.append(1)
		# If the current signal is a -1 (Sell) & the it's not equal to the previous signal
		# Then that is a trend reversal, so we SELL at that current market price
		elif df['signals'][i] == -1 and df['signals'][i] != df['signals'][i - 1]:
			sell_positions.append(df['Close'][i])
			buy_positions.append(np.nan)
			signals.append(-1)
		else:
			buy_positions.append(np.nan)
			sell_positions.append(np.nan)
			signals.append(0)

	# Add the positions list as a new column in the dataframe
	df['buy_positions'] = buy_positions
	df['sell_positions'] = sell_positions
	df["SIGNAL"]=signals # Final Signal 1 for by -1 for Sell and 0 for nothing
	return df


def supertrend(df, atr_multiplier=3,nrows=100):
	# Calculate the Upper Band(UB) and the Lower Band(LB)
	# Formular: Supertrend =(High+Low)/2 + (Multiplier)∗(ATR)
	df=df[-nrows:]
	current_average_high_low = (df['High'] + df['Low']) / 2
	df['atr'] = ta.atr(df['High'], df['Low'], df['Close'], period=10)
	df.dropna(inplace=True)
	df['basicUpperband'] = current_average_high_low + (atr_multiplier * df['atr'])
	df['basicLowerband'] = current_average_high_low - (atr_multiplier * df['atr'])
	first_upperBand_value = df['basicUpperband'].iloc[0]
	first_lowerBand_value = df['basicLowerband'].iloc[0]
	upperBand = [first_upperBand_value]
	lowerBand = [first_lowerBand_value]

	for i in range(1, len(df)):
		if df['basicUpperband'].iloc[i] < upperBand[i - 1] or df['Close'].iloc[i - 1] > upperBand[i - 1]:
			upperBand.append(df['basicUpperband'].iloc[i])
		else:
			upperBand.append(upperBand[i - 1])

		if df['basicLowerband'].iloc[i] > lowerBand[i - 1] or df['Close'].iloc[i - 1] < lowerBand[i - 1]:
			lowerBand.append(df['basicLowerband'].iloc[i])
		else:
			lowerBand.append(lowerBand[i - 1])

	df['upperband'] = upperBand
	df['lowerband'] = lowerBand
	df.drop(['basicUpperband', 'basicLowerband', ], axis=1, inplace=True)
	df = generate_signals(df)
	df = create_positions(df)
	return df

def SuperTrendPrediction(df):
	trenddf=supertrend(df, atr_multiplier=3)
	lastrow=trenddf.iloc[-1]
	if lastrow["SIGNAL"]==1:
		return True,"BUY"
	elif lastrow["SIGNAL"]==-1:
		return True,"SELL"
	else:
		return False,None

