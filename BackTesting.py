import os
import pickle as pk
import time,itertools

import pandas as pd
from Prediction.Startegy import MakePrediciton
from classes.ColorText import  colorText
import concurrent.futures
from DataProcessing.DataLoad import getData,getDatFrame


def getBrokrage(ammount,brokragePercent=0.24):
    return ammount*brokragePercent/100
def SellStock(ammount,sellprice,i,position,TradesList,df,reason="Target"):
    ammount += position["Quantity"] * sellprice-getBrokrage(position["Quantity"] * sellprice)
    position.update({"SelDate": df.index[i - 1], "SelPrice": sellprice, "Reason": reason})
    TradesList.append(position)
    return ammount

def calculateInvestmentGain(df, ammount=10000, startindays=100):
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
        today,pastData = df.iloc[i],df[:i]
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
        signal, side, currentPrice, stoploss, Target = MakePrediciton(pastData)
        if ammount>df["Close"].values[i-1]:
            if signal and side=="BUY" and len(Positions)==0:
                if today["Open"]<Target-(Target-currentPrice)/2 and today["Open"]>currentPrice:
                    buyprice=today["Open"]+today["Open"]*discountpercent
                    quantity=ammount//buyprice
                    if quantity>0 and ammount>quantity*buyprice:
                        Positions.append({"Quantity":quantity,"BuyPrice":buyprice,"Target":Target,"StopLoss":stoploss,"Buy Date":df.index[i]})
                        ammount-=quantity*buyprice-getBrokrage(quantity*buyprice)
        elif signal and side == "SELL" and len(Positions)>0:
            sellprice=today["Opend"]*0.9999
            ammount = SellStock(ammount, sellprice, i, position, TradesList, df, reason="SellSignal")
        LatestPrice=df["Close"].values[-1]
    for position in Positions:
        sellprice = LatestPrice - LatestPrice * discountpercent
        ammount = SellStock(ammount, sellprice, i, position, TradesList, df,reason="InHand")
    return position,ammount,TradesList,LatestPrice


def TrailingStopLosssFixTargetTesting(df,ammount=10000,startindays=100,discountpercent=.002,trailtriggerpercent=5,printFlag=False):
    TradesList,Positions = [],[]
    if df.shape[0]<startindays-10: return
    for i in range(startindays,df.shape[0]):
        pastData,today=df[:i],df.iloc[i]
        High,Low,Close=pastData["High"].values[-1],pastData["Low"].values[-1],pastData["Close"].values[-1]
        if len(Positions)>0:
            remaniedPositions=[]
            for position in Positions:
                if High>position["Target"]:
                    sellprice=position["Target"]-position["Target"]*discountpercent
                    if printFlag:print("Target Hitt",Close,position)
                    ammount=SellStock(ammount, sellprice, i, position, TradesList, df,reason="Target")
                elif Low < position["StopLoss"]:
                    sellprice = position["StopLoss"] - position["StopLoss"] * discountpercent
                    if printFlag:print("Stoploss Hitt",Close,position)
                    ammount=SellStock(ammount, sellprice, i, position, TradesList, df,reason="StopLoss")
                else:
                    buyprice=position["BuyPrice1"] if "BuyPrice1" in position else position["BuyPrice"]
                    tailtargetprices=buyprice+buyprice*trailtriggerpercent/100
                    if Close>tailtargetprices:
                        newstoploss=Close-(buyprice-position["StopLoss"])
                        if printFlag:
                            print("Stoploss updated",Close)
                            print(position)
                        position.update({'StopLoss':newstoploss,'BuyPrice1':Close})
                        if printFlag:print(position)
                    remaniedPositions.append(position)
            Positions=remaniedPositions
        signal, side, currentPrice, stoploss, Target = MakePrediciton(pastData)
        if ammount>df["Close"].values[i-1]:
            if signal and side=="BUY" and len(Positions)==0:
                if today["Open"]<Target-(Target-currentPrice)/2 and today["Open"]>currentPrice:
                    buyprice=today["Open"]+today["Open"]*discountpercent
                    quantity=ammount//buyprice
                    if quantity>0 and ammount>quantity*buyprice:
                        Positions.append({"Quantity":quantity,"BuyPrice":buyprice,"Target":Target,"StopLoss":stoploss,"Buy Date":df.index[i]})
                        ammount-=quantity*buyprice-getBrokrage(quantity*buyprice)
        elif signal and side == "SELL" and len(Positions) > 0:
            sellprice = today["Open"] * 0.9999
            ammount = SellStock(ammount, sellprice, i, position, TradesList, df, reason="SellSignal")
    LatestPrice=df["Close"].values[-1]
    for position in Positions:
        sellprice = LatestPrice - LatestPrice * discountpercent
        ammount = SellStock(ammount, sellprice, i, position, TradesList, df,reason="InHand")
    return Positions,ammount,TradesList,LatestPrice


