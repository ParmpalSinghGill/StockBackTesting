import os
import pickle as pk
import pandas as pd

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
    else:
        return getDatFrame(Fulldata[key])


