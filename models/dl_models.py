import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, TensorDataset
from typing import Dict, Any

class SimpleMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_layers: list, num_classes: int, dropout: float):
        super(SimpleMLP, self).__init__()
        layers = []
        in_dim = input_dim
        for h_dim in hidden_layers:
            layers.append(nn.Linear(in_dim, h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            in_dim = h_dim
        layers.append(nn.Linear(in_dim, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

class DLModelWrapper:
    """
    Wrapper for PyTorch models to mimic sklearn interface.
    """
    def __init__(self, model_type: str, params: Dict[str, Any], input_dim: int = None):
        self.model_type = model_type
        self.params = params
        self.input_dim = input_dim
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _build_model(self, input_dim: int):
        if self.model_type == 'mlp':
            self.model = SimpleMLP(
                input_dim=input_dim,
                hidden_layers=self.params.get('hidden_layers', [64, 32]),
                num_classes=3, # -1, 0, 1 mapped to 0, 1, 2
                dropout=self.params.get('dropout', 0.2)
            ).to(self.device)
        elif self.model_type == 'lstm':
            # Placeholder for LSTM - requires 3D input (batch, seq, feature)
            # For now, we'll stick to MLP for tabular data as primary DL example
            raise NotImplementedError("LSTM implementation requires sequence data loader adjustment.")
        else:
            raise ValueError(f"Unknown DL model type: {self.model_type}")

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.params.get('learning_rate', 0.001))

    def fit(self, X: pd.DataFrame, y: pd.Series):
        X_clean = self._preprocess(X)
        
        # Map labels from -1, 0, 1 to 0, 1, 2
        y_mapped = y.map({-1: 0, 0: 1, 1: 2}).values
        X_values = X_clean.values.astype(np.float32)
        
        if self.model is None:
            self._build_model(X_clean.shape[1])
            
        dataset = TensorDataset(torch.tensor(X_values), torch.tensor(y_mapped, dtype=torch.long))
        loader = DataLoader(dataset, batch_size=self.params.get('batch_size', 32), shuffle=True)
        
        epochs = self.params.get('epochs', 10)
        self.model.train()
        
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, batch_y in loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
            
            # print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(loader):.4f}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        probs = self.predict_proba(X)
        # Map 0, 1, 2 back to -1, 0, 1
        preds_mapped = np.argmax(probs, axis=1)
        mapping = {0: -1, 1: 0, 2: 1}
        return np.array([mapping[p] for p in preds_mapped])

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_clean = self._preprocess(X)
        X_values = torch.tensor(X_clean.values.astype(np.float32)).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_values)
            probs = torch.softmax(outputs, dim=1)
        
        return probs.cpu().numpy()

    def _preprocess(self, X: pd.DataFrame) -> pd.DataFrame:
        if 'Symbol' in X.columns:
            return X.drop(columns=['Symbol'])
        return X
