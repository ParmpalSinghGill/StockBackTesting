from enum import Enum, auto
import numpy as np,os
import numpy as np
import pandas as pd
from DataProcessing.DataLoad import getData, getMyStocks
from PlotCode.PlotCandles import PlotSupportAndRessitent
import numpy as np
import scipy as sp
os.chdir("../")
from DataProcessing.DataLoad import getData

period,source=10,'High/Low'
channel_width_percentage=6
def calculate_pivot_Edges( bars):
    src1 = bars["high"]
    src2 = bars["low"]
    pivot_high = (src1 == src1.rolling(period * 2 + 1, center=True).max()).astype(float)
    pivot_low = (src2 == src2.rolling(period * 2 + 1, center=True).min()).astype(float)
    pivot_high = src1 * pivot_high
    pivot_low = src2 * pivot_low
    pivotpoints=pd.Series(np.where(pivot_high > pivot_low, pivot_high, pivot_low), index=pivot_high.index)
    pivotpoints.index=range(pivotpoints.shape[0])
    pivotpoints=pivotpoints[pivotpoints>0]
    return pivotpoints.index,pivotpoints.values


def GetSupportAndRessitent(bars):

    bars.columns=['open', 'high', 'low', 'close', 'Adj Close', 'Volume']
    last300Close = bars.iloc[-300:, bars.columns.get_loc("close")]
    channel_width = (last300Close.max() - last300Close.min()) * channel_width_percentage / 100

    # Define the distance between strong peaks (in days).
    strong_peak_distance = 60
    # Define the prominence (how high the peaks are compared to their surroundings).
    strong_peak_prominence = 20
    # Find the strong peaks in the 'high' price data
    strong_peaks, _ = sp.signal.find_peaks(
      bars['high'],
      distance=strong_peak_distance,
      prominence=strong_peak_prominence
    )
    # strong_peaks,_=calculate_pivot_Edges(bars)

    # Extract the corresponding high values of the strong peaks
    strong_peaks_values = bars.iloc[strong_peaks]["high"].values.tolist()

    # Include the yearly high as an additional strong peak
    yearly_high = bars["high"].iloc[-252:].max()
    strong_peaks_values.append(yearly_high)
    # Define the shorter distance between general peaks (in days)
    # This controls how far apart peaks need to be to be considered separate.
    peak_distance = 10

    # Define the width (vertical distance) where peaks within this range will be grouped together.
    # If the high prices of two peaks are closer than this value, they will be merged into a single resistance level.
    peak_rank_width = channel_width #2

    # Define the threshold for how many times the stock has to reject a level
    # Before it becomes a resistance level
    resistance_min_pivot_rank = 3

    # Find general peaks in the stock's 'high' prices based on the defined distance between them.
    # The peaks variable will store the indices of the high points in the 'high' price data.
    peaks, _ = sp.signal.find_peaks(bars['high'], threshold=peak_distance)

    # Initialize a dictionary to track the rank of each peak
    peak_to_rank = {peak: 0 for peak in peaks}

    # Loop through all general peaks to compare their proximity and rank them
    for i, current_peak in enumerate(peaks):
        # Get the current peak's high price
        current_high = bars.iloc[current_peak]["high"]

        # Compare the current peak with previous peaks to calculate rank based on proximity
        for previous_peak in peaks[:i]:
            if abs(current_high - bars.iloc[previous_peak]["high"]) <= peak_rank_width:
                # Increase rank if the current peak is close to a previous peak
                peak_to_rank[current_peak] += 1
    # Initialize the list of resistance levels with the strong peaks already identified.
    resistances = strong_peaks_values

    # Now, go through each general peak and add it to the resistance list if its rank meets the minimum threshold.
    for peak, rank in peak_to_rank.items():
        # If the peak's rank is greater than or equal to the resistance_min_pivot_rank,
        # it means this peak level has been rejected enough times to be considered a resistance level.
        if rank >= resistance_min_pivot_rank:
            # Append the peak's high price to the resistances list, adding a small offset (1e-3)
            # to avoid floating-point precision issues during the comparison.
            resistances.append(bars.iloc[peak]["high"] + 1e-3)

    # Sort the list of resistance levels so that they are in ascending order.
    resistances.sort()
    # Initialize a list to hold bins of resistance levels that are close to each other.
    resistance_bins = []

    # Start the first bin with the first resistance level.
    current_bin = [resistances[0]]

    # Loop through the sorted resistance levels.
    for r in resistances:
        # If the difference between the current resistance level and the last one in the current bin
        # is smaller than a certain threshold (defined by peak_rank_w_pct), add it to the current bin.
        if r - current_bin[-1] < peak_rank_width:
            current_bin.append(r)
        else:
            # If the current resistance level is far enough from the last one, close the current bin
            # and start a new one.
            resistance_bins.append(current_bin)
            current_bin = [r]

    # Append the last bin.
    resistance_bins.append(current_bin)
    return resistance_bins



bars=getData("SBILIFE")[-300:]
# For each bin, calculate the average of the resistances within that bin.
# This will produce a clean list of resistance levels where nearby peaks have been merged.
resistance_bins=GetSupportAndRessitent(bars)
resistances = [np.mean(bin) for bin in resistance_bins]
print(resistances)
print(resistance_bins)
from PlotCode.PlotCandles import PlotChart
bars.columns=['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
PlotChart(bars, LineS=resistances, Trend="sr1")
