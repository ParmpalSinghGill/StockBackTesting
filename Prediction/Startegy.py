import random,talib
import pandas as pd,pickle as pk

def Random():
	return random.randint(0,10)>8

def getCandleSignal(df):
	print(talib.CDL)


def ShouldBuy(df):
	# return Random()
	print(df)
	getCandleSignal()
	exit()



def MakePrediciton(df):
	if ShouldBuy(df):
		currentPrice=df["Close"].values[-1]
		stoploss=currentPrice-currentPrice*.1
		Target=currentPrice+currentPrice*.1
		return True,"BUY",currentPrice,stoploss,Target
	return False,"BUY",None,None,None

def getDatFrame(stockData):
    try:
        return pd.DataFrame(stockData["data"],columns=stockData["columns"],index=stockData["index"])
    except Exception as e:
        print(stockData)
        raise e

def getData(key=None):
    with open("../StockData/AllSTOCKS.pk", "rb") as f:
        Fulldata=pk.load(f)
    if key is None:
        return Fulldata
    else:
        return getDatFrame(Fulldata[key])

if __name__ == '__main__':
    data=getData("HDFCBANK")
    MakePrediciton(data)