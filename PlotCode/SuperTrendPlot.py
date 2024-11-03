import datetime
import os

import warnings
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from Prediction.SuperTrend import supertrend

warnings.filterwarnings('ignore')
os.chdir("../")


def fetch_asset_data(symbol, start_date, interval, exchange):
	# Convert start_date to milliseconds timestamp
	start_date_ms = exchange.parse8601(start_date)
	ohlcv = exchange.fetch_ohlcv(symbol, interval, since=start_date_ms)
	header = ["date", 'Open', "High", 'Low', 'Close', "Volume"]
	df = pd.DataFrame(ohlcv, columns=header)
	df['date'] = pd.to_datetime(df['date'], unit='ms')
	df.set_index("date", inplace=True)
	# Drop the last row containing live data
	df.drop(df.index[-1], inplace=True)
	return df


def plot_data(df, symbol):
	# Define lowerband line plot
	lowerband_line = mpf.make_addplot(df['lowerband'], label="lowerband", color='green')
	# Define upperband line plot
	upperband_line = mpf.make_addplot(df['upperband'], label="upperband", color='red')
	# Define buy and sell markers
	buy_position_makers = mpf.make_addplot(df['buy_positions'], type='scatter', marker='^', label="Buy", markersize=50,
	                                       color='#2cf651')
	sell_position_makers = mpf.make_addplot(df['sell_positions'], type='scatter', marker='v', label="Sell",
	                                        markersize=50, color='#f50100')
	# A list of all addplots(apd)
	apd = [lowerband_line, upperband_line, buy_position_makers, sell_position_makers]
	# Create fill plots
	lowerband_fill = dict(y1=df['Close'].values, y2=df['lowerband'].values, panel=0, alpha=0.3, color="#CCFFCC")
	upperband_fill = dict(y1=df['Close'].values, y2=df['upperband'].values, panel=0, alpha=0.3, color="#FFCCCC")
	fills = [lowerband_fill, upperband_fill]
	# Plot the data
	mpf.plot(df, addplot=apd, type='candle', volume=True, style='charles', xrotation=20,
	         title=str(symbol + ' Supertrend Plot'), fill_between=fills)


def strategy_performance(strategy_df, capital=100, leverage=1):
	# Initialize the performance variables
	cumulative_balance = capital
	investment = capital
	pl = 0
	max_drawdown = 0
	max_drawdown_percentage = 0

	# Lists to store intermediate values for calculating metrics
	balance_list = [capital]
	pnl_list = [0]
	investment_list = [capital]
	peak_balance = capital

	# Loop from the second row (index 1) of the DataFrame
	for index in range(1, len(strategy_df)):
		row = strategy_df.iloc[index]

		# Calculate P/L for each trade signal
		if row['signals'] == 1:
			pl = ((row['Close'] - row['Open']) / row['Open']) * \
			     investment * leverage
		elif row['signals'] == -1:
			pl = ((row['Open'] - row['Close']) / row['Close']) * \
			     investment * leverage
		else:
			pl = 0

		# Update the investment if there is a signal reversal
		if row['signals'] != strategy_df.iloc[index - 1]['signals']:
			investment = cumulative_balance

		# Calculate the new balance based on P/L and leverage
		cumulative_balance += pl

		# Update the investment list
		investment_list.append(investment)

		# Calculate the cumulative balance and add it to the DataFrame
		balance_list.append(cumulative_balance)

		# Calculate the overall P/L and add it to the DataFrame
		pnl_list.append(pl)

		# Calculate max drawdown
		drawdown = cumulative_balance - peak_balance
		if drawdown < max_drawdown:
			max_drawdown = drawdown
			max_drawdown_percentage = (max_drawdown / peak_balance) * 100

		# Update the peak balance
		if cumulative_balance > peak_balance:
			peak_balance = cumulative_balance

	# Add new columns to the DataFrame
	strategy_df['investment'] = investment_list
	strategy_df['cumulative_balance'] = balance_list
	strategy_df['pl'] = pnl_list
	strategy_df['cumPL'] = strategy_df['pl'].cumsum()

	# Calculate other performance metrics (replace with your calculations)
	overall_pl_percentage = (
			                        strategy_df['cumulative_balance'].iloc[-1] - capital) * 100 / capital
	overall_pl = strategy_df['cumulative_balance'].iloc[-1] - capital
	min_balance = min(strategy_df['cumulative_balance'])
	max_balance = max(strategy_df['cumulative_balance'])

	# Print the performance metrics
	print("Overall P/L: {:.2f}%".format(overall_pl_percentage))
	print("Overall P/L: {:.2f}".format(overall_pl))
	print("Min balance: {:.2f}".format(min_balance))
	print("Max balance: {:.2f}".format(max_balance))
	print("Maximum Drawdown: {:.2f}".format(max_drawdown))
	print("Maximum Drawdown %: {:.2f}%".format(max_drawdown_percentage))

	# Return the Strategy DataFrame
	return strategy_df


# Plot the performance curve
def plot_performance_curve(strategy_df):
	plt.plot(strategy_df['cumulative_balance'], label='Strategy')
	plt.title('Performance Curve')
	plt.xlabel('Date')
	plt.ylabel('Balance')
	plt.xticks(rotation=70)
	plt.legend()
	plt.show()

from DataProcessing.DataLoad import getData
def OneCall():
	# Initialize data fetch parameters
	df = getData("HDFCBANK")[:-7]
	print(df.columns)

	volatility = 3

	# Apply supertrend formula
	supertrend_positions = supertrend(df=df, atr_multiplier=volatility)

	# # Calculate performance
	# supertrend_df = strategy_performance(supertrend_positions, capital=100, leverage=1)
	# print(supertrend_df)

	# Plot data
	plot_data(supertrend_positions[-100:], symbol="HDFCBANK")

	# # Plot the performance curve
	# plot_performance_curve(supertrend_df)

def BackTesting(symbol="HDFCBANK",datestart="2024-03-20",volatility=3):
	startdate=datetime.datetime.strptime(datestart,"%Y-%m-%d")
	df = getData(symbol)[startdate:]
	position_list=[]
	for index in range(30, df.shape[0]):
		pastdf=df[:index+1]
		supertrenddf = supertrend(df=pastdf, atr_multiplier=volatility)
		position_list.append(supertrenddf[-1:])
	trenddf=pd.concat(position_list)
	plot_data(trenddf, symbol=symbol)


if __name__ == '__main__':
	BackTesting()
