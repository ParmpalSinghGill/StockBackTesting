from DataProcessing.DataLoad import getData
import pytrendseries
import pandas as pd
trend = "uptrend"
window = 30
year = 2020

import time
import numpy as np

def detecttrend(
    df_prices, trend: str = "downtrend", limit: int = 5, window: int = 21, **kwargs
) -> pd.DataFrame:
    """It searches for trends on timeseries.
    Parameters:
        df_price (dataframe): timeseries.
        trend    (string):    the desired trend to be analyzed.
        limit    (int):       optional, the minimum value that represents the number of consecutive days (or another period of time) to be considered a trend.
        window   (int):       optional, the maximum period of time to be considered a trend.
    Returns:
        getTrend5 (dataframe): dataframe containing all trends within given window.
    """
    if pd.api.types.is_datetime64_ns_dtype(df_prices.index.dtype) == False:
        df_prices.index = pd.to_datetime(df_prices.index, format=kwargs.get("format"))

    start = time.time()
    df_prices = df_prices.sort_index()
    i = 0
    df_array = df_prices.reset_index().reset_index().values
    prices, date, index = df_array[:, 2], df_array[:, 1], df_array[:, 0]
    getTrend = np.empty([1, 6], dtype=object)

    while True:
        price2 = prices[i]
        price1 = prices[i + 1]
        if trend.lower() == "downtrend" and price1 < price2:
            go_trend = True
        elif trend.lower() == "uptrend" and price1 > price2:
            go_trend = True
        else:
            go_trend = False

        if go_trend:
            trend_df = np.empty([1, 6], dtype=object)
            try:
                found = df_array[i : (i + window)]
            except:
                found = df_array[i:]  # if len(array)<window size
            if trend.lower() == "downtrend":
                min_interval = found[np.where(found[:, 2] > price2)]
            elif trend.lower() == "uptrend":
                min_interval = found[np.where(found[:, 2] < price2)]
            if list(min_interval):
                min_interval = df_array[found[0][0] : min_interval[0][0]]
                if trend.lower() == "downtrend":
                    priceMax = np.max(min_interval[:, 2])
                elif trend.lower() == "uptrend":
                    priceMax = np.min(min_interval[:, 2])
                location_max = min_interval[np.where(min_interval == priceMax)[0], :][0][0]
                found2 = min_interval[np.where(min_interval[:, 0] > location_max)]
                if found2.size == 0:
                    found2 = min_interval
                if trend.lower() == "downtrend":
                    priceMin = np.min(found2[:, 2])
                elif trend.lower() == "uptrend":
                    priceMin = np.max(found2[:, 2])
                date_max = min_interval[np.where(min_interval[:, -1] == priceMax)][0][1]
                date_min = found2[np.where(found2[:, -1] == priceMin)][-1][1]
                location_min = found2[np.where(found2 == priceMin)[0], :][0][0]
            else:  # the first value is maximum or the minimum (uptrend)
                min_interval = found
                if trend.lower() == "downtrend":
                    priceMin = np.min(min_interval[:, 2])
                elif trend.lower() == "uptrend":
                    priceMin = np.max(min_interval[:, 2])
                location_min = min_interval[np.where(min_interval == priceMin)[0], :][
                    0
                ][0]
                if trend.lower() == "downtrend":
                    priceMax = np.max(min_interval[:, 2])  # min_interval[0][-1]
                elif trend.lower() == "uptrend":
                    priceMax = np.min(min_interval[:, 2])  # min_interval[0][-1]
                location_max = min_interval[np.where(min_interval == priceMax)[0], :][0][0]  # min_interval[0][0]
                date_max = min_interval[np.where(min_interval[:, -1] == priceMax)][-1][1]  # min_interval[0][1]
                date_min = min_interval[np.where(min_interval[:, -1] == priceMin)][-1][1]  # min_interval[-1][1]

            trend_df[0, 0] = date_max  # from
            trend_df[0, 1] = date_min  # to
            trend_df[0, 2] = priceMax  # price0
            trend_df[0, 3] = priceMin  # price1
            trend_df[0, 4] = location_max  # index_from
            trend_df[0, 5] = location_min  # index_to

            if trend_df[0, 5] - trend_df[0, 4] >= limit:
                getTrend = np.vstack([getTrend, trend_df])
                i = location_min - 1

        i += 1
        if i >= prices.shape[0] - 1:
            break

    getTrend2 = pd.DataFrame(getTrend)
    getTrend2.columns = ["from", "to", "price0", "price1", "index_from", "index_to"]

    getTrend2["time_span"] = getTrend2["index_to"] - getTrend2["index_from"]
    getTrend2 = getTrend2[getTrend2["time_span"] > 0]
    getTrend2["time_span"] = pd.to_numeric(getTrend2["time_span"])

    if trend == "downtrend":
        getTrend2["drawdown"] = [
            abs(getTrend2["price0"].iloc[x] - getTrend2["price1"].iloc[x])
            / max(getTrend2["price0"].iloc[x], getTrend2["price1"].iloc[x])
            for x in range(getTrend2.shape[0])
        ]
    elif trend == "uptrend":
        getTrend2["drawup"] = [
            abs(getTrend2["price0"].iloc[x] - getTrend2["price1"].iloc[x])
            / min(getTrend2["price0"].iloc[x], getTrend2["price1"].iloc[x])
            for x in range(getTrend2.shape[0])
        ]

    # print("Trends detected in {} secs".format(round((time.time() - start), 2)))
    return getTrend2.sort_values("from")


stockdata = getData("HDFCBANK")[["Close"]]
# filtered_data=stockdata[-132:-4]
filtered_data=stockdata[-132:-20]
# filtered_data=stockdata[-75:-40]
print(filtered_data.index)
# trends_detected = pytrendseries.detecttrend(filtered_data, trend=trend, window=window)
trends_detected = detecttrend(filtered_data, trend=trend, window=window)
print(trends_detected)
pytrendseries.vizplot.plot_trend(filtered_data, trends_detected, trend, year)