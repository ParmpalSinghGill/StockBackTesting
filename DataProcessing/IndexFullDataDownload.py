import datetime,os
import yfinance as yf
import pickle as pk
import classes.Fetcher as Fetcher
import classes.ConfigManager as ConfigManager

os.chdir("../")
configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
StockData = "StockData/"
os.makedirs(StockData, exist_ok=True)


def DownloadData():
	stockCodes=fetcher.fetchCodes(12)
	append_exchange = ".NS"

	if os.path.exists(StockData+"AllSTOCKS.pk"):
		with open(StockData+"AllSTOCKS.pk","rb") as f:
			AllStockData=pk.load(f)
	else:
		AllStockData={}
	print("Already have",len(AllStockData),"Exists")
	try:
		for stockCode in stockCodes:
			if stockCode not in AllStockData:
				print("Downloading",stockCode)
				backtestData = yf.download(
					tickers=stockCode + append_exchange,
					interval='1d',
					progress=False,
					timeout=10,
				)
				print(f"Downloaded {backtestData.shape[0]} days data for {stockCode}")
				AllStockData[stockCode]={"data":backtestData.values,"columns":backtestData.columns,"index":backtestData.index}

	except:
		print("Exception")
		pass

	with open(StockData+"AllSTOCKS.pk","wb") as f:
		pk.dump(AllStockData,f)



def saveIndexStock():
	nifty50 = fetcher.fetchCodes(1)
	indexlist={"Nifty50":nifty50}
	with open(StockData+"Indexices.pk","wb") as f:
		pk.dump(indexlist,f)

def CheckOldIndexData():
	niftydata = yf.download(
		tickers="^NSEI",
		period=str(365*40)+"d",
		interval='1d',
		proxy="",
		progress=False,
		timeout=10
	)
	niftydata.to_csv("NIFTY.csv")
	print(niftydata.shape)


# saveIndexStock()
CheckOldIndexData()