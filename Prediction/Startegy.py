import datetime
import os
import random,talib

import numpy as np
import pandas as pd,pickle as pk
import talib
from Prediction.SuperTrend import SuperTrendPrediction
from Prediction import CONFIG


# def MACDPrediciton(df,fastperiod=12,slowperiod=26,signalperiod=9,ndays=4):
# 	_,_,signal=talib.MACD(df["Close"].values,fastperiod=fastperiod,slowperiod=slowperiod,signalperiod=signalperiod)
# 	# print(df.iloc[-1:])
# 	# print(signal[-10:])
# 	if signal[-1]>0:
# 		if np.any(signal[-ndays:]<=0):
# 			return True,"BUY"
# 	else:
# 		if np.any(signal[-ndays:] >= 0):
# 			return True, "SELL"
# 	return False,None


def MACDPrediciton(
    df,
    fastperiod=12,
    slowperiod=26,
    signalperiod=9,
    ndays=4,                 # how many bars back we accept a recent cross
    ema_fast=50,             # structure trend confirmation
    ema_slow=200,            # primary trend filter
    breakout_lookback=3,     # require close > max of last N closes (excl current)
    atr_period=14,           # volatility floor
    min_atr_pct=0.004,       # >= 0.4% of price
    vol_lookback=20,         # volume confirmation window
    vol_mult=1.10,           # today volume must be >= 1.10 * 20SMA
    rsi_period=14,           # optional momentum sanity check
    rsi_buy_range=(48, 68)   # keep longs away from choppy/overbought edges
):
    """
    Returns (bool, 'BUY'/'SELL'/None). Long-only: never emits SELL.

    BUY when (all true):
      - Recent MACD up-cross within last `ndays`
      - Primary trend: Close > EMA200 AND EMA50 > EMA200
      - Short breakout: Close > max(Close[-breakout_lookback-1:-1])
      - Volatility floor: ATR/Close >= min_atr_pct
      - Volume confirmation: Vol >= vol_mult * SMA20(Vol)
      - RSI within rsi_buy_range (optional guard)
    """
    need = max(slowperiod, signalperiod, ema_slow, ema_fast, atr_period, vol_lookback, rsi_period) + ndays + 3
    if len(df) < need:
        return False, None

    close = df["Close"].values.astype(float)
    high  = df.get("High", df["Close"]).values.astype(float)
    low   = df.get("Low",  df["Close"]).values.astype(float)
    vol   = df.get("Volume", np.full_like(close, np.nan, dtype=float)).astype(float)

    macd, macd_signal, _ = talib.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    ema50  = talib.EMA(close, timeperiod=ema_fast)
    ema200 = talib.EMA(close, timeperiod=ema_slow)
    atr    = talib.ATR(high, low, close, timeperiod=atr_period)
    rsi    = talib.RSI(close, timeperiod=rsi_period) if rsi_period else None
    vma20  = talib.SMA(vol, timeperiod=vol_lookback) if np.isfinite(vol).all() else None

    c = close[-1]
    diff = macd - macd_signal
    recent = diff[-ndays-1:]  # include one extra to detect crossing inside window
    up_cross = np.any((recent[:-1] <= 0) & (recent[1:] > 0))

    trend_primary = (c > ema200[-1]) and (ema50[-1] > ema200[-1])
    breakout_ok = c > np.max(close[-(breakout_lookback+1):-1])
    vol_ok = True
    if vma20 is not None and np.isfinite(vma20[-1]) and np.isfinite(vol[-1]):
        vol_ok = vol[-1] >= vol_mult * vma20[-1]
    vol_floor_ok = (atr[-1] / max(c, 1e-9)) >= min_atr_pct
    rsi_ok = True
    if rsi is not None and np.isfinite(rsi[-1]):
        rsi_ok = (rsi_buy_range[0] <= rsi[-1] <= rsi_buy_range[1])

    buy_ok = up_cross and trend_primary and breakout_ok and vol_floor_ok and vol_ok and rsi_ok

    if buy_ok:
        return True, "BUY"

    # Long-only: never force an exit via SELL signal
    return False, None

