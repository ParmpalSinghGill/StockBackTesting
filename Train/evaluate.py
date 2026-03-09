import pandas as pd
import numpy as np
from typing import Any
from metrics import Metrics

class Evaluator:
    """
    Evaluates the model on test data.
    """
    def __init__(self, model: Any):
        self.model = model

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series, returns_test: pd.Series = None) -> dict:
        """
        Runs evaluation and returns a dictionary of metrics.
        """
        y_pred = self.model.predict(X_test)
        
        # Classification Metrics
        class_metrics = Metrics.calculate_classification_metrics(y_test.values, y_pred)
        
        # Trading Metrics (if returns are available)
        trading_metrics = {}
        if returns_test is not None:
            # We need returns aligned with y_test
            # Assuming returns_test is a Series with same index
            trading_metrics = Metrics.calculate_trading_metrics(y_test.values, y_pred, returns_test.values)
        
        return {**class_metrics, **trading_metrics}
