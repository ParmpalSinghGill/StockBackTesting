import os

import pandas as pd
import talib,numpy as np
from DataProcessing.DataLoad import getData,getDatFrame
from itertools import compress

OUTPUT_FOLDER = 'Temp/'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

candle_names = talib.get_function_groups()['Pattern Recognition']
removed = ['CDLCOUNTERATTACK', 'CDLLONGLINE', 'CDLSHORTLINE',
           'CDLSTALLEDPATTERN', 'CDLKICKINGBYLENGTH']
candle_names = [name for name in candle_names if name not in removed]

candlestick_days = {
    "CDL2CROWS": 2,
    "CDL3BLACKCROWS": 3,
    "CDL3INSIDE": 3,
    "CDL3LINESTRIKE": 4,
    "CDL3OUTSIDE": 3,
    "CDL3STARSINSOUTH": 3,
    "CDL3WHITESOLDIERS": 3,
    "CDLABANDONEDBABY": 3,
    "CDLADVANCEBLOCK": 3,
    "CDLBELTHOLD": 1,
    "CDLBREAKAWAY": 5,
    "CDLCLOSINGMARUBOZU": 1,
    "CDLCONCEALBABYSWALL": 4,
    "CDLCOUNTERATTACK": 2,
    "CDLDARKCLOUDCOVER": 2,
    "CDLDOJI": 1,
    "CDLDOJISTAR": 2,
    "CDLDRAGONFLYDOJI": 1,
    "CDLENGULFING": 2,
    "CDLEVENINGDOJISTAR": 3,
    "CDLEVENINGSTAR": 3,
    "CDLGAPSIDESIDEWHITE": 2,
    "CDLGRAVESTONEDOJI": 1,
    "CDLHAMMER": 1,
    "CDLHANGINGMAN": 1,
    "CDLHARAMI": 2,
    "CDLHARAMICROSS": 2,
    "CDLHIGHWAVE": 1,
    "CDLHIKKAKE": 3,
    "CDLHIKKAKEMOD": 3,
    "CDLHOMINGPIGEON": 2,
    "CDLIDENTICAL3CROWS": 3,
    "CDLINNECK": 2,
    "CDLINVERTEDHAMMER": 1,
    "CDLKICKING": 2,
    "CDLKICKINGBYLENGTH": 2,
    "CDLLADDERBOTTOM": 5,
    "CDLLONGLEGGEDDOJI": 1,
    "CDLLONGLINE": 1,
    "CDLMARUBOZU": 1,
    "CDLMATCHINGLOW": 2,
    "CDLMATHOLD": 5,
    "CDLMORNINGDOJISTAR": 3,
    "CDLMORNINGSTAR": 3,
    "CDLONNECK": 2,
    "CDLPIERCING": 2,
    "CDLRICKSHAWMAN": 1,
    "CDLRISEFALL3METHODS": 5,
    "CDLSEPARATINGLINES": 2,
    "CDLSHOOTINGSTAR": 1,
    "CDLSHORTLINE": 1,
    "CDLSPINNINGTOP": 1,
    "CDLSTALLEDPATTERN": 3,
    "CDLSTICKSANDWICH": 3,
    "CDLTAKURI": 1,
    "CDLTASUKIGAP": 3,
    "CDLTHRUSTING": 2,
    "CDLTRISTAR": 3,
    "CDLUNIQUE3RIVER": 3,
    "CDLUPSIDEGAP2CROWS": 3,
    "CDLXSIDEGAP3METHODS": 4
}