def TrailingStopLosssTesting(df,ammount=10000,startindays=100,discountpercent=.002,trailtriggerpercent=5,printFlag=False):
    TradesList,Positions = [],[]
    if df.shape[0]<startindays-10: return
    for i in range(startindays,df.shape[0]):
        pastData,today=df[:i],df.iloc[i]
        High,Low,Close=pastData["High"].values[-1],pastData["Low"].values[-1],pastData["Close"].values[-1]
        if len(Positions)>0:
            remaniedPositions=[]
            for position in Positions:
                if Low < position["StopLoss"]:
                    sellprice = position["StopLoss"] - position["StopLoss"] * discountpercent
                    if printFlag:print("Stoploss Hitt",Close,position)
                    ammount=SellStock(ammount, sellprice, i, position, TradesList, df,reason="StopLoss")
                else:
                    buyprice=position["BuyPrice1"] if "BuyPrice1" in position else position["BuyPrice"]
                    tailtargetprices=buyprice+buyprice*trailtriggerpercent/100
                    if Close>tailtargetprices:
                        newstoploss=Close-(buyprice-position["StopLoss"])
                        if printFlag:
                            print("Stoploss updated",Close)
                            print(position)
                        position.update({'StopLoss':newstoploss,'BuyPrice1':Close})
                        if printFlag:print(position)
                    remaniedPositions.append(position)
            Positions=remaniedPositions
        signal, side, currentPrice, stoploss, Target = MakePrediciton(pastData)
        if ammount>df["Close"].values[i-1]:
            if signal and side=="BUY" and len(Positions)==0:
                if today["Open"]<Target-(Target-currentPrice)/2 and today["Open"]>currentPrice:
                    buyprice=today["Open"]+today["Open"]*discountpercent
                    quantity=ammount//buyprice
                    if quantity>0 and ammount>quantity*buyprice:
                        Positions.append({"Quantity":quantity,"BuyPrice":buyprice,"Target":Target,"StopLoss":stoploss,"Buy Date":df.index[i]})
                        ammount-=quantity*buyprice-getBrokrage(quantity*buyprice)
        elif signal and side == "SELL" and len(Positions) > 0:
            sellprice = today["Opend"] * 0.9999
            ammount = SellStock(ammount, sellprice, i, position, TradesList, df, reason="SellSignal")
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


def DobackTesting(df,key="",ammount=10000,startindays=100,discountpercent=.002,method="SL&T",printResults=False):
    baseammount=ammount
    if method=="TSL&T":
        position,ammount,TradesList,LatestPrice=TrailingStopLosssFixTargetTesting(df,ammount=ammount,startindays=startindays,discountpercent=discountpercent,printFlag=False)
    elif method == "TSL":
        position, ammount, TradesList, LatestPrice = TrailingStopLosssFixTargetTesting(df, ammount=ammount,
                                                                                       startindays=startindays,
                                                                                       discountpercent=discountpercent,
                                                                                       printFlag=False)
    else:
        position,ammount,TradesList,LatestPrice=TargetStopLosssTesting(df,ammount=ammount,startindays=startindays,discountpercent=discountpercent)
    longtermgain=calculateInvestmentGain(df, ammount, startindays)
    results,longtermResults=ArrangeLongTermResults(baseammount, longtermgain)
    results=ArangeTraidingResults(key,df, baseammount, longtermgain, ammount, TradesList, LatestPrice,results,longtermResults, printResults)
    return results


def SingleStock(key="HDFCBANK"):
    df=getData(key)
    DobackTesting(df,key)
    # print(calculateInvertmentGain(df))


def ProcessStock(stockdict,k,method="SL&T",printResults=True):
    return DobackTesting(getDatFrame(stockdict[k]), k, method=method,printResults=printResults)


def AllStock():
    stockdict=getData()
    for k in stockdict:
        ProcessStock(stockdict,k,printResults=True)

def FurtherAnalaysis(df):
    print(df.columns)
    longtermgain= df["longtermgain"].sum()
    if "TraidingLoss" in df.columns:
        TraidingProfit= df["TraidingGain"].sum()-df["TraidingLoss"].sum()
    else:
        TraidingProfit = df["TraidingGain"].sum()
    if TraidingProfit>0:
        if TraidingProfit>longtermgain:
            print(f"Well Done you earn {TraidingProfit/longtermgain*100:.2f}% better in Traiding")
        else:
            print(f"Long Term Gain is {longtermgain/TraidingProfit*100:.2}% better then Traiding Stay Invested")
    else:
        print(f"You are in loss with Traiding stay with Investment")


def AllStockMultProcessing(type="ALL",method="SL&T"):
    assert method in ("TSL&T","TSL","SL&T") #TrailingStopLosssFixTargetTesting TrailingStopLosssFixTargetTesting TargetStopLosssTesting
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
        results = list(executor.map(ProcessStock, stockdictlist,keys,itertools.repeat(method)))
    df=pd.DataFrame(results)
    del df["resp"]
    os.makedirs("Results",exist_ok=True)
    df.to_csv(f"Results/Results{method}.csv",index=None)
    print("Total Time Taken ",time.time()-st,"Results Save at",f"Results/Results{method}.csv")

if __name__ == '__main__':

    # AllStock()
    stype="Nifty50"
    # method="SL&T"
    # method="TSL&T"
    method="TSL"
    # AllStockMultProcessing(stype,method=method)
    FurtherAnalaysis(pd.read_csv(f"Results/Results{method}.csv"))
    # SingleStock()

