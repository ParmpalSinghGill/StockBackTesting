import pickle as pk


with open("StockData/AllSTOCKS.pk","rb") as f:
    Stocks=pk.load(f)

def truncate(data,n=-180):
    return {'data':data["data"][:n], 'columns':data["columns"], 'index':data["index"][:n]}

print({k:v["data"].shape for k,v in Stocks.items()})
# Stocks={k:truncate(v) for k,v in Stocks.items()}
# Stocks={k:v for k,v in Stocks.items() if v["data"].shape[0]>0}
# print({k:v["data"].shape for k,v in Stocks.items()})

# with open("StockData/AllSTOCKS.pk","wb") as f:
#     pk.dump(Stocks,f)



