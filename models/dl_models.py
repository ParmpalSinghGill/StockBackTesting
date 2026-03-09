import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, TensorDataset
from typing import Dict, Any, Union

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

class LSTMClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int, num_classes: int, dropout: float):
        super(LSTMClassifier, self).__init__()
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        output, _ = self.lstm(x)
        last_timestep = output[:, -1, :]
        return self.fc(self.dropout(last_timestep))

class CNN1DClassifier(nn.Module):
    def __init__(
        self,
        input_dim: int,
        seq_length: int,
        num_classes: int,
        conv_channels: list,
        kernel_size: int,
        hidden_dim: int,
        dropout: float
    ):
        super(CNN1DClassifier, self).__init__()
        c1 = conv_channels[0] if len(conv_channels) > 0 else 64
        c2 = conv_channels[1] if len(conv_channels) > 1 else 128

        # Conv1d expects (batch, channels=input_dim, seq_len)
        self.features = nn.Sequential(
            nn.Conv1d(input_dim, c1, kernel_size=kernel_size, padding=kernel_size // 2),
            nn.ReLU(),
            nn.BatchNorm1d(c1),
            nn.Conv1d(c1, c2, kernel_size=kernel_size, padding=kernel_size // 2),
            nn.ReLU(),
            nn.BatchNorm1d(c2),
            nn.AdaptiveMaxPool1d(1)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(c2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )
        self.seq_length = seq_length

    def forward(self, x):
        # x shape: (batch, seq_len, input_dim) -> (batch, input_dim, seq_len)
        x = x.transpose(1, 2)
        x = self.features(x)
        return self.classifier(x)

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
        self.label_to_int = None
        self.int_to_label = None

    def _build_model(self, input_dim: int, num_classes: int, seq_length: int = None):
        if self.model_type == 'mlp':
            self.model = SimpleMLP(
                input_dim=input_dim,
                hidden_layers=self.params.get('hidden_layers', [64, 32]),
                num_classes=num_classes,
                dropout=self.params.get('dropout', 0.2)
            ).to(self.device)
        elif self.model_type == 'lstm':
            self.model = LSTMClassifier(
                input_dim=input_dim,
                hidden_dim=self.params.get('hidden_dim', 64),
                num_layers=self.params.get('num_layers', 2),
                num_classes=num_classes,
                dropout=self.params.get('dropout', 0.2)
            ).to(self.device)
        elif self.model_type == 'cnn':
            if seq_length is None:
                raise ValueError("CNN requires sequence input with known seq_length.")
            self.model = CNN1DClassifier(
                input_dim=input_dim,
                seq_length=seq_length,
                num_classes=num_classes,
                conv_channels=self.params.get('conv_channels', [64, 128]),
                kernel_size=self.params.get('kernel_size', 3),
                hidden_dim=self.params.get('hidden_dim', 64),
                dropout=self.params.get('dropout', 0.2)
            ).to(self.device)
        else:
            raise ValueError(f"Unknown DL model type: {self.model_type}")

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.params.get('learning_rate', 0.001))

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: pd.Series):
        X_values = self._preprocess(X, mode='fit')
        y_series = pd.Series(y).reset_index(drop=True)

        unique_labels = sorted(y_series.dropna().unique().tolist())
        self.label_to_int = {label: i for i, label in enumerate(unique_labels)}
        self.int_to_label = {i: label for label, i in self.label_to_int.items()}
        y_mapped = y_series.map(self.label_to_int).values.astype(np.int64)

        if self.model is None:
            input_dim = X_values.shape[-1] if X_values.ndim == 3 else X_values.shape[1]
            seq_length = X_values.shape[1] if X_values.ndim == 3 else None
            self._build_model(input_dim=input_dim, num_classes=len(unique_labels), seq_length=seq_length)

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

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        probs = self.predict_proba(X)
        preds_mapped = np.argmax(probs, axis=1)
        return np.array([self.int_to_label[int(p)] for p in preds_mapped])

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        X_values = torch.tensor(self._preprocess(X, mode='predict')).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_values)
            probs = torch.softmax(outputs, dim=1)
        
        return probs.cpu().numpy()

    def _preprocess(self, X: Union[pd.DataFrame, np.ndarray], mode: str = 'fit') -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            X_clean = X.drop(columns=['Symbol']) if 'Symbol' in X.columns else X
            values = X_clean.values.astype(np.float32)
            if self.model_type in ['lstm', 'cnn']:
                raise ValueError(
                    f"{self.model_type} expects sequence input (3D ndarray). "
                    "Set dataset_mode='sequence' in dataset config."
                )
            return values

        if isinstance(X, np.ndarray):
            values = X.astype(np.float32)
            if values.ndim == 2 and self.model_type in ['lstm', 'cnn']:
                raise ValueError(
                    f"{self.model_type} expects 3D input of shape (samples, seq_length, features)."
                )
            if values.ndim == 3 and self.model_type == 'mlp':
                # Allow MLP on sequence data by flattening each sequence.
                n, seq_len, feat = values.shape
                return values.reshape(n, seq_len * feat)
            return values

        raise TypeError(f"Unsupported X type: {type(X)}")
