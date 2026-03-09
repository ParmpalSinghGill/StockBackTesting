import sys
import os
import yaml
import joblib
import json
import argparse
import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from data.SwingDataset import SwingDataset
from models.ml_models import MLModelWrapper
from models.dl_models import DLModelWrapper
from evaluate import Evaluator

def _load_yaml(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def _load_train_bundle(config_path: str = 'configs/experiment.yaml'):
    """
    Returns (train_config, model_config, dataset_config).

    Supports:
    1) Unified config file with sections: training, model, dataset, labeling, features
    2) Legacy split config files:
       - training.yaml
       - model.yaml
       - dataset.yaml
    """
    cfg = _load_yaml(config_path)
    if not isinstance(cfg, dict):
        raise ValueError(f"Invalid config at {config_path}. Expected YAML mapping.")

    is_unified = any(k in cfg for k in ['training', 'model', 'dataset', 'labeling', 'features'])
    if is_unified:
        train_config = dict(cfg.get('training', {}))
        model_config = dict(cfg.get('model', {}))
        dataset_config = dict(cfg)
        if 'params' not in model_config:
            model_config['params'] = {}
        return train_config, model_config, dataset_config

    train_config = cfg
    model_config_path = train_config.get('model_config_path', 'configs/model.yaml')
    dataset_config_path = train_config.get('dataset_config_path', 'configs/dataset.yaml')
    model_config = _load_yaml(model_config_path)
    dataset_config = _load_yaml(dataset_config_path)
    return train_config, model_config, dataset_config

def _to_sequence_dataset(X: pd.DataFrame, y: pd.Series, seq_length: int):
    """
    Convert tabular per-row data into rolling per-symbol sequences.
    X must contain a Symbol column and datetime-like index.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("Tabular-to-sequence conversion expects X as DataFrame.")
    if 'Symbol' not in X.columns:
        raise ValueError("X must contain 'Symbol' column for sequence conversion.")
    if seq_length < 1:
        raise ValueError("seq_length must be >= 1.")

    work = X.copy()
    work['__label__'] = pd.Series(y).values
    work['__date__'] = X.index.to_numpy()
    feature_cols = [c for c in work.columns if c not in ['Symbol', '__label__', '__date__']]

    seq_data, seq_labels, seq_symbols, seq_dates = [], [], [], []

    for symbol, grp in work.groupby('Symbol'):
        grp = grp.sort_values('__date__')
        feats = grp[feature_cols].to_numpy(dtype=np.float32)
        labels = grp['__label__'].to_numpy()
        dates = pd.to_datetime(grp['__date__']).to_numpy()

        if len(grp) < seq_length:
            continue

        for i in range(seq_length - 1, len(grp)):
            start = i - seq_length + 1
            seq_data.append(feats[start:i + 1])
            seq_labels.append(labels[i])
            seq_symbols.append(symbol)
            seq_dates.append(dates[i])

    X_seq = np.asarray(seq_data, dtype=np.float32) if seq_data else np.empty((0, seq_length, len(feature_cols)), dtype=np.float32)
    y_seq = pd.Series(
        seq_labels,
        index=pd.MultiIndex.from_arrays([seq_symbols, pd.to_datetime(seq_dates)], names=['Symbol', 'Date']),
        name='label'
    ) if seq_labels else pd.Series(dtype=float, name='label')
    return X_seq, y_seq, feature_cols


def _resolve_models_to_train(model_config: dict, train_all_models: bool = False) -> list:
    def _flatten_model_names(value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple, set)):
            out = []
            for item in value:
                out.extend(_flatten_model_names(item))
            return out
        return [str(value)]

    if train_all_models:
        return list(model_config.get('params', {}).keys())

    model_types = model_config.get('model_types')
    if model_types:
        models = _flatten_model_names(model_types)
        return models

    model_type = model_config.get('model_type')
    if isinstance(model_type, (list, tuple, set)):
        return _flatten_model_names(model_type)
    if model_type == 'all':
        return list(model_config.get('params', {}).keys())
    return _flatten_model_names(model_type)


def _save_model_artifact(model, model_type: str, model_dir: str):
    if model_type in ['mlp', 'lstm', 'cnn']:
        import torch
        torch.save(model.model.state_dict(), os.path.join(model_dir, 'model.pth'))
    else:
        joblib.dump(model, os.path.join(model_dir, 'model.joblib'))


def train_pipeline(config_path: str = 'configs/experiment.yaml'):
    # Load config bundle (unified preferred, legacy supported)
    train_config, model_config, dataset_config = _load_train_bundle(config_path)

    # 1. Build Dataset
    print("Building dataset...")
    dataset = SwingDataset(dataset_config)
    X_train, y_train, X_test, y_test = dataset.build_dataset()
    
    print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")

    # 2. Train one or more models
    train_all_models = train_config.get('train_all_models', False)
    models_to_train = _resolve_models_to_train(model_config, train_all_models=train_all_models)
    print(f"Models to train: {models_to_train}")

    output_dir = train_config.get('output_dir', 'Results/experiment_1')
    os.makedirs(output_dir, exist_ok=True)

    if hasattr(X_train, "columns"):
        feature_names = [c for c in X_train.columns.tolist() if c != 'Symbol']
    else:
        feature_names = []
        if hasattr(X_train, "shape"):
            n_features = X_train.shape[-1] if len(X_train.shape) >= 2 else 0
            feature_names = [f"f_{i}" for i in range(n_features)]

    all_metrics = {}
    csv_rows = []

    for model_type in models_to_train:
        params = model_config.get('params', {}).get(model_type, {})
        print(f"\nTraining {model_type} ...")

        try:
            X_train_model, y_train_model = X_train, y_train
            X_test_model, y_test_model = X_test, y_test
            model_feature_names = list(feature_names)

            if model_type in ['lstm', 'cnn']:
                if isinstance(X_train, pd.DataFrame):
                    seq_length = int(params.get('seq_length', getattr(dataset, 'seq_length', 10)))
                    X_train_model, y_train_model, seq_feature_names = _to_sequence_dataset(X_train, y_train, seq_length)
                    X_test_model, y_test_model, _ = _to_sequence_dataset(X_test, y_test, seq_length)
                    model_feature_names = seq_feature_names
                    print(
                        f"Auto-converted tabular data to sequences for {model_type}: "
                        f"train={X_train_model.shape}, test={X_test_model.shape}, seq_length={seq_length}"
                    )

            if model_type in ['mlp', 'lstm', 'cnn']:
                input_dim = len(model_feature_names)
                if input_dim == 0 and hasattr(X_train_model, "shape"):
                    input_dim = X_train_model.shape[-1] if len(X_train_model.shape) >= 2 else None
                model = DLModelWrapper(model_type, params, input_dim=input_dim)
            else:
                if isinstance(X_train_model, np.ndarray) and X_train_model.ndim == 3:
                    n, s, f = X_train_model.shape
                    X_train_model = X_train_model.reshape(n, s * f)
                    X_test_model = X_test_model.reshape(X_test_model.shape[0], X_test_model.shape[1] * X_test_model.shape[2])
                    model_feature_names = [f"f_{i}" for i in range(X_train_model.shape[1])]
                model = MLModelWrapper(model_type, params)

            model.fit(X_train_model, y_train_model)

            evaluator = Evaluator(model)
            metrics = evaluator.evaluate(X_test_model, y_test_model)
            all_metrics[model_type] = metrics
            row = {"model": model_type, "status": "success"}
            for key, value in metrics.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = value
            csv_rows.append(row)

            metrics={k:v for k,v in metrics.items() if k in ["precision_long","recall_long","f1_long","accuracy"]}
            # metrics["confusion_matrix"]=metrics["confusion_matrix"]
            print(f"{model_type} metrics:\n{json.dumps(metrics, indent=2)}")

            model_dir = os.path.join(output_dir, model_type)
            os.makedirs(model_dir, exist_ok=True)

            if train_config.get('save_model', True):
                _save_model_artifact(model, model_type, model_dir)

            with open(os.path.join(model_dir, 'metrics.json'), 'w') as f:
                json.dump(metrics, f, indent=2)
            with open(os.path.join(model_dir, 'features.json'), 'w') as f:
                json.dump(model_feature_names, f, indent=2)

        except Exception as e:
            all_metrics[model_type] = {"error": str(e)}
            csv_rows.append({"model": model_type, "status": "failed", "error": str(e)})
            print(f"{model_type} failed: {e}")

    with open(os.path.join(output_dir, 'summary_metrics.json'), 'w') as f:
        json.dump(all_metrics, f, indent=2)
    comparison_csv_path = os.path.join(output_dir, train_config.get('comparison_csv', 'model_comparison.csv'))
    with open(comparison_csv_path, 'w') as _:
        pass
    pd.DataFrame(csv_rows).to_csv(comparison_csv_path, index=False)

    print(f"\nTraining complete. Artifacts saved to {output_dir}")
    print(f"Model comparison CSV: {comparison_csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Train models using unified or legacy config files.")
    parser.add_argument(
        "--config",
        default="configs/experiment.yaml",
        help="Path to config file (unified config recommended).",
    )
    args = parser.parse_args()
    print(f"Using config: {args.config}")
    train_pipeline(config_path=args.config)

if __name__ == "__main__":
    main()
