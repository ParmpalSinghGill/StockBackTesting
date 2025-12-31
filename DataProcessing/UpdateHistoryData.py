#!/usr/bin/python3
import datetime
# Pyinstaller compile Windows: pyinstaller --onefile --icon=src\icon.ico src\UpdateHistoryData.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress --hidden-import chromadb
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=src/icon.ico src/UpdateHistoryData.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive-progress --hidden-import chromadb

# Keep module imports prior to classes
import yfinance as yf
import time
# from yfinance.shared import YFRateLimitError
import os,sys
import yfinance as yf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
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


def _path_from_root(relative_path: str) -> str:
    return os.path.join(PROJECT_ROOT, relative_path)

def getFullData(stockCode,append_exchange = ".NS"):
        return  yf.download(
        tickers=stockCode + append_exchange,
        interval='1d',
        progress=False,
        timeout=10,
				)
    # return  yf.download(
	# 	tickers=tickers,
	# 	period=str(365*50)+"d",
	# 	interval='1d',
	# 	proxy="",
	# 	progress=False,
	# 	timeout=10
	# )



def UpdateFullStockData(stockDict):
    with open(_path_from_root("StockData/AllSTOCKS.pk"), "rb") as f:
        FullData=pk.load(f)
    Nodata=0
    i,total=0,len(stockDict)
    for k,v in stockDict.items():
        # try:    
        df=getDatFrame(v)
        df.columns=list(map(lambda x:x[0],df.columns))
        if df.shape[0]==0:
            print(f"No Data for {k}")
            Nodata+=1
            continue
        if FullData[k]["data"].shape[0]==0 or k not in FullData:
            print(f"{i}/{total} Data missing for  {k:10} so redownloading....")
            newfulldf=getFullData(k)
            FullData[k]={"data":newfulldf.values,"columns":list(map(lambda x:x[0],newfulldf.columns)),"index":newfulldf.index}            
        else:
            fuldatadf=getDatFrame(FullData[k])
            lastindex=fuldatadf.index[-1]
            if lastindex in df.index and (abs(fuldatadf.loc[lastindex,"Close"]-df.loc[lastindex,"Close"])/fuldatadf.loc[lastindex,"Close"]<0.01):
                fuldatadf=pd.concat([fuldatadf, df[~df.index.isin(fuldatadf.index)]])
                FullData[k]={"data":fuldatadf.values,"columns":fuldatadf.columns,"index":fuldatadf.index}
            else:
                print(f"{i}/{total} Seems Difference in {k:10} Price change from {fuldatadf.loc[lastindex,"Close"]:.2f}  to {df.loc[lastindex,"Close"] if lastindex in df.index else 0:.2f} so redownloading....")
                newfulldf=getFullData(k)
                FullData[k]={"data":newfulldf.values,"columns":list(map(lambda x:x[0],newfulldf.columns)),"index":newfulldf.index}
        i=i+1
        # except Exception as e:
        #     print(f"Error in {k} {e}")
        #     print(fuldatadf.shape,df.shape)
        #     raise e
    with open(_path_from_root("StockData/AllSTOCKS.pk"), "wb") as f:
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

def FillMissingComudintes(df):
    for col in ['NIFTY50_Open', 'NIFTY50_High', 'NIFTY50_Low', 'NIFTY50_Close']:
        df[col] = df[col].fillna(df['NIFTY50_Close'].shift())  # fill any remaining with previous close
    for col in ['gold_Open', 'gold_High', 'gold_Low', 'gold_Close']:
        df[col] = df[col].fillna(df['gold_Close'].shift())  # fill any remaining with previous close
    for col in ['crude_Open', 'crude_High', 'crude_Low', 'crude_Close']:
        df[col] = df[col].fillna(df['crude_Close'].shift())  # fill any remaining with previous close
    for col in ['NIFTY50_Volume', 'gold_Volume', 'crude_Volume']:
        df[col] = df[col].fillna(df[col].rolling(window=10, min_periods=1).mean())
        df[col]=df[col].fillna(0)
        df[col]=df[col].astype(int)
    return df

def download_with_retry(ticker, period, interval='1d', proxy=None, max_retries=20, initial_delay=5):
    """
    Downloads ticker data with a retry mechanism for rate limit errors.
    """
    retries = 0
    while retries < max_retries:
        try:
            print(f"Attempting to download {ticker}... (Attempt {retries + 1}/{max_retries})")
            data = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                proxy=proxy,
                progress=False,
                timeout=30
            )
            # Add a small delay between successful downloads to avoid hitting the rate limit
            time.sleep(1) 
            return data
        except Exception as e:
            delay = initial_delay * (2 ** retries)
            print(f"Rate limit hit for {ticker}. Retrying in {delay} seconds...")
            time.sleep(delay)
            retries += 1
        # except Exception as e:
        #     print(f"An unexpected error occurred for {ticker}: {e}")
        #     break
            
    print(f"Failed to download {ticker} after {max_retries} retries.")
    return None

def upDateIndex(comudityFIle: str | None = None):
    if comudityFIle is None:
        comudityFIle = _path_from_root("StockData/INDEXData/Comudities.csv")
    elif not os.path.isabs(comudityFIle):
        comudityFIle = _path_from_root(comudityFIle)

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


    niftydata = download_with_retry(
        ticker="^NSEI",
        period=period,
        proxy=proxyServer
    )
    if niftydata is not None:
        niftydata = niftydata.rename(columns={k: "NIFTY50_" + k for k in "Open,High,Low,Close,Adj Close,Volume".split(",")})


    gold = download_with_retry(
        ticker="GC=F",
        period=period,
        proxy=proxyServer
    )
    if gold is not None:
        gold = gold.add_prefix(prefix='gold_')
    crude = download_with_retry(
        ticker="CL=F",
        period=period,
        proxy=proxyServer
    )
    if crude is not None:
        crude = crude.add_prefix(prefix='crude_')
    # data = pd.concat([niftydata,bankniftydata,sensex, gold, crude], axis=1)
    data = pd.concat([niftydata, gold, crude], axis=1)
    data.to_csv("Comidity.csv")
    data.columns=data.columns.get_level_values('Price').tolist()
    if olddata is not None:
        data=data[data.index>lastdate]
        data=pd.concat([olddata,data])
    os.makedirs(os.path.dirname(comudityFIle),exist_ok=True)
    data=FillMissingComudintes(data)
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
    updateStockData()
    # upDateIndex()



if __name__ == "__main__":
    # if not configManager.checkConfigFile():
    #     configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    main()
