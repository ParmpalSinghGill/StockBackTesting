import pandas as pd
import yaml
from typing import Tuple, Dict, List
from .loader import DataLoader
from .labeler import Labeler
from .feature_engineer import FeatureEngineer

class SwingDataset:
    """
    Manages the full data pipeline: Load -> Features -> Labels -> Split.
    """
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.loader = DataLoader(self.config['data_path'])
        self.labeler = Labeler(
            target_pct=self.config['target_pct'],
            stop_loss_pct=self.config['stop_loss_pct'],
            holding_period=self.config['holding_period']
        )
        self.engineer = FeatureEngineer(self.config['feature_config'])
        
        self.train_end_date = pd.to_datetime(self.config['train_end_date'])
        self.test_start_date = pd.to_datetime(self.config['test_start_date'])

    def build_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Builds the dataset and returns train/test splits.
        
        Returns:
            X_train, y_train, X_test, y_test
        """
        source_tickers = self.config.get('source_tickers')
        target_tickers = self.config.get('target_tickers')
        
        # Ensure they are lists
        if isinstance(source_tickers, str):
            source_tickers = [source_tickers]
        if isinstance(target_tickers, str):
            target_tickers = [target_tickers]
        
        # Determine symbols to load (Union of source and target)
        symbols = set()
        if source_tickers:
            symbols.update(source_tickers)
        if target_tickers:
            symbols.update(target_tickers)
        
        # If both are null, symbols is empty set -> None (load all)
        load_symbols = list(symbols) if (symbols and source_tickers is not None and target_tickers is not None) else None
        
        # Fallback for deprecated target_stock
        if 'target_stock' in self.config and self.config['target_stock']:
             load_symbols = [self.config['target_stock']]

        print(f"Requesting symbols: {load_symbols if load_symbols else 'ALL'}")
        raw_data = self.loader.load_data(load_symbols)
        print(f"Loaded {len(raw_data)} stocks: {list(raw_data.keys())}")
        
        all_features = []
        all_labels = []
        
        for symbol, df in raw_data.items():
            # print(f"Processing {symbol}...")
            
            # 1. Compute Features
            features = self.engineer.compute_features(df)
            
            # 2. Compute Labels
            labels = self.labeler.create_labels(df)
            print(labels)
            
            # 3. Merge
            # Align indices
            common_index = features.index.intersection(labels.index)
            features = features.loc[common_index]
            labels = labels.loc[common_index]
            
            # Add metadata
            features['Symbol'] = symbol
            
            all_features.append(features)
            all_labels.append(labels['label'])
            
        if not all_features:
            raise ValueError("No data found or processed.")

        # Concatenate all stocks
        X = pd.concat(all_features)
        y = pd.concat(all_labels)
        
        # Drop NaNs created by indicators (warm-up)
        # Also drop NaNs in labels (end of data) if any (though labeler handles it)
        valid_mask = ~X.isna().any(axis=1) & ~y.isna()
        X = X[valid_mask]
        y = y[valid_mask]
        
        # Split
        X_train = X[X.index <= self.train_end_date]
        y_train = y[y.index <= self.train_end_date]
        
        X_test = X[X.index >= self.test_start_date]
        y_test = y[y.index >= self.test_start_date]
        
        # Filter by source/target tickers
        if source_tickers:
            train_mask = X_train['Symbol'].isin(source_tickers)
            X_train = X_train[train_mask]
            y_train = y_train[train_mask]
            
        if target_tickers:
            test_mask = X_test['Symbol'].isin(target_tickers)
            X_test = X_test[test_mask]
            y_test = y_test[test_mask]
        
        return X_train, y_train, X_test, y_test

    def get_raw_prices(self, symbols: List[str] = None) -> Dict[str, pd.DataFrame]:
        """Helper to get raw prices for backtesting/evaluation."""
        return self.loader.load_data(symbols)
