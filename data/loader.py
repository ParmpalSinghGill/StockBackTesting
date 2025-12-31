import pandas as pd
import pickle
import os
from typing import Dict, List, Optional, Union

class DataLoader:
    """
    Handles loading and initial filtering of stock data.
    """
    def __init__(self, data_path: str):
        self.data_path = data_path

    def load_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Loads data from the pickle file.
        
        Args:
            symbols: Optional list of stock symbols to filter.
            
        Returns:
            Dictionary mapping stock symbols to DataFrames.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found at {self.data_path}")

        try:
            with open(self.data_path, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load pickle file: {e}")

        standardized_data = {}

        if isinstance(data, dict):
            for symbol, stock_data in data.items():
                if symbols and symbol not in symbols:
                    continue
                
                # Convert dict to DataFrame if necessary (handling the format from DataLoad.py)
                if isinstance(stock_data, dict) and 'data' in stock_data and 'columns' in stock_data and 'index' in stock_data:
                    try:
                        df = pd.DataFrame(stock_data["data"], columns=stock_data["columns"], index=stock_data["index"])
                    except Exception as e:
                        print(f"Error converting data for {symbol}: {e}")
                        continue
                elif isinstance(stock_data, pd.DataFrame):
                    df = stock_data
                else:
                    # Skip unknown formats or print warning
                    # print(f"Skipping {symbol}: Unknown format {type(stock_data)}")
                    continue

                try:
                    standardized_data[symbol] = self._validate_and_clean(df)
                except Exception as e:
                    # print(f"Error validating data for {symbol}: {e}")
                    continue
        else:
            raise ValueError(f"Unsupported data format: {type(data)}")
            
        return standardized_data

    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensures DataFrame has required columns and correct types.
        """
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check for missing columns (case-insensitive)
        df_cols = {c.lower(): c for c in df.columns}
        rename_map = {}
        for req in required_cols:
            if req.lower() in df_cols:
                rename_map[df_cols[req.lower()]] = req
            else:
                raise ValueError(f"Missing required column: {req}")
        
        df = df.rename(columns=rename_map)
        
        # Ensure Date is index or column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
        
        if not isinstance(df.index, pd.DatetimeIndex):
             # Try to convert index to datetime if it's not already
            try:
                df.index = pd.to_datetime(df.index)
            except:
                raise ValueError("DataFrame index must be DatetimeIndex or 'Date' column must exist.")

        df = df.sort_index()
        
        # Basic cleaning
        df = df[required_cols].astype(float)
        df = df.dropna()
        
        return df
