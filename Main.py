import datetime,warnings,talib
warnings.filterwarnings("ignore")

import pandas as pd
import mplfinance as mpf
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


from DataProcessing.DataLoad import getData
from Prediction.MYTrendDetection import FindMyTrend



def findTrend(pastData, n=10, lastNDays=2):
	# return findpytrend(pastData, n=n, lastNDays=lastNDays)
	return FindMyTrend(pastData, min_days=10, max_reversal_pct=0.02,n=n, lastNDays=lastNDays)

def PlotChart(pastData,Trend="",TrendBox=None):
	pastData.index = pastData.index.map(lambda x: x.to_pydatetime())
	fig, axlist=mpf.plot(pastData, type='candle', style='charles', title=f'Candlestick chart for {Trend}',
	         ylabel='Price (USD)', volume=True, datetime_format='%Y-%m-%d',
	         xrotation=45, show_nontrading=True,returnfig=True, figratio=(30, 8))
	# Customize x-axis labels to make them more frequent
	ax = axlist[0]  # Get the main axis (the candlestick chart)

	if TrendBox is not None :
		TrendStart , TrnedEnd=TrendBox
		highlight_start_mdate = mdates.date2num(pd.to_datetime(TrendStart))
		highlight_end_mdate = mdates.date2num(pd.to_datetime(TrnedEnd))
		TrendData=pastData[(TrendStart<=pastData.index)&(pastData.index<=TrnedEnd)]
		# Get the price range to cover with the box (you can adjust the vertical limits as needed)
		low_price = TrendData['Low'].min()  # Lowest price in the data range
		high_price = TrendData['High'].max()  # Highest price in the data range
		# Create a rectangle box over the selected date range
		rect = Rectangle((highlight_start_mdate, low_price),  # (x, y) lower-left corner
		                 highlight_end_mdate - highlight_start_mdate,  # width (difference in date)
		                 high_price - low_price,  # height (difference in price)
		                 linewidth=1, edgecolor='red', facecolor='yellow', alpha=0.3)  # Rectangle style

		# Add the rectangle to the plot
		ax.add_patch(rect)

	# Set date format and frequency of the labels
	ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))  # Show labels every week
	ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Format labels as 'Year-Month-Day'

	# Rotate date labels to make them readable
	fig.autofmt_xdate()

	# Show the chart
	mpf.show()


def PlotTrend(df,windowlenght=100,n=10,lastNDays=2):
	if df.shape[0] < windowlenght - 10: return
	j=1
	for i in range(windowlenght, df.shape[0]):
		pastData = df[i-windowlenght:i]
		Trend,TrendStart, TrnedEnd=findTrend(pastData,n=n,lastNDays=lastNDays)
		if Trend==None: continue
		TrenDf=pastData[(pastData.index>=TrendStart) &(pastData.index<=TrnedEnd)]
		if Trend == "Down":
			startprice, endprice = TrenDf.loc[TrenDf.index[0], "High"], TrenDf.loc[TrenDf.index[-1], "Low"]
		else:
			startprice, endprice = TrenDf.loc[TrenDf.index[0], "Low"], TrenDf.loc[TrenDf.index[-1], "High"]
		ChartStart, ChartEnd = pastData.index[0], pastData.index[-1]
		print(TrenDf)
		print(f"Chart Start {ChartStart} Chart End {ChartEnd}")
		print(f"Trend Start {TrendStart} Trend End {TrnedEnd}")
		StockText=f"From {startprice:.2f} to {endprice:.2f} ({abs(startprice-endprice)/startprice*100:.2}%)"
		print(j,Trend,f"Stock Move From {startprice:.2f} to {endprice:.2f} That is {abs(startprice-endprice)/startprice*100:.2}%")
		PlotChart(pastData, f"{Trend} from {TrendStart}--->{TrnedEnd} {StockText}",(TrendStart,TrnedEnd))
		j+=1
		# exit()

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


def PlotMACD(df,fastperiod=12,slowperiod=26,signalperiod=9):
	_, _, signal = talib.MACD(df["Close"].values, fastperiod=fastperiod, slowperiod=slowperiod,
	                          signalperiod=signalperiod)



if __name__ == '__main__':
	df = getData("HDFCBANK")
	PlotMACD(df)

	# PlotTrend(df)
	# CheckTrend(df,lastDate="2000-08-01")
	# print(df)


# 2000-03-17 00:00:00 Chart End 2000-08-03 00:00:00