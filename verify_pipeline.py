import pandas as pd
import numpy as np
import os
import pickle
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from data.SwingDataset import SwingDataset
from models.ml_models import MLModelWrapper
from backtest.simulator import Backtester


def export_single_stock_features_csv(dataset: SwingDataset, symbol: str = "AAPL",
                                     output_path: str = None):
    """Export one stock's engineered features + labels to CSV."""
    if output_path is None:
        output_path=f"Results/verify_{symbol}_features_labels.csv"
    raw_prices = dataset.get_raw_prices([symbol])
    if symbol not in raw_prices:
        if not raw_prices:
            raise ValueError("No raw price data available to export features.")
        symbol = next(iter(raw_prices.keys()))

    df = raw_prices[symbol]
    features = dataset.engineer.compute_features(df)
    labels = dataset.labeler.create_labels(df)
    print("Label columns",labels.columns,np.unique(labels["label"],return_counts=True))

    # Keep only full-horizon label rows, aligned with SwingDataset behavior.
    if dataset.labeler.holding_period > 0:
        cutoff = len(df) - dataset.labeler.holding_period
        if cutoff > 0:
            full_horizon_index = df.index[:cutoff]
            features = features.loc[features.index.intersection(full_horizon_index)]
            labels = labels.loc[labels.index.intersection(full_horizon_index)]

    # merged = df.join(features, how='inner').join(labels, how='inner')
    merged = df.join(labels, how='inner')
    # merged['Symbol'] = symbol

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=True)
    print(f"Saved one-stock features+labels CSV: {output_path} (rows={len(merged)})")

def generate_synthetic_data(path: str):
    """Generates synthetic stock data for testing."""
    dates = pd.date_range(start="2023-01-01", end="2024-06-01", freq="B")
    data = {}
    
    for symbol in ['AAPL', 'GOOGL', 'MSFT']:
        n = len(dates)
        price = 100.0
        prices = []
        for _ in range(n):
            change = np.random.normal(0, 0.02)
            price *= (1 + change)
            prices.append(price)
            
        df = pd.DataFrame({
            'Open': prices,
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Close': prices, # Simplified
            'Volume': np.random.randint(1000, 10000, n)
        }, index=dates)
        data[symbol] = df
        
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    print(f"Synthetic data saved to {path}")

def verify_pipeline():
    # 1. Generate Data
    data_path = "/media/parmpal/Data/Codes/MyCodes/StockS/StockBackTesting/StockData/AllSTOCKS.pk"

    
    # 2. Update Configs to use synthetic data
    # We'll just modify the dataset config in memory or write a temp one
    # For simplicity, let's overwrite dataset.yaml temporarily or assume the user will update it.
    # Actually, let's create a test config.
    
    test_dataset_config = f"""
data_path: "{data_path}"
source_tickers: ["HDFCBANK"]
target_tickers: ["HDFCBANK"]
holding_period: 20
target_pct: 0.1
stop_loss_pct: 0.05
negative_label: -1
train_end_date: "2023-12-31"
test_start_date: "2024-01-01"
feature_config: "configs/indicators_min.yaml"
"""
    with open("configs/test_dataset.yaml", "w") as f:
        f.write(test_dataset_config)
        
    # 3. Run Dataset Build
    print("\n--- Testing Dataset Build ---")
    dataset = SwingDataset("configs/test_dataset.yaml")
    export_single_stock_features_csv(dataset, symbol="HDFCBANK")
    # X_train, y_train, X_test, y_test = dataset.build_dataset()
    # print(f"Train shape: {X_train.shape}")
    # print(f"Test shape: {X_test.shape}")
    
    # if X_train.empty or X_test.empty:
    #     print("Error: Dataset is empty!")
    #     return

    # # 4. Train Model
    # print("\n--- Testing Model Training ---")
    # params = {
    #     'n_estimators': 10,
    #     'max_depth': 3,
    #     'random_state': 42
    # }
    # model = MLModelWrapper('random_forest', params)
    # model.fit(X_train, y_train)
    
    # # 5. Predict
    # print("\n--- Testing Prediction ---")
    # preds = model.predict(X_test)
    # print(f"Predictions: {preds[:10]}")
    
    # # 6. Backtest
    # print("\n--- Testing Backtest ---")
    # # Prepare predictions DataFrame
    # predictions = pd.DataFrame({
    #     'prediction': preds,
    #     'Symbol': X_test['Symbol']
    # }, index=X_test.index)
    
    # raw_prices = dataset.get_raw_prices()
    # backtester = Backtester()
    # trade_log, equity_curve = backtester.run_backtest(
    #     raw_prices, predictions, 
    #     target_pct=0.02, stop_loss_pct=0.01, holding_period=5
    # )
    
    # print(f"Trades: {len(trade_log)}")
    # print(f"Final Equity: {equity_curve.iloc[-1]['Equity'] if not equity_curve.empty else 'N/A'}")
    
    # print("\nVerification Complete!")

if __name__ == "__main__":
    verify_pipeline()