candle_rankings = {
        "CDL3LINESTRIKE_Bull": 1,
        "CDL3LINESTRIKE_Bear": 2,
        "CDL3BLACKCROWS_Bull": 3,
        "CDL3BLACKCROWS_Bear": 3,
        "CDLEVENINGSTAR_Bull": 4,
        "CDLEVENINGSTAR_Bear": 4,
        "CDLTASUKIGAP_Bull": 5,
        "CDLTASUKIGAP_Bear": 5,
        "CDLINVERTEDHAMMER_Bull": 6,
        "CDLINVERTEDHAMMER_Bear": 6,
        "CDLMATCHINGLOW_Bull": 7,
        "CDLMATCHINGLOW_Bear": 7,
        "CDLABANDONEDBABY_Bull": 8,
        "CDLABANDONEDBABY_Bear": 8,
        "CDLBREAKAWAY_Bull": 10,
        "CDLBREAKAWAY_Bear": 10,
        "CDLMORNINGSTAR_Bull": 12,
        "CDLMORNINGSTAR_Bear": 12,
        "CDLPIERCING_Bull": 13,
        "CDLPIERCING_Bear": 13,
        "CDLSTICKSANDWICH_Bull": 14,
        "CDLSTICKSANDWICH_Bear": 14,
        "CDLTHRUSTING_Bull": 15,
        "CDLTHRUSTING_Bear": 15,
        "CDLINNECK_Bull": 17,
        "CDLINNECK_Bear": 17,
        "CDL3INSIDE_Bull": 20,
        "CDL3INSIDE_Bear": 56,
        "CDLHOMINGPIGEON_Bull": 21,
        "CDLHOMINGPIGEON_Bear": 21,
        "CDLDARKCLOUDCOVER_Bull": 22,
        "CDLDARKCLOUDCOVER_Bear": 22,
        "CDLIDENTICAL3CROWS_Bull": 24,
        "CDLIDENTICAL3CROWS_Bear": 24,
        "CDLMORNINGDOJISTAR_Bull": 25,
        "CDLMORNINGDOJISTAR_Bear": 25,
        "CDLXSIDEGAP3METHODS_Bull": 27,
        "CDLXSIDEGAP3METHODS_Bear": 26,
        "CDLTRISTAR_Bull": 28,
        "CDLTRISTAR_Bear": 76,
        "CDLGAPSIDESIDEWHITE_Bull": 46,
        "CDLGAPSIDESIDEWHITE_Bear": 29,
        "CDLEVENINGDOJISTAR_Bull": 30,
        "CDLEVENINGDOJISTAR_Bear": 30,
        "CDL3WHITESOLDIERS_Bull": 32,
        "CDL3WHITESOLDIERS_Bear": 32,
        "CDLONNECK_Bull": 33,
        "CDLONNECK_Bear": 33,
        "CDL3OUTSIDE_Bull": 34,
        "CDL3OUTSIDE_Bear": 39,
        "CDLRICKSHAWMAN_Bull": 35,
        "CDLRICKSHAWMAN_Bear": 35,
        "CDLSEPARATINGLINES_Bull": 36,
        "CDLSEPARATINGLINES_Bear": 40,
        "CDLLONGLEGGEDDOJI_Bull": 37,
        "CDLLONGLEGGEDDOJI_Bear": 37,
        "CDLHARAMI_Bull": 38,
        "CDLHARAMI_Bear": 72,
        "CDLLADDERBOTTOM_Bull": 41,
        "CDLLADDERBOTTOM_Bear": 41,
        "CDLCLOSINGMARUBOZU_Bull": 70,
        "CDLCLOSINGMARUBOZU_Bear": 43,
        "CDLTAKURI_Bull": 47,
        "CDLTAKURI_Bear": 47,
        "CDLDOJISTAR_Bull": 49,
        "CDLDOJISTAR_Bear": 51,
        "CDLHARAMICROSS_Bull": 50,
        "CDLHARAMICROSS_Bear": 80,
        "CDLADVANCEBLOCK_Bull": 54,
        "CDLADVANCEBLOCK_Bear": 54,
        "CDLSHOOTINGSTAR_Bull": 55,
        "CDLSHOOTINGSTAR_Bear": 55,
        "CDLMARUBOZU_Bull": 71,
        "CDLMARUBOZU_Bear": 57,
        "CDLUNIQUE3RIVER_Bull": 60,
        "CDLUNIQUE3RIVER_Bear": 60,
        "CDL2CROWS_Bull": 61,
        "CDL2CROWS_Bear": 61,
        "CDLBELTHOLD_Bull": 62,
        "CDLBELTHOLD_Bear": 63,
        "CDLHAMMER_Bull": 65,
        "CDLHAMMER_Bear": 65,
        "CDLHIGHWAVE_Bull": 67,
        "CDLHIGHWAVE_Bear": 67,
        "CDLSPINNINGTOP_Bull": 69,
        "CDLSPINNINGTOP_Bear": 73,
        "CDLUPSIDEGAP2CROWS_Bull": 74,
        "CDLUPSIDEGAP2CROWS_Bear": 74,
        "CDLGRAVESTONEDOJI_Bull": 77,
        "CDLGRAVESTONEDOJI_Bear": 77,
        "CDLHIKKAKEMOD_Bull": 82,
        "CDLHIKKAKEMOD_Bear": 81,
        "CDLHIKKAKE_Bull": 85,
        "CDLHIKKAKE_Bear": 83,
        "CDLENGULFING_Bull": 84,
        "CDLENGULFING_Bear": 91,
        "CDLMATHOLD_Bull": 86,
        "CDLMATHOLD_Bear": 86,
        "CDLHANGINGMAN_Bull": 87,
        "CDLHANGINGMAN_Bear": 87,
        "CDLRISEFALL3METHODS_Bull": 94,
        "CDLRISEFALL3METHODS_Bear": 89,
        "CDLKICKING_Bull": 96,
        "CDLKICKING_Bear": 102,
        "CDLDRAGONFLYDOJI_Bull": 98,
        "CDLDRAGONFLYDOJI_Bear": 98,
        "CDLCONCEALBABYSWALL_Bull": 101,
        "CDLCONCEALBABYSWALL_Bear": 101,
        "CDL3STARSINSOUTH_Bull": 103,
        "CDL3STARSINSOUTH_Bear": 103,
        "CDLDOJI_Bull": 104,
        "CDLDOJI_Bear": 104
    }
