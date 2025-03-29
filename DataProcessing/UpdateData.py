#!/usr/bin/python3
import datetime
# Pyinstaller compile Windows: pyinstaller --onefile --icon=src\icon.ico src\UpdateData.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress --hidden-import chromadb
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=src/icon.ico src/UpdateData.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress --hidden-import chromadb

# Keep module imports prior to classes
import os
import yfinance as yf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import classes.Fetcher as Fetcher
import classes.ConfigManager as ConfigManager
import classes.Screener as Screener
import classes.Utility as Utility
from classes.ParallelProcessing import StockConsumer
from classes.CandlePatterns import CandlePatterns
import argparse,urllib
import numpy as np
import pandas as pd,pickle as pk
import multiprocessing
import classes.Fetcher as Fetcher
import classes.ConfigManager as ConfigManager
from classes.ColorText import colorText
from alive_progress import alive_bar
# os.chdir("../")
from datetime import datetime, date

configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)

multiprocessing.freeze_support()
try:
    import chromadb
    CHROMA_AVAILABLE = True
except:
    CHROMA_AVAILABLE = False

# # Argument Parsing for test purpose
# argParser = argparse.ArgumentParser()
# argParser.add_argument('-t', '--testbuild', action='store_true', help='Run in test-build mode', required=False)
# argParser.add_argument('-d', '--download', action='store_true', help='Only Download Stock data in .pkl file', required=False)
# argParser.add_argument('-v', action='store_true')        # Dummy Arg for pytest -v
# args = argParser.parse_args()

# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"

# Constants
np.seterr(divide='ignore', invalid='ignore')

# Global Variabls
screenCounter = None
screenResultsCounter = None
screenResultsCounter = multiprocessing.Value('i', 0)
stockDict = None
# keyboardInterruptEvent = None
keyboardInterruptEvent = multiprocessing.Manager().Event()
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
    with open("../StockData/AllSTOCKS.pk", "rb") as f:
        FullData=pk.load(f)
    Nodata=0
    for k,v in stockDict.items():
        df=getDatFrame(v)
        df.columns=list(map(lambda x:x[0],df.columns))
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
    with open("../StockData/AllSTOCKS.pk", "wb") as f:
        pk.dump(FullData,f)
    print(f"All Stock Updated {Nodata} Stock with no Data  out of {len(FullData)}")

def DowloadExpacitaly(stockDict,n=-1):
    print(colorText.BOLD + colorText.FAIL + "Downloading data Explacitily" + colorText.END)
    configManager.getConfig(ConfigManager.parser)
    daysForLowestVolume=30
    listStockCodes = fetcher.fetchStockCodes(12, proxyServer=proxyServer)
    if n>0: listStockCodes=listStockCodes[:n]
    items = [(12, 2, None, None, daysForLowestVolume, 0, 100, 1, 7, len(listStockCodes),
              configManager, fetcher, screener, candlePatterns, stock, False, True, vectorSearch,
              None, date.today()) for stock in listStockCodes]
    tasks_queue = multiprocessing.JoinableQueue()
    results_queue = multiprocessing.Queue()
    totalConsumers = multiprocessing.cpu_count()
    consumers = [StockConsumer(tasks_queue, results_queue, screenCounter, screenResultsCounter, stockDict, proxyServer,
                               keyboardInterruptEvent)
                 for _ in range(totalConsumers)]

    for worker in consumers:
        worker.daemon = True
        worker.start()

    for item in items:
        tasks_queue.put(item)
    # Append exit signal for each process indicated by None
    for _ in range(multiprocessing.cpu_count()):
        tasks_queue.put(None)
    try:
        numStocks, totalStocks = len(listStockCodes), len(listStockCodes)
        os.environ['SCREENIPY_TOTAL_STOCKS'] = str(totalStocks)
        print(colorText.END + colorText.BOLD)
        bar, spinner = Utility.tools.getProgressbarStyle()
        with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
            while numStocks:
                result = results_queue.get()
                if result is not None:
                    screenResults = pd.concat([screenResults, pd.DataFrame([result[0]])], ignore_index=True)
                    saveResults = pd.concat([saveResults, pd.DataFrame([result[1]])], ignore_index=True)
                numStocks -= 1
                os.environ['SCREENIPY_SCREEN_COUNTER'] = str(int((totalStocks - numStocks) / totalStocks * 100))
                progressbar.text(
                    colorText.BOLD + colorText.GREEN + f'Found {screenResultsCounter.value} Stocks' + colorText.END)
                progressbar()
    except KeyboardInterrupt:
        try:
            keyboardInterruptEvent.set()
        except KeyboardInterrupt:
            pass
        print(colorText.BOLD + colorText.FAIL +
              "\n[+] Terminating Script, Please wait..." + colorText.END)
        for worker in consumers:
            worker.terminate()
    for worker in consumers:
        try:
            worker.terminate()
        except OSError as e:
            if e.winerror == 5:
                pass
    Utility.tools.saveStockData(stockDict, configManager, len(stockDict))


def updateStockData():
    stockDict = multiprocessing.Manager().dict()
    configManager.getConfig(ConfigManager.parser)
    Utility.tools.loadStockData(stockDict, configManager, proxyServer)
    if len(stockDict)==0:
        DowloadExpacitaly(stockDict)
    UpdateFullStockData(stockDict)
    return stockDict


def upDateIndex(comudityFIle="../StockData/INDEXData/Comudities.csv"):
    if os.path.exists(comudityFIle):
        olddata=pd.read_csv(comudityFIle,index_col=0)
        olddata.index=pd.to_datetime(olddata.index)
        lastdate=olddata.index[-1]
        days=(datetime.now()-lastdate).days
        if days<1: return
        period=str(days)+'d'
    else:
        olddata=None
        period="max"
    niftydata = yf.download(
        tickers="^NSEI",
        period=period,
        interval='1d',
        proxy=proxyServer,
        progress=False,
        timeout=10
    ).rename(columns={k:"NIFTY50_"+k for k in "Open,High,Low,Close,Adj Close,Volume".split(",")})
    gold = yf.download(
        tickers="GC=F",
        period=period,
        interval='1d',
        proxy=proxyServer,
        progress=False,
        timeout=10
    ).add_prefix(prefix='gold_')
    print(gold)
    crude = yf.download(
        tickers="CL=F",
        period=period,
        interval='1d',
        proxy=proxyServer,
        progress=False,
        timeout=10
    ).add_prefix(prefix='crude_')
    # data = pd.concat([niftydata,bankniftydata,sensex, gold, crude], axis=1)
    data = pd.concat([niftydata, gold, crude], axis=1)
    data.columns=data.columns.get_level_values('Price').tolist()
    if olddata is not None:
        data=data[data.index>lastdate]
        data=pd.concat([olddata,data])
    os.makedirs(os.path.dirname(comudityFIle),exist_ok=True)
    data.to_csv(comudityFIle)
    print("Updated Commidity to ",comudityFIle)



def saveIndexStocks():
    nifty50 = fetcher.fetchCodes(1)
    indexlist={"Nifty50":nifty50}
    with open("../StockData/Indexices.pk", "wb") as f:
        pk.dump(indexlist,f)

# Main function
def main():
    # print(fetcher.fetchCodepip install --upgrade yfinances(12))
    # updateStockData()
    upDateIndex()



if __name__ == "__main__":
    # if not configManager.checkConfigFile():
    #     configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    main()
    # getData()
    # saveIndexStocks()
