import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None
# from lightgbm import LGBMClassifier
# from catboost import CatBoostClassifier

class ModelFactory:
    """
    Factory to create ML models based on config.
    """
    @staticmethod
    def create_model(model_type: str, params: Dict[str, Any]):
        if model_type == 'logistic_regression':
            return LogisticRegression(**params)
        elif model_type == 'random_forest':
            return RandomForestClassifier(**params)
        elif model_type == 'xgboost':
            if XGBClassifier is None:
                raise ImportError("XGBoost is not installed.")
            return XGBClassifier(**params)
        # elif model_type == 'lightgbm':
        #     return LGBMClassifier(**params)
        # elif model_type == 'catboost':
        #     return CatBoostClassifier(**params)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

class MLModelWrapper:
    """
    Wrapper for ML models to handle training and prediction consistently.
    """
    def __init__(self, model_type: str, params: Dict[str, Any]):
        self.model = ModelFactory.create_model(model_type, params)
        self.model_type = model_type

    def fit(self, X: pd.DataFrame, y: pd.Series):
        # Drop non-feature columns if present
        X_clean = self._preprocess(X)
        self.model.fit(X_clean, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        X_clean = self._preprocess(X)
        return self.model.predict(X_clean)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_clean = self._preprocess(X)
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X_clean)
        else:
            raise NotImplementedError(f"{self.model_type} does not support predict_proba")

    def _preprocess(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Removes metadata columns like 'Symbol' before passing to model.
        """
        if 'Symbol' in X.columns:
            return X.drop(columns=['Symbol'])
        return X
