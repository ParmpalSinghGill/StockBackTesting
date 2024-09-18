import random


def ShouldBuy(df):
	return random.randint(0,10)>8

def MakePrediciton(df):
	if ShouldBuy(df):
		currentPrice=df["Close"].values[-1]
		stoploss=currentPrice-currentPrice*.1
		Target=currentPrice+currentPrice*.1
		return True,currentPrice,stoploss,Target
	return False,None,None,None