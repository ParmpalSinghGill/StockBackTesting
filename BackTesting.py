import pickle as pk
import time,itertools

import pandas as pd
from Startegy import MakePrediciton
from classes.ColorText import  colorText
import concurrent.futures

def getDatFrame(stockData):
    try:
        return pd.DataFrame(stockData["data"],columns=stockData["columns"],index=stockData["index"])
    except Exception as e:
        print(stockData)
        raise e


def getData(key=None):
    with open("StockData/AllSTOCKS.pk","rb") as f:
        Fulldata=pk.load(f)
    if key is None:
        return Fulldata
    else:
        return getDatFrame(Fulldata[key])

def getBrokrage(ammount,brokragePercent=0.24):
    return ammount*brokragePercent/100
def SellStock(ammount,sellprice,i,position,TradesList,df,reason="Target"):
    ammount += position["Quantity"] * sellprice-getBrokrage(position["Quantity"] * sellprice)
    position.update({"SelDate": df.index[i - 1], "SelPrice": sellprice, "Reason": reason})
    TradesList.append(position)
    return ammount

def calculateInvertmentGain(df,ammount=10000,startindays=100):
    if df.shape[0]>startindays:
        buyprice=df.loc[df.index[startindays],"High"]
    else:
        buyprice = df.loc[df.index[0], "High"]
    selprice=df.loc[df.index[-1],"Low"]
    baseammount=ammount
    stockcount=ammount//buyprice
    ammount-=stockcount*buyprice
    ammount+=stockcount*selprice
    # print("Total Long term gain is ",ammount-baseammount,"With ",stockcount,"Shares")
    return ammount-baseammount

def TargetStopLosssTesting(df,ammount=10000,startindays=100,discountpercent=.002):
    TradesList,Positions = [],[]
    if df.shape[0]<startindays-10: return
    for i in range(startindays,df.shape[0]):
        pastData=df[:i]
        High,Low=pastData["High"].values[-1],pastData["Low"].values[-1]
        if len(Positions)>0:
            remaniedPositions=[]
            for position in Positions:
                if High>position["Target"]:
                    sellprice=position["Target"]-position["Target"]*discountpercent
                    ammount=SellStock(ammount, sellprice, i, position, TradesList, df,reason="Target")
                elif Low < position["StopLoss"]:
                    sellprice = position["StopLoss"] - position["StopLoss"] * discountpercent
                    ammount=SellStock(ammount, sellprice, i, position, TradesList, df,reason="StopLoss")
                else:
                    remaniedPositions.append(position)
            Positions=remaniedPositions
        today = df.iloc[i]
        if ammount>df["Close"].values[i-1]:
            pred=MakePrediciton(pastData)
            if pred[0]:
                if today["Open"]<pred[3]-(pred[3]-pred[1])/2 and today["Open"]>pred[2]:
                    buyprice=today["Open"]+today["Open"]*discountpercent
                    quantity=ammount//buyprice
                    if quantity>0 and ammount>quantity*buyprice:
                        Positions.append({"Quantity":quantity,"BuyPrice":buyprice,"Target":pred[3],"StopLoss":pred[2],"Buy Date":df.index[i]})
                        ammount-=quantity*buyprice-getBrokrage(quantity*buyprice)
    LatestPrice=df["Close"].values[-1]
    for position in Positions:
        sellprice = LatestPrice - LatestPrice * discountpercent
        ammount = SellStock(ammount, sellprice, i, position, TradesList, df,reason="InHand")
    return position,ammount,TradesList,LatestPrice

def ArrangeLongTermResults(baseammount,longtermgain,results={}):
    if longtermgain>0:
        results.update({"longtermgain":longtermgain,"longtermgainpercent":f"{longtermgain*100/baseammount:.2f}"})
        longtermResults=f"Long term {colorText.GREEN} gain is  {longtermgain*100//baseammount}% {colorText.END}"
    else:
        results.update({"longtermloss":longtermgain*-1,"longtermlosspercent":f"{longtermgain*-100/baseammount:.2f}"})
        longtermResults=f"Long term {colorText.FAIL} Loss is {longtermgain*-100//baseammount}% {colorText.END}"
    return results,longtermResults


