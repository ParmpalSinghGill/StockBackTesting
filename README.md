# StockBackTesting
A simple project for backtesting the Traiding Startegy 

Install depencieis

`conda env install -f env.yml`

Download full back Data of all stock list in NSE InDia

`python FullDataDownload.py`

You need to run the [FullDataDownload.py](FullDataDownload.py) only once then you can run the [UpdateData.py](UpdateData.py) daily basis to update the stock data by

`python UpdateData.py`

You can edit the MakePrediciton in [Startegy.py](Startegy.py) file to run code on your startegy and run

`python BackTesting.py`


