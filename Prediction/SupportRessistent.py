from enum import Enum, auto
import numpy as np,os
import numpy as np
import pandas as pd
from DataProcessing.DataLoad import getData
from PlotCode.PlotCandles import PlotSupportAndRessitent
import numpy as np


class Sup_Res_Finder():
    def __init__(self,N=2):
        self.N=N
    # def isSupport(self, df, i):
    #     support = df['Low'][i] < df['Low'][i - 1] and df['Low'][i] < df['Low'][i + 1] \
    #               and df['Low'][i + 1] < df['Low'][i + 2] and df['Low'][i - 1] < df['Low'][i - 2]
    #
    #     return support
    #
    # def isResistance(self, df, i):
    #     resistance = df['High'][i] > df['High'][i - 1] and df['High'][i] > df['High'][i + 1] \
    #                  and df['High'][i + 1] > df['High'][i + 2] and df['High'][i - 1] > df['High'][i - 2]
    #
    #     return resistance

    def isSupport(self, df, i):
        return all([df['Low'][i-j] < df['Low'][i-j-1] and df['Low'][i+j] < df['Low'][i + 1+j]  for j in range(self.N)])

    def isResistance(self, df, i):
        return all([df['High'][i-j] > df['High'][i-j-1] and df['High'][i+j] > df['High'][i + 1+j]  for j in range(self.N)])


    def find_levels(self, df):
        levels = []
        s = np.mean(df['High'] - df['Low'])

        for i in range(self.N, df.shape[0] -self.N):
            if self.isSupport(df, i):
                l = df['Low'][i]
                if np.sum([abs(l - x) < s for x in levels]) == 0:
                    levels.append(l)
            elif self.isResistance(df, i):
                l = df['High'][i]

                if np.sum([abs(l - x) < s for x in levels]) == 0:
                    levels.append(l)
        return levels



if __name__ == '__main__':
    os.chdir("../")
    pl=Sup_Res_Finder(N=2)
    data = getData("HDFCBANK")
    PlotSupportAndRessitent(pl.find_levels,data[-1000:],windowlenght=300)
    # print(pl.find_levels(data.iloc[-200:]))