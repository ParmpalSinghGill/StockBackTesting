import datetime

import pandas as pd
import numpy as np
import pytrendseries

def FindMyTrend(stock_data, min_days=5,window=21, lastNDays=2,trend="downtrend",isPloting=False):
	trends_detected = pytrendseries.detecttrend(stock_data[["Close"]][-window-5:], trend=trend,limit=min_days, window=window)
	if trends_detected.shape[0]>0:
		lasttrend=trends_detected.iloc[-1]
		if isPloting:
			lastNDays=2
			if lasttrend["to"]==stock_data.index[-1]:
				return None, None, None
		if lasttrend["to"] > stock_data.index[-1] - datetime.timedelta(days=lastNDays):
			return trend,lasttrend["from"],lasttrend["to"]
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

	stock_data = pd.DataFrame(data,index=pd.date_range(start='2023-11-01', periods=30))

	# # Detect trends
	# detected_trends = detect_trend(stock_data, min_days=5, max_reversal_pct=0.02)
	#
	# for trend in detected_trends:
	# 	print(trend)
	print(FindMyTrend(stock_data))
