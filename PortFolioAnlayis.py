import pandas as pd
from DataProcessing.DataLoad import getData


def price_level_story(
    df: pd.DataFrame,
    price_col="Close",
    near_pct=0.02
):
    """
    df:
      - DateTimeIndex
      - OHLC columns
    returns:
      - human-readable analysis string
    """

    df = df.sort_index()
    price = df[price_col].iloc[-1]
    last_date = df.index[-1]

    story = []
    
    # Track the highest timeframe found for each condition
    found_high_tf = None
    found_low_tf = None

    def check_window(days=None):
        if days:
            start = last_date - pd.Timedelta(days=days)
            temp = df.loc[df.index >= start]
        else:
            temp = df

        if temp.empty:
            return None, None

        high = temp["High"].max() if "High" in temp.columns else temp[price_col].max()
        low = temp["Low"].min() if "Low" in temp.columns else temp[price_col].min()

        dist_high = (high - price) / high
        dist_low = (price - low) / low
        
        is_high = dist_high <= near_pct
        is_low = dist_low <= near_pct
        
        return is_high, is_low

    # Higher-timeframe first (important for clean narratives)
    checks = [
        ("all-time", None),
        ("5-year", 1825),
        ("3-year", 1095),
        ("52-week", 365),
        ("6-month", 180),
        ("3-month", 90),
        ("1-month", 30),
    ]

    for label, days in checks:
        is_high, is_low = check_window(days)
        
        if is_high and not found_high_tf:
            found_high_tf = label
        
        if is_low and not found_low_tf:
            found_low_tf = label
            
        # If we found both, we can stop checking (optimization)
        if found_high_tf and found_low_tf:
            break

    # --- Narrative synthesis ---
    if found_high_tf:
        story.append(
            f"Price is trading near its {found_high_tf} high, indicating strong upward momentum."
        )

    if found_low_tf:
        story.append(
            f"Price is hovering near its {found_low_tf} low, suggesting a potential accumulation or risk zone."
        )

    if not story:
        story.append(
            "Price is trading away from major highs and lows, indicating a neutral or range-bound phase."
        )
        details = []
        for label, days in checks:
            if days:
                start = last_date - pd.Timedelta(days=days)
                temp = df.loc[df.index >= start]
            else:
                temp = df
            
            if not temp.empty:
                h = temp["High"].max() if "High" in temp.columns else temp[price_col].max()
                l = temp["Low"].min() if "Low" in temp.columns else temp[price_col].min()
                d_h = (price - h) / h * 100
                d_l = (price - l) / l * 100
                details.append(f"{label}: {d_h:.1f}%H / {d_l:.1f}%L")
        
        if details:
            story.append("Range Details: [" + ", ".join(details) + "]")

    all_time_high = df["High"].max() if "High" in df.columns else df[price_col].max()
    all_time_low = df["Low"].min() if "Low" in df.columns else df[price_col].min()
    diff_ath = (price - all_time_high) / all_time_high * 100
    diff_atl = (price - all_time_low) / all_time_low * 100
    
    story.append(f"It is {diff_ath:.2f}% from its all-time high and {diff_atl:.2f}% from its all-time low.")

    return " ".join(story)



def AllPortfolioStocksData():
    df=pd.read_excel("PortFolio/Stocks_Holdings_Statement_5364437922_30-12-2025.xlsx",skiprows=10)
    # print(getData().keys())
    stockNames=df["Stock Name"].values
    pfDict={}
    for sn in stockNames:
        df=getData(sn)
        if df is None:
            print(f"Key {sn} not found")
        else:
            pfDict[sn]=df
    df=pd.read_csv("PortFolio/holdings.csv")
    for sn in df["Instrument"].values:
        df=getData(sn)
        if df is None:
            print(f"Key {sn} not found")
        else:
            pfDict[sn]=df
            
    return pfDict


def Analysis():
    for sname,df in AllPortfolioStocksData().items():
        # print(sname,df.shape)
        print("*"*150)
        print(sname,price_level_story(df))

Analysis()



