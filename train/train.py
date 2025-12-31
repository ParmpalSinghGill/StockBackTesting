import sys
import os
import yaml
import pandas as pd
import joblib
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from data.dataset import SwingDataset
from models.ml_models import MLModelWrapper
from models.dl_models import DLModelWrapper
from evaluate import Evaluator

def train_pipeline(config_path: str = 'configs/training.yaml'):
    # Load configs
    with open(config_path, 'r') as f:
        train_config = yaml.safe_load(f)
    
    with open('configs/model.yaml', 'r') as f:
        model_config = yaml.safe_load(f)
        
    # 1. Build Dataset
    print("Building dataset...")
    dataset = SwingDataset('configs/dataset.yaml')
    X_train, y_train, X_test, y_test = dataset.build_dataset()
    
    print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    
    # # 2. Initialize Model
    # model_type = model_config['model_type']
    # params = model_config['params'].get(model_type, {})
    
    # print(f"Training {model_type}...")
    # if model_type in ['mlp', 'lstm']:
    #     model = DLModelWrapper(model_type, params, input_dim=X_train.shape[1])
    # else:
    #     model = MLModelWrapper(model_type, params)
        
    # # 3. Train
    # model.fit(X_train, y_train)
    
    # # 4. Evaluate
    # print("Evaluating...")
    # evaluator = Evaluator(model)
    
    # # Get returns for trading metrics (hacky: re-calculate or retrieve from labeler logic)
    # # Ideally, dataset should provide this. For now, we'll skip trading metrics in this step 
    # # or implement a quick lookup if we had the raw returns.
    # # Let's try to get returns from the dataset if possible, or just pass None
    # # In dataset.py, we didn't explicitly store returns in X or y. 
    # # But we can re-derive or just rely on classification metrics here.
    # # The backtester is for the real trading evaluation.
    
    # metrics = evaluator.evaluate(X_test, y_test)
    # print("Metrics:", json.dumps(metrics, indent=2))
    
    # # 5. Save Artifacts
    # output_dir = train_config['output_dir']
    # os.makedirs(output_dir, exist_ok=True)
    
    # # Save model
    # if model_type not in ['mlp', 'lstm']:
    #     joblib.dump(model, os.path.join(output_dir, 'model.joblib'))
    # else:
    #     # Save PyTorch model
    #     import torch
    #     torch.save(model.model.state_dict(), os.path.join(output_dir, 'model.pth'))
        
    # # Save metrics
    # with open(os.path.join(output_dir, 'metrics.json'), 'w') as f:
    #     json.dump(metrics, f, indent=2)
        
    # # Save feature list
    # feature_names = X_train.columns.tolist()
    # if 'Symbol' in feature_names: feature_names.remove('Symbol')
    # with open(os.path.join(output_dir, 'features.json'), 'w') as f:
    #     json.dump(feature_names, f)

    # print(f"Training complete. Artifacts saved to {output_dir}")

if __name__ == "__main__":
    train_pipeline()
