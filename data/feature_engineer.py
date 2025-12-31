import pandas as pd
import numpy as np
import yaml
from typing import Dict, List, Any

class FeatureEngineer:
    """
    Computes technical indicators based on configuration.
    """
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.indicators = self.config.get('indicators', [])

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates features for a single stock DataFrame.
        """
        df = df.copy()
        features = pd.DataFrame(index=df.index)
        
        # Basic columns
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        for ind in self.indicators:
            name = ind['name']
            params = ind.get('params', {})
            
            if name == "Returns":
                for w in params.get('windows', [1]):
                    features[f'Return_{w}d'] = close.pct_change(w)
            
            elif name == "LogReturns":
                for w in params.get('windows', [1]):
                    features[f'LogReturn_{w}d'] = np.log(close / close.shift(w))

            elif name == "VolumeChange":
                for w in params.get('windows', [1]):
                    features[f'VolumeChange_{w}d'] = volume.pct_change(w)

            elif name == "OBV":
                # On-Balance Volume
                change = close.diff()
                direction = np.where(change > 0, 1, -1)
                direction[change == 0] = 0
                features['OBV'] = (volume * direction).cumsum()

            elif name == "VWMA":
                for w in params.get('windows', [20]):
                    vwma = (close * volume).rolling(window=w).sum() / volume.rolling(window=w).sum()
                    features[f'VWMA_{w}'] = vwma

            elif name == "SMA":
                for w in params.get('windows', [20]):
                    features[f'SMA_{w}'] = close.rolling(window=w).mean()
                    # Normalize SMA by Close to make it stationary-ish
                    features[f'SMA_{w}_Dist'] = (close - features[f'SMA_{w}']) / features[f'SMA_{w}']

            elif name == "EMA":
                for w in params.get('windows', [20]):
                    features[f'EMA_{w}'] = close.ewm(span=w, adjust=False).mean()
                    features[f'EMA_{w}_Dist'] = (close - features[f'EMA_{w}']) / features[f'EMA_{w}']

            elif name == "SMA_Slope":
                for w in params.get('windows', [20]):
                    # Simple slope: change in SMA over window
                    sma = close.rolling(window=w).mean()
                    features[f'SMA_{w}_Slope'] = (sma - sma.shift(1)) / sma.shift(1)

            elif name == "RSI":
                w = params.get('window', 14)
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=w).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=w).mean()
                rs = gain / loss
                features[f'RSI_{w}'] = 100 - (100 / (1 + rs))

            elif name == "ROC":
                for w in params.get('windows', [10]):
                    features[f'ROC_{w}'] = (close - close.shift(w)) / close.shift(w)

            elif name == "ATR":
                w = params.get('window', 14)
                tr1 = high - low
                tr2 = abs(high - close.shift(1))
                tr3 = abs(low - close.shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                features[f'ATR_{w}'] = tr.rolling(window=w).mean()
                # Normalize ATR by price
                features[f'ATR_{w}_Pct'] = features[f'ATR_{w}'] / close

            elif name == "RollingStd":
                for w in params.get('windows', [20]):
                    features[f'Std_{w}'] = close.rolling(window=w).std() / close

            elif name == "BB_Width":
                w = params.get('window', 20)
                std = params.get('std_dev', 2)
                sma = close.rolling(window=w).mean()
                rolling_std = close.rolling(window=w).std()
                upper = sma + (rolling_std * std)
                lower = sma - (rolling_std * std)
                features[f'BB_Width_{w}'] = (upper - lower) / sma

            elif name == "ZScore":
                for w in params.get('windows', [20]):
                    mean = close.rolling(window=w).mean()
                    std = close.rolling(window=w).std()
                    features[f'ZScore_{w}'] = (close - mean) / std

        # Replace infinite values with NaN and forward fill
        features = features.replace([np.inf, -np.inf], np.nan)
        # Drop rows with NaNs (warm-up period)
        # Instead of dropping, we can let the dataset handler manage this, 
        # but for now, let's keep NaNs so we align with original dates.
        
        return features