def MASDEMARSIPrediciton(
		df,
		fastperiod=12, slowperiod=26, signalperiod=9,
		ndays=2,
		ema_fast=50, ema_slow=200,
		breakout_lookback=1,  # BUY: close must take out prior N highs
		atr_period=14, min_atr_pct=0.0035,
		vol_lookback=20, vol_mult=1.05,
		adx_period=14, min_adx=20,  # trend strength
		rsi_period=14, rsi_buy_range=(48, 68),
		max_ext_above_ema50=0.08  # avoid chasing >8% above EMA50
):
	need = max(slowperiod, signalperiod, ema_slow, ema_fast, atr_period,
	           vol_lookback, adx_period, rsi_period) + ndays + 3
	if len(df) < need:
		return False, None

	close = df["Close"].values.astype(float)
	high = df.get("High", df["Close"]).values.astype(float)
	low = df.get("Low", df["Close"]).values.astype(float)
	vol = df.get("Volume", np.full_like(close, np.nan, dtype=float)).astype(float)

	macd, macd_signal, macd_hist = talib.MACD(close, fastperiod, slowperiod, signalperiod)
	ema50 = talib.EMA(close, timeperiod=ema_fast)
	ema200 = talib.EMA(close, timeperiod=ema_slow)
	atr = talib.ATR(high, low, close, timeperiod=atr_period)
	adx = talib.ADX(high, low, close, timeperiod=adx_period)
	rsi = talib.RSI(close, timeperiod=rsi_period)

	c = close[-1]
	diff = macd - macd_signal
	recent = diff[-ndays - 1:]  # for cross detection
	up_cross = np.any((recent[:-1] <= 0) & (recent[1:] > 0))
	down_cross = np.any((recent[:-1] >= 0) & (recent[1:] < 0))

	# ===== BUY quality gates =====
	trend_primary = (c > ema200[-1]) and (ema50[-1] > ema200[-1])
	ema200_slope_up = ema200[-1] > ema200[-5]  # rising base
	breakout_ok = c > np.max(close[-(breakout_lookback + 1):-1])
	vol_floor_ok = (atr[-1] / max(c, 1e-9)) >= min_atr_pct
	vol_ok = True
	if np.isfinite(vol).all():
		vma20 = talib.SMA(vol, timeperiod=vol_lookback)
		if np.isfinite(vma20[-1]):
			vol_ok = vol[-1] >= vol_mult * vma20[-1]
	adx_ok = adx[-1] >= min_adx
	ext = (c - ema50[-1]) / max(ema50[-1], 1e-9)
	not_overextended = (ext >= 0) and (ext <= max_ext_above_ema50)
	rsi_ok = (rsi_buy_range[0] <= rsi[-1] <= rsi_buy_range[1])

	buy_ok = up_cross and trend_primary and ema200_slope_up and breakout_ok \
	         and vol_floor_ok and vol_ok and adx_ok and not_overextended and rsi_ok

	# ===== SELL (exit) conditions — long-only exits, no shorts =====
	# 1) Structure break: close < EMA200 (trend broken)
	trend_break = c < ema200[-1]
	# 2) Momentum roll + structure loss: MACD down-cross AND close < EMA50
	momentum_roll = down_cross and (c < ema50[-1])
	# 3) RSI loses the 50 area (after being >=50 yesterday) -> momentum deterioration
	rsi_cross_down = False
	if len(rsi) >= 2 and np.isfinite(rsi[-1]) and np.isfinite(rsi[-2]):
		rsi_cross_down = (rsi[-2] >= 50) and (rsi[-1] < 45)
	# 4) MACD histogram accelerating negative (extra early exit nudge)
	macd_momentum_down = np.isfinite(macd_hist[-1]) and np.isfinite(macd_hist[-2]) and (macd_hist[-1] < 0) and (
				macd_hist[-1] < macd_hist[-2])

	sell_ok = trend_break or momentum_roll or rsi_cross_down or macd_momentum_down

	# Prioritize exits over entries if both happen on same bar
	if sell_ok:
		return True, "SELL"
	if buy_ok:
		return True, "BUY"
	return False, None

def Random():
	return random.randint(0,10)>8

def getCandleSignal(df):
	print(talib.CDL)


def ShouldBuy(df):
	# return Random()
	print(df)
	getCandleSignal()
	exit()

def RandomPredicition(df):
	if ShouldBuy(df):
		return True,"BUY"
	return False,"BUY"


# def getTargetAndStopLoss(df,signal,side):
# 	if signal and side=="BUY":
# 		currentPrice = df["Close"].values[-1]
# 		stoploss = currentPrice - currentPrice * CONFIG.STOPLOSSPERCENT/100
# 		Target = currentPrice + currentPrice * CONFIG.TARGETPERCENT/100
# 		return currentPrice,stoploss,Target
# 	return df["Close"].values[-1],None,None

def getTargetAndStopLoss(
    df, signal, side,
    atr_period=14,
    atr_sl_mult=1.8,     # ~swing stop: 1.5–2.0×ATR works well
    atr_tp_mult=2.5      # initial swing target; trailing can take over in your BT
):
    """
    On BUY signal:
      StopLoss = Close - atr_sl_mult * ATR
      Target   = Close + atr_tp_mult * ATR
    Otherwise: return (last close, None, None)
    """
    close = df["Close"].values.astype(float)
    if signal and side == "BUY":
        high = df.get("High", df["Close"]).values.astype(float)
        low  = df.get("Low",  df["Close"]).values.astype(float)
        atr  = talib.ATR(high, low, close, timeperiod=atr_period)
        atr_now = float(atr[-1]) if np.isfinite(atr[-1]) else 0.0

        currentPrice = float(close[-1])
        if atr_now <= 0:
            # Fallback to small percent if ATR not available (rare)
            sl = currentPrice * 0.98
            tp = currentPrice * 1.10
        else:
            sl = currentPrice - atr_sl_mult * atr_now
            tp = currentPrice + atr_tp_mult * atr_now

        return currentPrice, sl, tp

    return float(close[-1]), None, None

def MakePrediciton(df):
	# signal,side=RandomPredicition(df)
	# signal,side= MACDPrediciton(df)
	signal,side=MASDEMARSIPrediciton(df)
	# signal,side= SuperTrendPrediction(df)
	currentPrice, stoploss, Target=getTargetAndStopLoss(df,signal,side)
	# if signal and side=="BUY":
	# 	print(f"{side},{currentPrice}, {stoploss}, {Target:.2f},{(Target-currentPrice)/currentPrice*100:.2f}%/{(currentPrice-stoploss)/currentPrice*100:.2f}%")
	return signal,side,currentPrice, stoploss, Target

def getDatFrame(stockData):
    try:
        return pd.DataFrame(stockData["data"],columns=stockData["columns"],index=stockData["index"])
    except Exception as e:
        print(stockData)
        raise e

def getData(key=None):
    with open("StockData/AllSTOCKS.pk", "rb") as f:
        Fulldata=pk.load(f)
    if key is None:
        return Fulldata
    else:
        return getDatFrame(Fulldata[key])

def getPredicitonForDate(df,date):
	date=datetime.datetime.strptime(date,"%Y-%m-%d")
	print(MakePrediciton(df[:date]))


if __name__ == '__main__':
	data=getData("HDFCBANK")
	# print(MakePrediciton(data[:-5]))
	print(getPredicitonForDate(data,"1996-08-14"))