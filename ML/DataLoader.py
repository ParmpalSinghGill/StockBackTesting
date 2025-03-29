import datetime
import os.path

import pandas as pd
import pickle as pk


BasePath="../StockData/"
EquaityPath=BasePath+"AllSTOCKS.pk"
ComudityPath=BasePath+"INDEXData/Comudities.csv"

class StockDataset():
    def __init__(self, targetstock="HDFCBANK",startdate="2020-01-01",backN=30,datalookup=100,FriendsStoks=[]):
        with open(EquaityPath,"rb") as f:
            stockdata=pk.load(f)
        FriendsStoks.append(targetstock)
        csvdict={k:pd.DataFrame(sd["data"], columns=sd["columns"], index=sd["index"]) for k,sd in stockdata.items() if k in FriendsStoks}
        comdity=pd.read_csv(ComudityPath,index_col="Date")
        csvdict.update({d:comdity[list(filter(lambda x:x.startswith(d),comdity.columns))]  for d in ["NIFTY50","gold","crude"]})
        DiffStockes=sorted(csvdict.keys())
        startdate=datetime.datetime.strptime(startdate,"%Y-%m-%d")
        mindate=startdate-datetime.timedelta(days=backN+datalookup*2)
        for k,v in csvdict.items():
            csvdict[k].columns=[f"{k}_{col}" for col in  csvdict[k].columns]
            csvdict[k].index=pd.to_datetime(csvdict[k].index)
        df=pd.concat([csvdict[c] for c in DiffStockes],axis=1)
        print(df.shape)
        df.to_csv("Data.csv")
        # self.stockData = pd.read_csv(annotations_file)
        # self.img_dir = img_dir
        # self.transform = transform
        # self.target_transform = target_transform

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
        image = read_image(img_path)
        label = self.img_labels.iloc[idx, 1]
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label


data=StockDataset()