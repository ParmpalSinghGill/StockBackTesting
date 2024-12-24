import os,datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import timedelta

os.chdir("../")
from DataProcessing.DataLoad import getData
# data=getData("SBILIFE")
data=getData("HDFCBANK")
data["time"]=pd.to_datetime(data.index)
print(data.shape)
data.columns=['open', 'high', 'low', 'close', 'Adj Close', 'Volume', 'time']
# DateAfter=datetime.datetime.strptime("22-10-15","%y-%m-%d")
# data=data[data.index>=DateAfter]
print(data.shape)

# Input Parameters
timeframe = 'D'  # Higher Time Frame
prd = 10  # Pivot Period
loopback = 290  # Loopback Period
channel_width_pct = 6  # Maximum Channel Width (%)
min_strength = 1  # Minimum Strength
max_num_sr = 6  # Maximum Number of S/R to Show

class SRChannels:
    def __init__(self, period=10, source='High/Low', channel_width_percentage=6, min_strength=1, max_num_sr=6, loopback=290):
        self.period = period
        self.source = source
        self.channel_width_percentage = channel_width_percentage
        self.min_strength = min_strength
        self.max_num_sr = max_num_sr
        self.loopback = loopback
        self.pivot_vals = []
        self.pivot_locs = []
        self.support_resistance = [[0, 0] for _ in range(20)]

    def calculate_pivot_points(self, high, low, close, open_):
        src1 = high if self.source == 'High/Low' else np.maximum(close, open_)
        src2 = low if self.source == 'High/Low' else np.minimum(close, open_)
        pivot_high = (src1 == src1.rolling(self.period * 2 + 1, center=True).max()).astype(float)
        pivot_low = (src2 == src2.rolling(self.period * 2 + 1, center=True).min()).astype(float)
        pivot_high = src1 * pivot_high
        pivot_low = src2 * pivot_low
        return pivot_high, pivot_low

    def get_sr_vals(self, ind):
        lo = self.pivot_vals[ind]
        hi = lo
        num_pp = 0

        for cpp in self.pivot_vals:
            width = abs(cpp - lo) if cpp <= hi else abs(hi - cpp)
            if width <= self.channel_width:
                lo = min(lo, cpp)
                hi = max(hi, cpp)
                num_pp += 20

        return hi, lo, num_pp

    # def process_pivots(self, ph,pl):
    #     if any(ph>0) or any(pl>0):  # If there is a pivot high (ph) or pivot low (pl)
    #         self.pivot_vals=[ for h,l in zip(h,l)]
            # self.pivotvals.insert(0, ph if ph else pl)  # Add the pivot value (ph or pl) at the beginning of the list
            # self.pivotlocs.insert(0, range(self.df.shape[0]))  # Add the current bar_index at the beginning of the list
            #
            # # Loop through the pivotvals and pivotlocs in reverse order
            # for x in range(len(pivotvals) - 1, -1, -1):
            #     # Check if the distance between the current bar and the pivot point is greater than the loopback
            #     if bar_index - pivotlocs[x] > loopback:
            #         pivotvals.pop()  # Remove the oldest pivot value
            #         pivotlocs.pop()  # Remove the corresponding pivot location
            #         continue  # Move to the next pivot
            #     break  # Stop the loop when the condition is not met
            #
    # def process_pivots(self, high, low, close, bar_index):
    #     for ph, pl in zip(high, low):
    #         if ph or pl:
    #             pivot = ph if ph else pl
    #             self.pivot_vals.insert(0, pivot)
    #             self.pivot_locs.insert(0, bar_index)
    #
    #             while len(self.pivot_vals) > 0 and bar_index - self.pivot_locs[-1] > self.loopback:
    #                 self.pivot_vals.pop()
    #                 self.pivot_locs.pop()

    def update_support_resistance(self, high, low, close):
        supres = []
        strengths = [0] * 10

        for ind, _ in enumerate(self.pivot_vals):
            hi, lo, strength = self.get_sr_vals(ind)
            supres.append((strength, hi, lo))

        for ind, (hi, lo, _) in enumerate(supres):
            s = 0
            for i in range(self.loopback):
                if (high[i] <= hi and high[i] >= lo) or (low[i] <= hi and low[i] >= lo):
                    s += 1
            supres[ind] = (supres[ind][0] + s, hi, lo)

        supres.sort(reverse=True, key=lambda x: x[0])

        for i in range(min(self.max_num_sr, len(supres))):
            _, hi, lo = supres[i]
            self.support_resistance[i] = [hi, lo]

    def get_channel_colors(self, close):
        colors = []
        for hi, lo in self.support_resistance[:self.max_num_sr]:
            if hi and lo:
                if close > hi and close > lo:
                    colors.append("Resistance")
                elif close < hi and close < lo:
                    colors.append("Support")
                else:
                    colors.append("Inside Channel")
        return colors

    def check_broken_channels(self, close, close_prev):
        resistance_broken = False
        support_broken = False

        for hi, lo in self.support_resistance[:self.max_num_sr]:
            if hi and lo:
                if close_prev <= hi < close:
                    resistance_broken = True
                if close_prev >= lo > close:
                    support_broken = True

        return resistance_broken, support_broken

    def getSupportAndRessitent(self,df):
        self.df=df
        # Calculate Pivot Points
        last300=df.iloc[-300:, df.columns.get_loc("close")]
        self.channel_width=(last300.max() - last300.min()) * self.channel_width_percentage / 100
        pivot_high, pivot_low = self.calculate_pivot_points(df["high"], df["low"], df["close"], df["open"])
        print(pivot_high[pivot_high>0])
        # Process Pivot Points
        # self.process_pivots(pivot_high, pivot_low)
        # self.process_pivots(pivot_high, pivot_low, df["close"], np.arange(len(df)))
        #
        # # Update Support and Resistance Levels
        # sr.update_support_resistance(df["high"], df["low"], df["close"])
        #
        # # Check Broken Channels
        # close_prev = df["close"].shift(1).fillna(df["close"][0])
        # resistance_broken, support_broken = sr.check_broken_channels(df["close"], close_prev)
        #
        # # Display Results
        # print("Support/Resistance Levels:", sr.support_resistance)
        # print("Resistance Broken:", resistance_broken)
        # print("Support Broken:", support_broken)


# Example Usage
def main():
    # # Sample Data
    # data = {
    #     "open": [1, 1.1, 1.2, 1.3, 1.4, 1.5],
    #     "high": [1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
    #     "low": [0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
    #     "close": [1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
    # }
    # df = pd.DataFrame(data)'
    df=data

    sr = SRChannels()
    sr.getSupportAndRessitent(df)

if __name__ == "__main__":
    main()
