import datetime
import os
import random,talib

import numpy as np
import pandas as pd,pickle as pk
import talib
from Prediction.SuperTrend import SuperTrendPrediction
from Prediction import CONFIG


def Random():
	return random.randint(0,10)>8

def getCandleSignal(df):
	print(talib.CDL)


def ShouldBuy(df):
	# return Random()
	print(df)
	getCandleSignal()
	exit()

def RandomPredicition(df):
	if ShouldBuy(df):
		return True,"BUY"
	return False,"BUY"

def MACDPrediciton(df,fastperiod=12,slowperiod=26,signalperiod=9,ndays=4):
	_,_,signal=talib.MACD(df["Close"].values,fastperiod=fastperiod,slowperiod=slowperiod,signalperiod=signalperiod)
	# print(df.iloc[-1:])
	# print(signal[-10:])
	if signal[-1]>0:
		if np.any(signal[-ndays:]<=0):
			return True,"BUY"
	else:
		if np.any(signal[-ndays:] >= 0):
			return True, "SELL"
	return False,None

def getTargetAndStopLoss(df,signal,side):
	if signal and side=="BUY":
		currentPrice = df["Close"].values[-1]
		stoploss = currentPrice - currentPrice * CONFIG.STOPLOSSPERCENT/100
		Target = currentPrice + currentPrice * CONFIG.TARGETPERCENT/100
		return currentPrice,stoploss,Target
	return df["Close"].values[-1],None,None

def MakePrediciton(df):
	# signal,side=RandomPredicition(df)
	signal,side= MACDPrediciton(df)
	# signal,side= SuperTrendPrediction(df)
	currentPrice, stoploss, Target=getTargetAndStopLoss(df,signal,side)
	return signal,side,currentPrice, stoploss, Target

def getDatFrame(stockData):
    try:
        return pd.DataFrame(stockData["data"],columns=stockData["columns"],index=stockData["index"])
    except Exception as e:
        print(stockData)
        raise e

def getData(key=None):
    with open("StockData/AllSTOCKS.pk", "rb") as f:
        Fulldata=pk.load(f)
    if key is None:
        return Fulldata
    else:
        return getDatFrame(Fulldata[key])

def getPredicitonForDate(df,date):
	date=datetime.datetime.strptime(date,"%Y-%m-%d")
	print(MakePrediciton(df[:date]))


if __name__ == '__main__':
	data=getData("HDFCBANK")
	# print(MakePrediciton(data[:-5]))
	print(getPredicitonForDate(data,"1996-08-14"))