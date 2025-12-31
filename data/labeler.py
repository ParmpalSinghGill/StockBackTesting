import pandas as pd
import numpy as np
from typing import Tuple

class Labeler:
    """
    Generates labels for swing trading based on future price events.
    """
    def __init__(self, target_pct: float, stop_loss_pct: float, holding_period: int,negative_label: int=0):
        self.target_pct = target_pct
        self.stop_loss_pct = stop_loss_pct
        self.holding_period = holding_period
        self.negative_label = negative_label

    def create_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Simulates trades to generate labels.
        
        Labels:
        +1: Target hit before Stop Loss within holding period.
        -1: Stop Loss hit before Target within holding period.
        0: Neither hit (time exit).
        """
        # We need to look ahead, so we iterate or use rolling windows.
        # Iteration is clearer for event-based logic with multiple conditions.
        
        labels = []
        entry_dates = []
        exit_dates = []
        holding_days_list = []
        returns = []
        
        # Pre-calculate price arrays for speed
        opens = df['Open'].values
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        dates = df.index
        
        n = len(df)
        
        for i in range(n):
            # Cannot label the last N days fully if we strictly need N days, 
            # but here we just need to see what happens *within* N days.
            # If i + holding_period >= n, we look until the end of data.
            
            entry_price = closes[i]
            entry_date = dates[i]
            
            target_price = entry_price * (1 + self.target_pct)
            stop_price = entry_price * (1 - self.stop_loss_pct)
            
            outcome = 0
            exit_date = None
            held_days = 0
            exit_price = entry_price # Default to entry if no movement (unlikely)
            
            # Look forward
            end_idx = min(i + 1 + self.holding_period, n)
            
            for j in range(i + 1, end_idx):
                # Check High for target and Low for stop
                # Conservative assumption: Check Low first (Stop Loss) then High (Target) 
                # to avoid optimistic bias on days where both are hit.
                # Or check Open first.
                # Standard practice: If Open is below stop, stopped out immediately.
                # If Open is above target, target hit immediately.
                
                current_open = opens[j]
                current_low = lows[j]
                current_high = highs[j]
                current_close = closes[j]
                current_date = dates[j]
                
                # Gap checks
                if current_open <= stop_price:
                    outcome = self.negative_label
                    exit_date = current_date
                    exit_price = current_open # Stopped at open gap
                    held_days = (current_date - entry_date).days
                    break
                
                if current_open >= target_price:
                    outcome = 1
                    exit_date = current_date
                    exit_price = current_open # Target hit at open gap
                    held_days = (current_date - entry_date).days
                    break
                
                # Intraday checks
                # Check Low against Stop
                if current_low <= stop_price:
                    outcome = self.negative_label
                    exit_date = current_date
                    exit_price = stop_price
                    held_days = (current_date - entry_date).days
                    break
                
                # Check High against Target
                if current_high >= target_price:
                    outcome = 1
                    exit_date = current_date
                    exit_price = target_price
                    held_days = (current_date - entry_date).days
                    break
            
            # If loop finishes without break, it's a time exit (0)
            if outcome == 0:
                if i + 1 < n: # If there is at least one future day
                    # Exit at close of the last day in window
                    last_idx = end_idx - 1
                    if last_idx > i:
                        exit_date = dates[last_idx]
                        exit_price = closes[last_idx]
                        held_days = (exit_date - entry_date).days
                    else:
                         # End of data
                        exit_date = dates[i]
                        exit_price = closes[i]
                        held_days = 0
                else:
                    # No future data
                    exit_date = dates[i]
                    exit_price = closes[i]
                    held_days = 0

            labels.append(outcome)
            entry_dates.append(entry_date)
            exit_dates.append(exit_date)
            holding_days_list.append(held_days)
            returns.append((exit_price - entry_price) / entry_price)
            
        result_df = pd.DataFrame({
            'label': labels,
            'entry_date': entry_dates,
            'exit_date': exit_dates,
            'holding_days': holding_days_list,
            'trade_return': returns
        }, index=df.index)
        
        return result_df
