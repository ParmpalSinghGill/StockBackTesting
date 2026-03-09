import os,time
import difflib
import pickle as pk
import pandas as pd
from core.paths import project_path
from core.stock_io import split_dict_to_df, load_pickle, dump_pickle

INDEX_DIR = project_path("StockData/INDEX")
INDEX_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR = project_path("Results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

AllStocks=None
ComditiyDict=None

tickerMapping = {
    "NIFTY50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    2: "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    3: "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    4: "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
    5: "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    6: "https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
    7: "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
    8: "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
    9: "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
    10: "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    11: "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    14: "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
}

def getDatFrame(stockData):
    return split_dict_to_df(stockData)

def readFile(path):
    return load_pickle(project_path(path))
            

def getTickerFromName(name):
    global ComditiyDict
    if ComditiyDict is None:
        ComditiyDict=pd.read_csv(project_path("StockData/EQUITY_L.csv"))
        ComditiyDict={row["NAME OF COMPANY"].lower():row["SYMBOL"] for i,row in ComditiyDict.iterrows()}
    name=name.lower().replace("ltd","limited")
    expcase={"adani port & sez limited":"ADANIPORTS"}
    if name in expcase:
        return expcase[name]
    matches = difflib.get_close_matches(name, ComditiyDict.keys(), n=1, cutoff=0.6)
    if matches:
        return ComditiyDict[matches[0]]
    return None


def getData(key=None):
    global AllStocks,ComditiyDict
    if AllStocks is None:
        AllStocks=readFile("StockData/AllSTOCKS.pk")
    if key is None:
        return AllStocks
    elif key in AllStocks:
        return getDatFrame(AllStocks[key])
    elif key in ['NIFTY50', 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14]:
        IndexPath=project_path(f"StockData/INDEX/{key}.pk")
        if (not IndexPath.exists()) or (time.time() - IndexPath.stat().st_mtime) > 2629800: # ~30.4 days
            symbollist=pd.read_csv(tickerMapping[key])["Symbol"].values
            dump_pickle(IndexPath, symbollist)
        symbollist=load_pickle(IndexPath)
        return {k:v for k,v in AllStocks.items() if k in symbollist}
    else:
        if ComditiyDict is None:
            ComditiyDict=pd.read_csv(project_path("StockData/EQUITY_L.csv"))
            ComditiyDict={row["NAME OF COMPANY"].lower():row["SYMBOL"] for i,row in ComditiyDict.iterrows()}
        if key.lower() in ComditiyDict:
            return getDatFrame(AllStocks[ComditiyDict[key.lower()]])            
        else:
            ticker = getTickerFromName(key)
            if ticker:
                # print(f"Ticker found for {key} : {ticker}")
                if ticker in AllStocks:
                    return getDatFrame(AllStocks[ticker])
            # print(f"Key {key} not found")
            return None




def getMyStocks():
    with open(project_path("DataProcessing/MyStock")) as f:
        data=[d[:-1] for d in f.readlines()]
    return data

