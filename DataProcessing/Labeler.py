import pandas as pd
import numpy as np

# Sample data creation for demonstration purposes
# Suppose df has columns: Date, Stock, Close, Benchmark_Close, Event_Flag
# Event_Flag is 1 if an event occurred on that day for the stock, else 0.
Benchmark_Close="Nifty_Close"
dates = pd.date_range(start='2023-01-01', periods=100)
stocks = ['A', 'B', 'C']
np.random.seed(42)
data = []
for stock in stocks:
	price = 100 + np.cumsum(np.random.randn(len(dates)))
	benchmark = 100 + np.cumsum(np.random.randn(len(dates)))
	# Random events with 5% probability
	events = np.random.choice([0, 1], size=len(dates), p=[0.95, 0.05])
	for d, p, b, e in zip(dates, price, benchmark, events):
		data.append({'Date': d, 'Stock': stock, 'Close': p, Benchmark_Close: b, 'Event_Flag': e})
df = pd.DataFrame(data)

# Sort data for future returns calculation
df = df.sort_values(by=['Stock', 'Date']).reset_index(drop=True)


# Function to calculate future returns over a window (forward return)
def add_future_return(df, window=5):
	df = df.copy()
	df['Future_Close'] = df.groupby('Stock')['Close'].shift(-window)
	# Calculate forward return (percentage change over the window)
	df['Future_Return'] = (df['Future_Close'] / df['Close']) - 1
	return df


# Adding the future returns column (using a 5-day forward window as an example)
window = 5
df = add_future_return(df, window)


# 1. Combined Fixed Threshold & Relative Performance Labeling
def label_combined(df, fixed_threshold=0.03, relative_margin=0.02):
	"""
	Labels a day as 1 if:
	  - Future return >= fixed_threshold, and
	  - Future return exceeds the benchmark's return (calculated similarly) by relative_margin.
	"""
	df = df.copy()
	# Calculate benchmark future return (assuming benchmark available per stock or overall)
	df['Benchmark_Future_Close'] = df.groupby('Stock')[Benchmark_Close].shift(-window)
	df['Benchmark_Future_Return'] = (df['Benchmark_Future_Close'] / df[Benchmark_Close]) - 1

	# Label if stock's future return exceeds both fixed threshold and benchmark + margin.
	conditions = (df['Future_Return'] >= fixed_threshold) & \
				 (df['Future_Return'] >= df['Benchmark_Future_Return'] + relative_margin)
	df['Label_Combined'] = np.where(conditions, 1, 0)
	return df


df = label_combined(df)


# 2. Quantile-Based Labeling
def label_quantile(df, quantile=0.8):
	"""
	Labels a day as 1 if the stock's future return is in the top quantile among all stocks on that day.
	"""
	df = df.copy()

	# For each day, compute the quantile cutoff for Future_Return.
	def quantile_label(group):
		threshold = group['Future_Return'].quantile(quantile)
		group['Label_Quantile'] = np.where(group['Future_Return'] >= threshold, 1, 0)
		return group

	df = df.groupby('Date').apply(quantile_label)
	return df


df = label_quantile(df)


# 3. Risk-Adjusted Labeling
def label_risk_adjusted(df, return_threshold=0.03, risk_multiple=1.0, risk_window=20):
	"""
	Labels a day as 1 if the future return is above a return threshold adjusted for risk.
	Risk is estimated as the rolling standard deviation of past returns.
	The threshold becomes: return_threshold + (risk_multiple * volatility)
	"""
	df = df.copy()
	# Calculate daily returns for each stock (historical)
	df['Daily_Return'] = df.groupby('Stock')['Close'].pct_change()
	# Rolling volatility over past risk_window days
	df['Volatility'] = df.groupby('Stock')['Daily_Return'].transform(lambda x: x.rolling(risk_window).std())
	# Fill missing volatility with a small number to avoid NaNs (or drop those rows)
	df['Volatility'] = df['Volatility'].fillna(0)

	# Adjust threshold for risk
	df['Risk_Adjusted_Threshold'] = return_threshold + risk_multiple * df['Volatility']

	conditions = (df['Future_Return'] >= df['Risk_Adjusted_Threshold'])
	df['Label_RiskAdjusted'] = np.where(conditions, 1, 0)
	return df


df = label_risk_adjusted(df)


# 4. Dynamic Threshold Labeling
def label_dynamic_threshold(df, base_threshold=0.03, dynamic_factor=1.5, risk_window=20):
	"""
	Uses historical volatility to dynamically adjust the threshold.
	The threshold is: base_threshold * (1 + dynamic_factor * volatility)
	"""
	df = df.copy()
	# Calculate daily returns for each stock (historical)
	df['Daily_Return'] = df.groupby('Stock')['Close'].pct_change()
	df['Volatility'] = df.groupby('Stock')['Daily_Return'].transform(lambda x: x.rolling(risk_window).std())
	df['Volatility'] = df['Volatility'].fillna(0)

	# Dynamic threshold adjusted for volatility
	df['Dynamic_Threshold'] = base_threshold * (1 + dynamic_factor * df['Volatility'])
	conditions = (df['Future_Return'] >= df['Dynamic_Threshold'])
	df['Label_Dynamic'] = np.where(conditions, 1, 0)
	return df


df = label_dynamic_threshold(df)



# Display a few rows to see the labels
print(df[['Date', 'Stock', 'Close', 'Future_Return', 'Label_Combined', 'Label_Quantile',
		  'Label_RiskAdjusted', 'Label_Dynamic', ]].head(20))
