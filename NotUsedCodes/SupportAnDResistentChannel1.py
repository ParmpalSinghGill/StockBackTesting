import os,datetime
import numpy as np
import pandas as pd
from PlotCode.PlotCandles import PlotChart

os.chdir("../")
from DataProcessing.DataLoad import getData


class SRChannels:
    def __init__(self, period=10, source='High/Low', channel_width_percentage=6, min_strength=1, max_num_sr=6, loopback=290):
        self.period = period
        self.source = source
        self.channel_width_percentage = channel_width_percentage
        self.min_strength = min_strength
        self.max_num_sr = max_num_sr
        self.loopback = loopback-1
        self.calculationDays=300


    def ForwarFillPivots(self, pivot_high, pivot_low):
        pivot_high,pivot_low=pivot_high.iloc[:-self.period+1],pivot_low.iloc[:-self.period+1]
        pivot = pivot_high.where(pivot_high != 0, pivot_low)
        pivot=pivot.reset_index(drop=True)
        pivot=pivot[pivot>0]
        pivotebeforlopback=pivot[pivot.index > (pivot.index[-1] - self.loopback)].values[::-1]
        seen = set()
        return [x for x in pivotebeforlopback if not (x in seen or seen.add(x))] # remove dupli

    def calculate_pivot_points(self, high, low, close, open_):
        src1 = high if self.source == 'High/Low' else np.maximum(close, open_)
        src2 = low if self.source == 'High/Low' else np.minimum(close, open_)
        pivot_high = (src1 == src1.rolling(self.period * 2 + 1, center=True).max()).astype(float)
        pivot_low = (src2 == src2.rolling(self.period * 2 + 1, center=True).min()).astype(float)
        pivot_high = src1 * pivot_high
        pivot_low = src2 * pivot_low
        return self.ForwarFillPivots(pivot_high, pivot_low)

    def get_SR_vals(self, lo, pivot_vals):
        hi = lo
        num_pp = 0
        for cpp in pivot_vals:
            width = abs(hi - cpp) if cpp <= hi else abs(cpp - lo)
            if width <= self.channel_width:
                lo = min(lo, cpp)
                hi = max(hi, cpp)
                num_pp += self.period*2
        for y in range(self.loopback):
            row=self.df.iloc[-y-1]
            if (row["High"] <= hi and row["High"] >= lo) or (row["Low"] <= hi and row["Low"] >= lo):
                num_pp += 1
        return [num_pp,hi, lo]

    def changeit(self,x, y, suportresistance):
        # Get and swap  pair of elements
        tmp = suportresistance[y]
        suportresistance[y] = suportresistance[x]
        suportresistance[x] = tmp


    def getStrongSupportAndRessitent(self,pivotvals,supres):
        supportandRessitent,stren=[],[]
        src = 0
        for x in range(len(pivotvals)):
            stv=-1
            stl=-1
            for y,sup in enumerate(supres):
                if sup[0]>stv and sup[0]>=self.min_strength*self.period*2:
                    stv,stl=sup[0],y
            if stl >= 0:
                # get sr level
                hh = supres[stl][1]
                ll = supres[stl][2]
                supportandRessitent.append([hh,ll])
                stren.append(supres[stl][0])

                for sp in supres:
                    if sp[1]<=hh and sp[1]>=ll or sp[2]<=hh and sp[2]>=ll:
                        sp[0]=-1
                src += 1
                if src >= 10:break

        for x in range(len(stren)-1):
            for y in range(x+1,len(stren)):
                if stren[y] > stren[x]:
                    stren[y]=stren[x]
                    self.changeit(x,y,supportandRessitent)
        return supportandRessitent

    def getSupportAndRessitent(self,fulldf,nDays=0):
        self.df=fulldf
        self.df[-self.calculationDays:]
        # get Channel width with high low of last year
        self.channel_width=(self.df.iloc[-300:, self.df.columns.get_loc("High")].max() - self.df.iloc[-300:, self.df.columns.get_loc("Low")].min()) * self.channel_width_percentage / 100
        # Calculate Pivot Points
        pivotvals = self.calculate_pivot_points(self.df["High"], self.df["Low"], self.df["Close"], self.df["Open"])
        # print(pivotvals)
        sandr=[self.get_SR_vals(x, pivotvals) for x in pivotvals]
        # print(sandr)
        supres=self.getStrongSupportAndRessitent(pivotvals,sandr)
        # print(len(supres),supres)
        supres=supres[:self.max_num_sr]
        return supres



# Example Usage
def main():
    # Input Parameters
    timeframe = 'D'  # Higher Time Frame
    prd = 10  # Pivot Period
    loopback = 290  # 290  # Loopback Period
    channel_width_pct = 6  # Maximum Channel Width (%)
    min_strength = 1  # Minimum Strength
    max_num_sr = 6  # Maximum Number of S/R to Show

    # data=getData("SBILIFE")
    data=getData("HINDUNILVR")
    # data = getData("HDFCBANK")
    # data = getData("HYUNDAI")
    # data["time"] = pd.to_datetime(data.index)
    # data.columns = ['open', 'high', 'low', 'close', 'Adj Close', 'Volume', 'time']
    # DateAfter=datetime.datetime.strptime("22-10-15","%y-%m-%d")
    # data=data[data.index>=DateAfter]
    print(data.shape)

    df=data
    sr = SRChannels(period=prd,channel_width_percentage=channel_width_pct,min_strength=min_strength,max_num_sr=max_num_sr,loopback=loopback)
    spandr=sr.getSupportAndRessitent(df)
    PlotChart(df[-150:],Trend="S&R",Bars=spandr)

if __name__ == "__main__":
    main()