def ArangeTraidingResults(key,df,baseammount,longtermgain, ammount,TradesList,LatestPrice,results,longtermResults,printResults=False):
    profitTrades=len([t for t in TradesList if t["Reason"]=="Target"])
    lossTrades=len([t for t in TradesList if t["Reason"]=="StopLoss"])
    StockInHand=sum([t["Quantity"] for t in TradesList if t["Reason"]=="InHand"])
    results.update({"key":key,"profitTrades":profitTrades,"lossTrades":lossTrades,"StockInHand":StockInHand,"LatestPrice":LatestPrice})
    if printResults:
        print("*************************",key,df.shape[0],"Days*************************")
        if StockInHand>0:
            print("Profit Trades",profitTrades,"Loss Trades",lossTrades,"In Hand",StockInHand,"LTP",LatestPrice)
        else:
            print("Profit Trades",profitTrades,"Loss Trades",lossTrades)
    if ammount>baseammount:
        results.update({"TraidingGain":ammount-baseammount,"TraidingGainpercent":f"{(ammount-baseammount)*100/baseammount:.2f}"})
        resp=f"Trading {colorText.GREEN} Profit {(ammount-baseammount)*100//baseammount}% {colorText.END} With {len(TradesList)} Trades And {longtermResults}"
    else:
        results.update({"TraidingLoss":baseammount-ammount,"TraidingLosspercent":f"{(baseammount-ammount)*100/baseammount:.2f}"})
        resp=f"Trading {colorText.FAIL} Loss {(baseammount-ammount)*100//baseammount}% {colorText.END} With {len(TradesList)} Trades And {longtermResults}"
    results["resp"]=resp
    if printResults:
        print(resp)
    return results


def DobackTesting(df,key="",ammount=10000,startindays=100,discountpercent=.002,printResults=False):
    baseammount=ammount
    position,ammount,TradesList,LatestPrice=TargetStopLosssTesting(df,ammount=ammount,startindays=startindays,discountpercent=discountpercent)
    longtermgain=calculateInvertmentGain(df,ammount,startindays)
    results,longtermResults=ArrangeLongTermResults(baseammount, longtermgain)
    results=ArangeTraidingResults(key,df, baseammount, longtermgain, ammount, TradesList, LatestPrice,results,longtermResults, printResults)
    return results


def SingleStock(key="HDFCBANK"):
    df=getData(key)
    DobackTesting(df,key)
    # print(calculateInvertmentGain(df))


def ProcessStock(stockdict,k,printResults=True):
    return DobackTesting(getDatFrame(stockdict[k]), k, printResults=printResults)


def AllStock():
    stockdict=getData()
    for k in stockdict:
        ProcessStock(stockdict,k,printResults=True)

def FurtherAnalaysis(df):
    longtermgain= df["longtermgain"].sum()
    TraidingProfit= df["TraidingGain"].sum()-df["TraidingLoss"].sum()
    if TraidingProfit>0:
        if TraidingProfit>longtermgain:
            print(f"Well Done you earn {TraidingProfit/longtermgain*100:.2f}% better in Traiding")
        else:
            print(f"Long Term Gain is {longtermgain/TraidingProfit*100:.2}% better then Traiding")
    else:
        print(f"You are in loss with Traiding stay with Investment")


def AllStockMultProcessing(type="ALL"):
    stockdict=getData()
    if type=="ALL":
        keys=stockdict.keys()
        stockdictlist=[stockdict for k in stockdict.keys()]
    else:
        with open("StockData/Indexices.pk","rb") as f:
            keys=pk.load(f)[type]
            stockdictlist=[stockdict for k in keys]
    st=time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
        # Submit the tasks and collect results
        results = list(executor.map(ProcessStock, stockdictlist,keys ))
    df=pd.DataFrame(results)
    del df["resp"]
    df.to_csv("Results.csv",index=None)
    print("Total Time Taken ",time.time()-st)

# AllStock()
# AllStockMultProcessing("Nifty50")
FurtherAnalaysis(pd.read_csv("Results.csv"))
# SingleStock()

