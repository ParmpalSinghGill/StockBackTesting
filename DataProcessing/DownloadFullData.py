import datetime,pickle as pk
import multiprocessing,urllib
import classes.ConfigManager as ConfigManager
from classes.CandlePatterns import CandlePatterns
from classes.ParallelProcessing import StockConsumer
import classes.Utility as Utility
import classes.Screener as Screener
import classes.Fetcher as Fetcher
import os,pandas as pd
from classes.ColorText import colorText
from alive_progress import alive_bar

def getDatFrame(stockData):
    try:
        if len(stockData["columns"][0])==2:
            stockData["columns"]=list(map(lambda x:x[0],stockData["columns"]))
        return pd.DataFrame(stockData["data"],columns=stockData["columns"],index=stockData["index"])
    except Exception as e:
        print(stockData)
        raise e


def UpdateFullStockData(stockDict,AllDataPath="StockData/AllSTOCKS.pk"):
    # with open(AllDataPath, "rb") as f:
    #     FullData=pk.load(f)
    with open("StockData/AllSTOCKS_back1.pk", "rb") as f:
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
    with open(AllDataPath, "wb") as f:
        pk.dump(FullData,f)
    print(f"All Stock Updated {Nodata} Stock with no Data  out of {len(FullData)}")



# Global Variabls
stockDict = multiprocessing.Manager().dict()
loadedStockData = False
loadCount = 0
maLength = None
newlyListedOnly = False
vectorSearch = False
# Get system wide proxy for networking
try:
    proxyServer = urllib.request.getproxies()['http']
    print("Proxyserver",proxyServer)
except KeyError:
    proxyServer = ""

screenCounter = multiprocessing.Value('i', 1)
screenResultsCounter = multiprocessing.Value('i', 0)
keyboardInterruptEvent = multiprocessing.Manager().Event()


configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
screener = Screener.tools(configManager)
candlePatterns=CandlePatterns()
configManager.getConfig(ConfigManager.parser)
tasks_queue = multiprocessing.JoinableQueue()
results_queue = multiprocessing.Queue()
totalConsumers = multiprocessing.cpu_count()

screenResults = pd.DataFrame(columns=[
    'Stock', 'Consolidating', 'Breaking-Out', 'LTP', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern'])
saveResults = pd.DataFrame(columns=[
    'Stock', 'Consolidating', 'Breaking-Out', 'LTP', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern'])

if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
    totalConsumers -= 1
Utility.tools.loadStockData(stockDict, configManager, proxyServer)
consumers = [StockConsumer(tasks_queue, results_queue, screenCounter, screenResultsCounter, stockDict, proxyServer,
                           keyboardInterruptEvent) for _ in range(totalConsumers)]

for worker in consumers:
    worker.daemon = True
    worker.start()
tickerOption, executeOption, reversalOption, maLength, daysForLowestVolume, minRSI, maxRSI, respChartPattern, insideBarToLookback, =12,2,None,None,30,0,100,1,7
newlyListedOnly, downloadOnly, vectorSearch, isDevVersion, backtestDate=False,True,False,None,datetime.date.today()
listStockCodes = fetcher.fetchStockCodes(tickerOption, proxyServer=proxyServer)
items = [(tickerOption, executeOption, reversalOption, maLength, daysForLowestVolume, minRSI, maxRSI, respChartPattern,insideBarToLookback, len(listStockCodes),
          configManager, fetcher, screener, candlePatterns, stock, newlyListedOnly, downloadOnly, vectorSearch,isDevVersion, backtestDate)
         for stock in listStockCodes]

for item in items:
    tasks_queue.put(item)
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
            progressbar.text(colorText.BOLD + colorText.GREEN +
                             f'Found {screenResultsCounter.value} Stocks' + colorText.END)
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

# with open("StocksS.pk","wb") as f:
#     pk.dump(stockDict,f)

# with open("/media/parmpal/Data/Codes/MyCodes/StockS/StockBackTesting/StocksS.pk","rb") as f:
#     stockDict=pk.load(f)

UpdateFullStockData(stockDict)