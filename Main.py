import datetime
import os
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import mplfinance as mpf
from VisulaizeChart import PlotSimpleChart
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


from DataLoad import getData
from Prediction.TrendPrediction import identify_df_trends


def PlotTrend11(days=30,n=10):
	df=getData("HDFCBANK")
	trenddata=identify_df_trends(df[100:],"Close",window_size=n)
	for lastday,row in trenddata.iterrows():
		if not pd.isna(row["Up Trend"]) or not pd.isna(row["Down Trend"]):
			trend="UP" if not pd.isna(row["Up Trend"]) else "Down"
			daybefore=lastday-datetime.timedelta(days=days)
			selectdays=df[daybefore:lastday]
			# Create and display the candlestick chart using mplfinance
			trendpred="_".join(trenddata["Up Trend" if trend=="UP" else "Down Trend"][daybefore:lastday].fillna("").values)
			# print(trenddata["Up Trend" if trend=="UP" else "Down Trend"][daybefore:lastday])
			trendpred=trendpred.split("__")[-1]

			if len(trendpred.replace("_",""))>n:
				# print(len(trendpred),len(trendpred.replace("_","")),"A",trendpred,"B")
				print(trend,trendpred.rsplit("__")[-1])
				mpf.plot(selectdays, type='candle', style='charles', title=f'Candlestick Chart for {trend}',ylabel='Price (USD)', volume=True)

def PlotChart(pastData,Trend="",TrendStart=None,TrnedEnd=None):
	pastData.index = pastData.index.map(lambda x: x.to_pydatetime())
	fig, axlist=mpf.plot(pastData, type='candle', style='charles', title=f'Candlestick chart for {Trend}',
	         ylabel='Price (USD)', volume=True, datetime_format='%Y-%m-%d',
	         xrotation=45, show_nontrading=True,returnfig=True, figratio=(30, 8))
	# Customize x-axis labels to make them more frequent
	ax = axlist[0]  # Get the main axis (the candlestick chart)

	if TrendStart is not None and TrnedEnd is not None:
		print(TrendStart,TrnedEnd)
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


def PlotTrend(df,startindays=100,n=20,lastNDays=2):
	if df.shape[0] < startindays - 10: return
	j=1
	for i in range(startindays, df.shape[0]):
		pastData = df[i-100:i]
		trenddata = identify_df_trends(pastData[-3*n:], "Close", window_size=n)
		if "Down Trend" not in trenddata.columns and "Up Trend" not in trenddata.columns: continue
		lastdays=trenddata[-lastNDays:].dropna()
		Trend="Down Trend" if "Down Trend" in lastdays.columns else "Up Trend"
		if lastdays.shape[0]==0: continue
		trenddata[Trend]=trenddata[Trend].fillna("")
		TrendSymbol=trenddata[Trend].values[-3]
		TrenDf=trenddata[trenddata[Trend]==TrendSymbol]
		TrendStart,TrnedEnd=TrenDf.index[0].strftime('%Y-%m-%d'),TrenDf.index[-1].strftime('%Y-%m-%d')
		ChartStart,ChartEnd=pastData.index[0],pastData.index[-1]
		if Trend=="Down Trend": start,end=TrenDf.loc[TrenDf.index[0],"High"],TrenDf.loc[TrenDf.index[-1],"Low"]
		else:	start,end=TrenDf.loc[TrenDf.index[0],"Low"],TrenDf.loc[TrenDf.index[-1],"High"]
		print(TrenDf)
		print(f"Chart Start {ChartStart} Chart End {ChartEnd}")
		print(f"Trend Start {TrendStart} Trend End {TrnedEnd}")
		StockText=f"From {start:.2f} to {end:.2f} ({abs(start-end)/start*100:.2}%)"
		print(j,Trend,f"Stock Move From {start:.2f} to {end:.2f} That is {abs(start-end)/start*100:.2}%")
		PlotChart(pastData, f"{Trend} from {TrendStart}--->{TrnedEnd} {StockText}",TrendStart,TrnedEnd)
		j+=1
		# exit()

def CheckTrend(df,lastDate,n=10):
	lastDate=datetime.datetime.strptime(lastDate,"%Y-%m-%d")
	pastData=df[:lastDate]
	trenddata = identify_df_trends(pastData[-3*n:], "Close", window_size=n)
	print(trenddata)
	PlotChart(pastData[-50:])


if __name__ == '__main__':
	df = getData("HDFCBANK")
	PlotTrend(df)
	# CheckTrend(df,lastDate="2000-08-02")


