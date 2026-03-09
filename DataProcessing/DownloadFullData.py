import datetime
import multiprocessing
import urllib

import os
import pandas as pd
import pickle as pk
from alive_progress import alive_bar

import classes.ConfigManager as ConfigManager
import classes.Fetcher as Fetcher
import classes.Screener as Screener
import classes.Utility as Utility
from classes.CandlePatterns import CandlePatterns
from classes.ColorText import colorText
from classes.ParallelProcessing import StockConsumer
from core.paths import project_path
from core.stock_io import split_dict_to_df, df_to_split_dict, load_pickle, dump_pickle


def getDatFrame(stockData):
    return split_dict_to_df(stockData)


def UpdateFullStockData(stockDict, all_data_path=None):
    if all_data_path is None:
        all_data_path = project_path("StockData/AllSTOCKS.pk")
    backup_path = project_path("StockData/AllSTOCKS_back1.pk")

    full_data = load_pickle(backup_path)
    no_data = 0
    for k, v in stockDict.items():
        df = getDatFrame(v)
        if df.shape[0] == 0:
            print(f"No Data for {k}")
            no_data += 1
            continue
        if k not in full_data:
            full_data[k] = df_to_split_dict(df)
            continue
        full_df = getDatFrame(full_data[k])
        full_df = pd.concat([full_df, df[~df.index.isin(full_df.index)]])
        full_data[k] = df_to_split_dict(full_df)
    dump_pickle(all_data_path, full_data)
    print(f"All Stock Updated {no_data} Stock with no Data  out of {len(full_data)}")


def run_download():
    stockDict = multiprocessing.Manager().dict()
    screenCounter = multiprocessing.Value("i", 1)
    screenResultsCounter = multiprocessing.Value("i", 0)
    keyboardInterruptEvent = multiprocessing.Manager().Event()

    try:
        proxyServer = urllib.request.getproxies()["http"]
        print("Proxyserver", proxyServer)
    except KeyError:
        proxyServer = ""

    configManager = ConfigManager.tools()
    fetcher = Fetcher.tools(configManager)
    screener = Screener.tools(configManager)
    candlePatterns = CandlePatterns()
    configManager.getConfig(ConfigManager.parser)

    tasks_queue = multiprocessing.JoinableQueue()
    results_queue = multiprocessing.Queue()
    totalConsumers = multiprocessing.cpu_count()
    if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
        totalConsumers -= 1

    screenResults = pd.DataFrame(
        columns=["Stock", "Consolidating", "Breaking-Out", "LTP", "Volume", "MA-Signal", "RSI", "Trend", "Pattern"]
    )
    saveResults = pd.DataFrame(
        columns=["Stock", "Consolidating", "Breaking-Out", "LTP", "Volume", "MA-Signal", "RSI", "Trend", "Pattern"]
    )

    Utility.tools.loadStockData(stockDict, configManager, proxyServer)
    consumers = [
        StockConsumer(
            tasks_queue,
            results_queue,
            screenCounter,
            screenResultsCounter,
            stockDict,
            proxyServer,
            keyboardInterruptEvent,
        )
        for _ in range(totalConsumers)
    ]
    for worker in consumers:
        worker.daemon = True
        worker.start()

    (
        tickerOption,
        executeOption,
        reversalOption,
        maLength,
        daysForLowestVolume,
        minRSI,
        maxRSI,
        respChartPattern,
        insideBarToLookback,
    ) = (12, 2, None, None, 30, 0, 100, 1, 7)
    newlyListedOnly, downloadOnly, vectorSearch, isDevVersion, backtestDate = (
        False,
        True,
        False,
        None,
        datetime.date.today(),
    )
    listStockCodes = fetcher.fetchStockCodes(tickerOption, proxyServer=proxyServer)
    items = [
        (
            tickerOption,
            executeOption,
            reversalOption,
            maLength,
            daysForLowestVolume,
            minRSI,
            maxRSI,
            respChartPattern,
            insideBarToLookback,
            len(listStockCodes),
            configManager,
            fetcher,
            screener,
            candlePatterns,
            stock,
            newlyListedOnly,
            downloadOnly,
            vectorSearch,
            isDevVersion,
            backtestDate,
        )
        for stock in listStockCodes
    ]

    for item in items:
        tasks_queue.put(item)
    for _ in range(multiprocessing.cpu_count()):
        tasks_queue.put(None)

    try:
        numStocks, totalStocks = len(listStockCodes), len(listStockCodes)
        os.environ["SCREENIPY_TOTAL_STOCKS"] = str(totalStocks)
        print(colorText.END + colorText.BOLD)
        bar, spinner = Utility.tools.getProgressbarStyle()
        with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
            while numStocks:
                result = results_queue.get()
                if result is not None:
                    screenResults = pd.concat([screenResults, pd.DataFrame([result[0]])], ignore_index=True)
                    saveResults = pd.concat([saveResults, pd.DataFrame([result[1]])], ignore_index=True)
                numStocks -= 1
                os.environ["SCREENIPY_SCREEN_COUNTER"] = str(int((totalStocks - numStocks) / totalStocks * 100))
                progressbar.text(colorText.BOLD + colorText.GREEN + f"Found {screenResultsCounter.value} Stocks" + colorText.END)
                progressbar()
    except KeyboardInterrupt:
        try:
            keyboardInterruptEvent.set()
        except KeyboardInterrupt:
            pass
        print(colorText.BOLD + colorText.FAIL + "\n[+] Terminating Script, Please wait..." + colorText.END)
        for worker in consumers:
            worker.terminate()

    UpdateFullStockData(stockDict)


def main():
    run_download()


if __name__ == "__main__":
    main()
