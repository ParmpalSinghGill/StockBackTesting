import datetime,warnings,talib
warnings.filterwarnings("ignore")
import pandas as pd
from PlotCode.PlotCandles import PlotChart, PlotMACDForTrade, PlotTrend, PlotMACD, PlotCandles

from DataProcessing.DataLoad import getData
from Prediction.MYTrendDetection import FindMyTrend



def findTrend(pastData, n=10, lastNDays=2):
	# return findpytrend(pastData, n=n, lastNDays=lastNDays)
	return FindMyTrend(pastData, min_days=10, max_reversal_pct=0.02,n=n, lastNDays=lastNDays)


def CheckTrend(df,lastDate,n=10,lastNDays=2):
	lastDate=datetime.datetime.strptime(lastDate,"%Y-%m-%d")
	pastData=df[:lastDate][-50:]
	Trend, TrendStart, TrnedEnd = findTrend(pastData, n=n, lastNDays=lastNDays)
	if Trend == None:
		print("No Trend")
		return
	TrenDf = pastData[(pastData.index >= TrendStart) & (pastData.index <= TrnedEnd)]
	if Trend == "Down":
		startprice, endprice = TrenDf.loc[TrenDf.index[0], "High"], TrenDf.loc[TrenDf.index[-1], "Low"]
	else:
		startprice, endprice = TrenDf.loc[TrenDf.index[0], "Low"], TrenDf.loc[TrenDf.index[-1], "High"]
	StockText=f"From {startprice:.2f} to {endprice:.2f} ({abs(startprice-endprice)/startprice*100:.2}%)"
	print(TrenDf)
	PlotChart(pastData, f"{Trend} from {TrendStart}--->{TrnedEnd} {StockText}", (TrendStart, TrnedEnd))

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['EMA12'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    return data[['MACD', 'Signal_Line']]




def CheckMACDTrades(key,method="SL&T"):
	df = getData(key)
	TradeDf=pd.read_csv(f"Results/{method}/{key}.csv")
	for i,row in TradeDf.iterrows():
		print(row)
		PlotMACDForTrade(df,row,Key=key)


if __name__ == '__main__':
	# CheckMACDTrades("HDFCBANK")
	df = getData("HDFCBANK")
	# PlotCandles(df[-100:])

	# PlotMACD(df,Key="HDFCBANK")
	PlotTrend(findTrend,df)
	# CheckTrend(df,lastDate="2000-08-01")
	# print(df)


# 2000-03-17 00:00:00 Chart End 2000-08-03 00:00:00