def AddPattrens(df):
	for candle in candle_names:
		# below is same as;
		# df["CDL3LINESTRIKE"] = talib.CDL3LINESTRIKE(op, hi, lo, cl)
		df[candle] = getattr(talib, candle)(df["Open"], df["High"], df["Low"], df["Close"])

def getCanleStickPattrns(df,lastndays=0):
    df=df[-lastndays:]
    AddPattrens(df)

    df['candlestick_pattern'] = np.nan
    df['candlestick_match_count'] = np.nan

    for index, row in df.iterrows():
        # no pattern found
        if len(row[candle_names]) - sum(row[candle_names] == 0) == 0:
            df.loc[index,'candlestick_pattern'] = "NO_PATTERN"
            df.loc[index, 'candlestick_match_count'] = 0
        # single pattern found
        elif len(row[candle_names]) - sum(row[candle_names] == 0) == 1:
            # bull pattern 100 or 200
            if any(row[candle_names].values > 0):
                pattern = list(compress(row[candle_names].keys(), row[candle_names].values != 0))[0] + '_Bull'
                df.loc[index, 'candlestick_pattern'] = pattern
                df.loc[index, 'candlestick_match_count'] = 1
            # bear pattern -100 or -200
            else:
                pattern = list(compress(row[candle_names].keys(), row[candle_names].values != 0))[0] + '_Bear'
                df.loc[index, 'candlestick_pattern'] = pattern
                df.loc[index, 'candlestick_match_count'] = 1
        # multiple patterns matched -- select best performance
        else:
            # filter out pattern names from bool list of values
            patterns = list(compress(row[candle_names].keys(), row[candle_names].values != 0))
            container = []
            for pattern in patterns:
                if row[pattern] > 0:
                    container.append(pattern + '_Bull')
                else:
                    container.append(pattern + '_Bear')
            rank_list = [candle_rankings[p] for p in container]
            if len(rank_list) == len(container):
                rank_index_best = rank_list.index(min(rank_list))
                df.loc[index, 'candlestick_pattern'] = container[rank_index_best]
                df.loc[index, 'candlestick_match_count'] = len(container)


    # clean up candle columns
    try:
        df.drop(candle_names, axis = 1, inplace = True)
    except:
        pass

    df.loc[df.candlestick_pattern == 'NO_PATTERN', 'candlestick_pattern'] = ''
    df.candlestick_pattern = df.candlestick_pattern.apply(lambda x: x[3:])
    return df

def getFullDataCanldes(df):
    return getCanleStickPattrns(df)

def getLatestCanlePattenOnly(df):
    df=getCanleStickPattrns(df,lastndays=30)[-1:]
    print(df["candlestick_pattern"],"candlestick_match_count")

def getStockInAction(type="NIFTY50"):
    stocklist=getData(type)
    dflist=[]
    for k,v in stocklist.items():
        df = getCanleStickPattrns(getDatFrame(v), lastndays=30)[-1:]
        df["Symbol"]=k
        dflist.append(df)
    df=pd.concat(dflist)
    df=df[df["candlestick_match_count"]>0]
    df=df[['Symbol','candlestick_pattern', 'candlestick_match_count','Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    df.columns=['Symbol','Pattern', 'Match_Count','Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    df.to_csv("Temp/FilterStock.csv")
    df=df.sort_values(by="Match_Count",ascending=False)
    dfbull=df[df["Pattern"].str.contains("Bull")]
    dfbull.to_csv("Temp/BullFiltered.csv")
    print("Bull Symbold",dfbull["Symbol"].values)


def Experimnt():
    # Load historical stock data
    df = getData("HDFCBANK")
    # df=getCanleStickPattrns(df,lastndays=30)
    # print(df[-10:][["candlestick_pattern","candlestick_match_count"]])
    # df.to_csv(OUTPUT_FOLDER + 'HDFC.csv')
    getLatestCanlePattenOnly(df)

getStockInAction()