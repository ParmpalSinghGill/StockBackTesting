import yfinance as yf

import classes.ConfigManager as ConfigManager
import classes.Fetcher as Fetcher
from core.paths import project_path
from core.stock_io import dump_pickle, load_pickle


configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
STOCK_DATA_DIR = project_path("StockData")
STOCK_DATA_DIR.mkdir(parents=True, exist_ok=True)


def DownloadData():
    stockCodes = fetcher.fetchCodes(12)
    append_exchange = ".NS"
    all_stocks_path = project_path("StockData/AllSTOCKS.pk")

    if all_stocks_path.exists():
        AllStockData = load_pickle(all_stocks_path)
    else:
        AllStockData = {}
    print("Already have", len(AllStockData), "Exists")
    try:
        for stockCode in stockCodes:
            if stockCode not in AllStockData:
                print("Downloading", stockCode)
                backtestData = yf.download(
                    tickers=stockCode + append_exchange,
                    interval="1d",
                    progress=False,
                    timeout=10,
                )
                print(f"Downloaded {backtestData.shape[0]} days data for {stockCode}")
                AllStockData[stockCode] = {
                    "data": backtestData.values,
                    "columns": backtestData.columns,
                    "index": backtestData.index,
                }
    except Exception:
        print("Exception")

    dump_pickle(all_stocks_path, AllStockData)


def saveIndexStock():
    nifty50 = fetcher.fetchCodes(1)
    indexlist = {"Nifty50": nifty50}
    dump_pickle(project_path("StockData/Indexices.pk"), indexlist)


def CheckOldIndexData():
    niftydata = yf.download(
        tickers="^NSEI",
        period=str(365 * 40) + "d",
        interval="1d",
        proxy="",
        progress=False,
        timeout=10,
    )
    niftydata.to_csv(project_path("NIFTY.csv"))
    print(niftydata.shape)


def main():
    # saveIndexStock()
    CheckOldIndexData()


if __name__ == "__main__":
    main()
