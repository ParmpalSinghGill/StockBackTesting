import os,time
import pickle
import pickle as pk
import pandas as pd

os.makedirs("StockData/INDEX", exist_ok=True)

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

os.makedirs("Results", exist_ok=True)
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
    elif key in Fulldata:
        return getDatFrame(Fulldata[key])
    else:
        IndexPath=f"StockData/INDEX/{key}.pk"
        if not os.path.exists(IndexPath) or (time.time() - os.path.getmtime(IndexPath)) > 2629800: # ~30.4 days
            symbollist=pd.read_csv(tickerMapping[key])["Symbol"].values
            with open(IndexPath,"wb") as f:
                pickle.dump(symbollist,f)
        with open(IndexPath,"rb") as f:
            symbollist=pickle.load(f)
        return {k:v for k,v in Fulldata.items() if k in symbollist}




def getMyStocks():
    with open("DataProcessing/MyStock") as f:
        data=[d[:-1] for d in f.readlines()]
    return data

