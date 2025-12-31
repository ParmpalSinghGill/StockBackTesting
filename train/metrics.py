import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix

class Metrics:
    """
    Calculates various performance metrics for the model.
    """
    @staticmethod
    def calculate_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        """
        Standard classification metrics.
        """
        # Precision/Recall for class +1 (Long)
        # Assuming labels are -1, 0, 1
        
        # Binary metrics for +1 vs Rest
        y_true_binary = (y_true == 1).astype(int)
        y_pred_binary = (y_pred == 1).astype(int)
        
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        # Overall accuracy
        acc = accuracy_score(y_true, y_pred)
        
        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=[-1, 0, 1])
        
        return {
            "precision_long": precision,
            "recall_long": recall,
            "f1_long": f1,
            "accuracy": acc,
            "confusion_matrix": cm.tolist()
        }

    @staticmethod
    def calculate_trading_metrics(y_true: np.ndarray, y_pred: np.ndarray, returns: np.ndarray) -> dict:
        """
        Trading-specific metrics based on realized returns of predicted trades.
        """
        # Filter for trades taken (prediction != 0)
        # For now, let's focus on Long trades (+1)
        long_mask = (y_pred == 1)
        
        if not np.any(long_mask):
            return {
                "win_rate": 0.0,
                "avg_return": 0.0,
                "trade_count": 0,
                "total_return": 0.0
            }
            
        long_returns = returns[long_mask]
        
        # Win rate: % of trades with positive return
        wins = np.sum(long_returns > 0)
        win_rate = wins / len(long_returns)
        
        avg_return = np.mean(long_returns)
        total_return = np.sum(long_returns) # Simple sum, not compounded for this metric
        
        return {
            "win_rate": win_rate,
            "avg_return": avg_return,
            "trade_count": int(len(long_returns)),
            "total_return": total_return
        }
