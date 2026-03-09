import pandas as pd
import numpy as np
import yaml,json
import argparse
from typing import Tuple, Dict, List, Union, Any
try:
    from .loader import DataLoader
    from .labeler import Labeler
    from .feature_engineer import FeatureEngineer
except ImportError:
    # Allow running as a direct script: python data/SwingDataset.py
    from loader import DataLoader
    from labeler import Labeler
    from feature_engineer import FeatureEngineer

class SwingDataset:
    """
    Manages the full data pipeline: Load -> Features -> Labels -> Split.
    """
    def __init__(self, config_source: Union[str, Dict[str, Any]]):
        if isinstance(config_source, dict):
            root_cfg = config_source
        else:
            with open(config_source, 'r') as f:
                root_cfg = yaml.safe_load(f)

        self.config = self._normalize_config(root_cfg)

        self.loader = DataLoader(self.config['data_path'])
        self.labeler = Labeler(
            target_pct=self.config['target_pct'],
            stop_loss_pct=self.config['stop_loss_pct'],
            holding_period=self.config['holding_period'],
            negative_label=self.config.get('negative_label', -1),
            stop_loss_check=self.config.get('stop_loss_check', "low"),
            target_check=self.config.get('target_check', "high"),
            exitOnGap=self.config.get('exit_on_gap', True)
        )
        self.engineer = FeatureEngineer(self.config['feature_config'])

        # Dataset output mode:
        # - tabular (default): returns 2D features for classical ML/MLP
        # - sequence: returns 3D (samples, seq_length, features) for LSTM/sequence models
        self.dataset_mode = str(self.config.get('dataset_mode', 'tabular')).lower()
        self.seq_length = int(self.config.get('seq_length', 10))
        if self.seq_length < 1:
            raise ValueError(f"Invalid seq_length={self.seq_length}. Must be >= 1.")
        if self.dataset_mode not in {'tabular', 'sequence', 'timeseries', 'time_series'}:
            raise ValueError(
                f"Invalid dataset_mode='{self.dataset_mode}'. "
                "Expected one of: tabular, sequence, timeseries, time_series."
            )
        
        self.train_end_date = pd.to_datetime(self.config['train_end_date'])
        self.test_start_date = pd.to_datetime(self.config['test_start_date'])
        if self.train_end_date >= self.test_start_date:
            raise ValueError(
                f"Invalid split: train_end_date ({self.train_end_date.date()}) "
                f"must be earlier than test_start_date ({self.test_start_date.date()})."
            )

    def _normalize_config(self, root_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Supports both:
        1) Legacy flat dataset config (existing behavior)
        2) Unified config with sections: dataset, labeling, features
        """
        if not isinstance(root_cfg, dict):
            raise ValueError("Dataset config must be a dictionary or YAML mapping.")

        # Unified layout
        if any(k in root_cfg for k in ['dataset', 'labeling', 'features']):
            dataset_cfg = dict(root_cfg.get('dataset', {}))
            label_cfg = dict(root_cfg.get('labeling', {}))
            features_cfg = root_cfg.get('features', {})

            cfg = {}
            cfg.update(dataset_cfg)
            cfg.update(label_cfg)

            if isinstance(features_cfg, dict) and 'indicators' in features_cfg:
                cfg['feature_config'] = features_cfg
            elif isinstance(features_cfg, str):
                cfg['feature_config'] = features_cfg
            else:
                cfg['feature_config'] = cfg.get('feature_config', 'configs/indicators_full.yaml')

            return cfg

        # Legacy flat layout
        return root_cfg

    def _build_sequence_dataset(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Tuple[np.ndarray, pd.Series]:
        """
        Convert tabular rows into per-symbol rolling sequences.
        Label for each sequence is the label of the sequence's last timestep.
        """
        if X.empty:
            return np.empty((0, self.seq_length, 0), dtype=np.float32), pd.Series(dtype=int, name='label')

        work = X.copy()
        work['__label__'] = y.to_numpy()
        work['__date__'] = X.index.to_numpy()

        feature_cols = [c for c in work.columns if c not in ['Symbol', '__label__', '__date__']]
        n_features = len(feature_cols)

        seq_data = []
        seq_labels = []
        seq_symbols = []
        seq_dates = []

        for symbol, grp in work.groupby('Symbol'):
            grp = grp.sort_values('__date__')
            feats = grp[feature_cols].to_numpy(dtype=np.float32)
            labels = grp['__label__'].to_numpy()
            dates = pd.to_datetime(grp['__date__']).to_numpy()

            if len(grp) < self.seq_length:
                continue

            for i in range(self.seq_length - 1, len(grp)):
                start = i - self.seq_length + 1
                seq_data.append(feats[start:i + 1])
                seq_labels.append(labels[i])
                seq_symbols.append(symbol)
                seq_dates.append(dates[i])

        if not seq_data:
            empty = np.empty((0, self.seq_length, n_features), dtype=np.float32)
            empty_y = pd.Series(dtype=int, name='label')
            return empty, empty_y

        X_seq = np.asarray(seq_data, dtype=np.float32)
        y_seq = pd.Series(
            seq_labels,
            index=pd.MultiIndex.from_arrays(
                [seq_symbols, pd.to_datetime(seq_dates)],
                names=['Symbol', 'Date']
            ),
            name='label'
        )
        return X_seq, y_seq

    def build_dataset(self) -> Tuple[Union[pd.DataFrame, np.ndarray], pd.Series, Union[pd.DataFrame, np.ndarray], pd.Series]:
        """
        Builds the dataset and returns train/test splits.

        Returns:
            - tabular mode: X_train, y_train, X_test, y_test (2D features)
            - sequence mode: X_train, y_train, X_test, y_test where X_* are
              np.ndarray with shape (samples, seq_length, n_features)
        """
        source_tickers = self.config.get('source_tickers')
        target_tickers = self.config.get('target_tickers')
        assert source_tickers is not None and target_tickers is not None,"You need to provide both source and target ticker"
        
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
        all_exit_dates = []
        
        for symbol, df in raw_data.items():
            # print(f"Processing {symbol}...")
            
            # 1. Compute Features
            features = self.engineer.compute_features(df)
            
            # 2. Compute Labels
            labels = self.labeler.create_labels(df)
            # print(labels)

            # Keep only entries with full lookahead horizon to avoid partial tail labels.
            if self.labeler.holding_period > 0:
                cutoff = len(df) - self.labeler.holding_period
                if cutoff <= 0:
                    continue
                full_horizon_index = df.index[:cutoff]
                features = features.loc[features.index.intersection(full_horizon_index)]
                labels = labels.loc[labels.index.intersection(full_horizon_index)]
            
            # 3. Merge
            # Align indices
            common_index = features.index.intersection(labels.index)
            features = features.loc[common_index]
            labels = labels.loc[common_index]
            
            # Add metadata
            features['Symbol'] = symbol
            
            all_features.append(features)
            all_labels.append(labels['label'])
            all_exit_dates.append(labels['exit_date'])
            
        if not all_features:
            raise ValueError("No data found or processed.")

        # Concatenate all stocks
        X = pd.concat(all_features)
        y = pd.concat(all_labels)
        exit_dates = pd.concat(all_exit_dates)
        
        # Drop NaNs created by indicators (warm-up)
        # Also drop NaNs in labels (end of data) if any (though labeler handles it)
        valid_mask = ~X.isna().any(axis=1) & ~y.isna() & ~exit_dates.isna()
        X = X[valid_mask]
        y = y[valid_mask]
        exit_dates = exit_dates[valid_mask]
        
        # Split
        train_mask = (X.index <= self.train_end_date) & (exit_dates < self.test_start_date)
        X_train = X[train_mask]
        y_train = y[train_mask]
        
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

        if self.dataset_mode in {'sequence', 'timeseries', 'time_series'}:
            X_train, y_train = self._build_sequence_dataset(X_train, y_train)
            X_test, y_test = self._build_sequence_dataset(X_test, y_test)

        return X_train, y_train, X_test, y_test

    def get_raw_prices(self, symbols: List[str] = None) -> Dict[str, pd.DataFrame]:
        """Helper to get raw prices for backtesting/evaluation."""
        return self.loader.load_data(symbols)


def _shape_of(x):
    return x.shape if hasattr(x, "shape") else (len(x),)


def main():
    with open("configs/experiment.yaml", 'r') as f:
        root_cfg = yaml.safe_load(f)
    root_cfg["labeling"]={
        "holding_period": 30,
        "target_pct": 0.08,
        "stop_loss_pct": 0.03,
        "negative_label": -1,
        "stop_loss_check": "low",
        "target_check": "high",
        "exit_on_gap": True
    }
    allsymbols=["ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BPCL","BHARTIARTL","BRITANNIA","CIPLA","COALINDIA","DRREDDY","EICHERMOT","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","ITC","INDUSINDBK","INFY","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NTPC","NESTLEIND","ONGC","POWERGRID","RELIANCE","SBILIFE","SHRIRAMFIN","SBIN","SUNPHARMA","TCS","TATACONSUM","TATAMOTORS","TATASTEEL","TECHM","TITAN","TRENT","ULTRACEMCO","WIPRO"]

    root_cfg["dataset"]["source_tickers"]=["HDFCBANK"]
    root_cfg["dataset"]["target_tickers"]=["HDFCBANK"]
    # root_cfg["dataset"]["source_tickers"]=allsymbols
    # root_cfg["dataset"]["target_tickers"]=allsymbols
    # root_cfg["dataset"]["train_end_date"]="2010-12-31"
    # root_cfg["dataset"]["test_start_date"]="2011-01-01"
    # print(json.dumps(root_cfg,indent=4))

    dataset = SwingDataset(root_cfg)
    X_train, y_train, X_test, y_test = dataset.build_dataset()
    print("Train have ",X_train.shape,"Test have ",X_test.shape)
    traincount,testcount=np.unique(y_train,return_counts=True),np.unique(y_test,return_counts=True)
    print("Training have",traincount,"Test have",testcount)
    traincount=traincount[0], [int(c/sum(traincount[1])*100) for c in traincount[1]]   
    testcount=testcount[0], [int(c/sum(testcount[1])*100) for c in testcount[1]]   
    print("Training have",traincount,"Test have",testcount)

    # y_train_s = pd.Series(y_train)
    # y_test_s = pd.Series(y_test)

    # print(f"Using config: {args.config}")
    # print(f"Train X shape: {_shape_of(X_train)}, y shape: {_shape_of(y_train)}")
    # print(f"Test  X shape: {_shape_of(X_test)}, y shape: {_shape_of(y_test)}")
    # print(f"Train label counts: {y_train_s.value_counts().sort_index().to_dict()}")
    # print(f"Test  label counts: {y_test_s.value_counts().sort_index().to_dict()}")


if __name__ == "__main__":
    main()
