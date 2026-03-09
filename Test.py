import pickle as pk

fpath="StockData/INDEX/NIFTY50.pk"

with open(fpath,"rb") as f:
    stocks=pk.load(f)

print('["','","'.join(stocks),'"]')

