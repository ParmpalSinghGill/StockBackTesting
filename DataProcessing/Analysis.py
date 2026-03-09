import sys
sys.path.append(".")

from DataProcessing.DataLoad import getData
import pandas as pd
import numpy as np

def analyze_continuous_uptrend_trades(min_trade_ret=10):
    print("Loading data...")
    all_data = getData()
    if all_data is None:
        print("No data found.")
        return

    results = []

    # Iterate over all tickers
    tickers = list(all_data.keys())
    print(f"Analyzing {len(tickers)} stocks...")

    for ticker in tickers:
        try:
            df = getData(ticker)
            if df is None or df.empty:
                continue
            
            # Ensure we have necessary columns
            if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                continue

            # Convert to numpy for speed
            opens = df['Open'].values
            closes = df['Close'].values
            highs = df['High'].values
            lows = df['Low'].values
            
            n = len(df)
            if n == 0:
                continue

            count = 0
            i = 0
            while i < n:
                # Start of a potential trade at i
                # We extend as long as condition holds:
                # Low[j] >= Low[j-1] AND High[j] >= High[j-1]
                
                j = i + 1
                while j < n:
                    if lows[j] >= lows[j-1] and highs[j] >= highs[j-1]:
                        j += 1
                    else:
                        break
                
                # The sequence is from i to j-1
                # Trade return: (Close[end] - Open[start]) / Open[start]
                # End index is j-1
                
                if j - 1 >= i:
                    trade_ret = (closes[j-1] - opens[i]) / opens[i] * 100
                    if trade_ret > min_trade_ret:
                        count += 1
                
                # Next search starts at j
                # If j == i (which shouldn't happen if we start j=i+1), we force advance
                if j == i:
                    i += 1
                else:
                    i = j
                
            if count > 0:
                results.append({'Stock': ticker, 'TradeCount': count})
                
        except Exception as e:
            # print(f"Error analyzing {ticker}: {e}")
            continue

    results_df = pd.DataFrame(results)
    if results_df.empty:
        return results_df
    return results_df.sort_values(by='TradeCount', ascending=False)


def render_continuous_uptrend_results(results_df: pd.DataFrame):
    if not results_df.empty:
        print(results_df.to_string(index=False))
        print(f"\nTotal Stocks with trades: {len(results_df)}")
        results_df.to_csv("Results/ContinuousUptrendTrades.csv", index=False)
        print("Results saved to Results/ContinuousUptrendTrades.csv")
    else:
        print("No trades found matching criteria.")

def analyze_specific_ticker(ticker,min_trade_ret=10):
    print(f"Analyzing {ticker}...")
    df = getData(ticker)
    if df is None or df.empty:
        print(f"No data found for {ticker}")
        return

    # Ensure we have necessary columns
    if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        print("Missing required columns")
        return

    # Convert to numpy for speed
    opens = df['Open'].values
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    dates = df.index
    
    n = len(df)
    if n == 0:
        print("Empty data")
        return

    trades = []
    i = 0
    while i < n:
        j = i + 1
        while j < n:
            if lows[j] >= lows[j-1] and highs[j] >= highs[j-1]:
                j += 1
            else:
                break
        
        if j - 1 >= i:
            trade_ret = (closes[j-1] - opens[i]) / opens[i] * 100
            if trade_ret > min_trade_ret:
                trades.append({
                    'Start Date': dates[i],
                    'End Date': dates[j-1],
                    'Return %': trade_ret,
                    'Start Price': opens[i],
                    'End Price': closes[j-1]
                })
        
        if j == i:
            i += 1
        else:
            i = j
            
    if trades:
        trades_df = pd.DataFrame(trades)
        print(f"\nTrades for {ticker}:")
        print(trades_df.to_string(index=False))
        print(f"\nTotal Trades: {len(trades)}")
    else:
        print(f"No qualifying trades found for {ticker}")

if __name__ == "__main__":
    analyze_specific_ticker("ARMANFIN",min_trade_ret=30)
    # render_continuous_uptrend_results(analyze_continuous_uptrend_trades())
