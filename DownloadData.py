#!/usr/bin/python3

# Pyinstaller compile Windows: pyinstaller --onefile --icon=src\icon.ico src\UpdateData.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress --hidden-import chromadb
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=src/icon.ico src/UpdateData.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress --hidden-import chromadb

# Keep module imports prior to classes
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import classes.Fetcher as Fetcher
import classes.ConfigManager as ConfigManager
import classes.Screener as Screener
import classes.Utility as Utility
from classes.CandlePatterns import CandlePatterns
import argparse
import urllib
import numpy as np
import pandas as pd,pickle as pk
import multiprocessing
import classes.Fetcher as Fetcher
import classes.ConfigManager as ConfigManager

configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)

multiprocessing.freeze_support()
try:
    import chromadb
    CHROMA_AVAILABLE = True
except:
    CHROMA_AVAILABLE = False

# Argument Parsing for test purpose
argParser = argparse.ArgumentParser()
argParser.add_argument('-t', '--testbuild', action='store_true', help='Run in test-build mode', required=False)
argParser.add_argument('-d', '--download', action='store_true', help='Only Download Stock data in .pkl file', required=False)
argParser.add_argument('-v', action='store_true')        # Dummy Arg for pytest -v
args = argParser.parse_args()

# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"

# Constants
np.seterr(divide='ignore', invalid='ignore')

# Global Variabls
screenCounter = None
screenResultsCounter = None
stockDict = None
keyboardInterruptEvent = None
loadedStockData = False
loadCount = 0
maLength = None
newlyListedOnly = False
vectorSearch = False

CHROMADB_PATH = "chromadb_store/"

configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
screener = Screener.tools(configManager)
candlePatterns = CandlePatterns()

# Get system wide proxy for networking
try:
    proxyServer = urllib.request.getproxies()['http']
except KeyError:
    proxyServer = ""

# Clear chromadb store initially
if CHROMA_AVAILABLE:
    chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)
    try:
        chroma_client.delete_collection("nse_stocks")
    except:
        pass


# Manage Execution flow
def getDatFrame(stockData):
    try:
        return pd.DataFrame(stockData["data"],columns=stockData["columns"],index=stockData["index"])
    except Exception as e:
        print(stockData)
        raise e


def UpdateFullStockData(stockDict):
    with open("StockData/AllSTOCKS.pk", "rb") as f:
        FullData=pk.load(f)
    Nodata=0
    for k,v in stockDict.items():
        df=getDatFrame(v)
        if df.shape[0]==0:
            print(f"No Data for {k}")
            Nodata+=1
            continue
        if k not in FullData:
            FullData[k] = {"data":df.values,"columns":df.columns,"index":df.index}
            continue
        fuldatadf=getDatFrame(FullData[k])
        fuldatadf=pd.concat([fuldatadf, df[~df.index.isin(fuldatadf.index)]])
        FullData[k]={"data":fuldatadf.values,"columns":fuldatadf.columns,"index":fuldatadf.index}
    with open("StockData/AllSTOCKS.pk", "wb") as f:
        pk.dump(FullData,f)
    print(f"All Stock Updated {Nodata} Stock with no Data  out of {len(FullData)}")

def getData():
    stockDict = multiprocessing.Manager().dict()
    configManager.getConfig(ConfigManager.parser)
    Utility.tools.loadStockData(stockDict, configManager, proxyServer)
    UpdateFullStockData(stockDict)
    return stockDict


def saveIndexStock():
    nifty50 = fetcher.fetchCodes(1)
    indexlist={"Nifty50":nifty50}
    with open("StockData/Indexices.pk","wb") as f:
        pk.dump(indexlist,f)

# Main function
def main():
    # print(fetcher.fetchCodes(12))
    getData()
    # UpdateFullStockData(stockDict)
    # print(stockDict.keys())
    # print(stockDict["AVROIND"].keys())
    # print(getDatFrame(stockDict["AVROIND"]).shape)



if __name__ == "__main__":
    # if not configManager.checkConfigFile():
    #     configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    # main()
    getData()
    # saveIndexStock()
