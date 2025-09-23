# StockBackTesting
A simple project for backtesting the Traiding Startegy 

Install depencieis

`conda env install -f env.yml`

Download full back Data of all stock list in NSE InDia

`python FullDataDownload.py`

You need to run the [FullDataDownload.py](DataProcessing/FullDataDownload.py) only once then you can run the [UpdateHistoryData.py](UpdateData.py) daily basis to update the stock data by

`python UpdateHistoryData.py`

You can edit the MakePrediciton in [Startegy.py](Prediction/Startegy.py) file to run code on your startegy and run

`python BackTesting.py`

## Info
Old Nifty data can be download from
https://www.niftyindices.com/reports/historical-data

