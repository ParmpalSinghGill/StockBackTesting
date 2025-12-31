import pickle
import sys

def inspect_keys(path):
    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        if isinstance(data, dict):
            keys = list(data.keys())
            print(f"Total keys: {len(keys)}")
            print(f"First 10 keys: {keys[:10]}")
            
            # Check for HDFC variants
            hdfc_keys = [k for k in keys if 'HDFC' in str(k)]
            print(f"Keys containing 'HDFC': {hdfc_keys}")
        else:
            print(f"Data is not a dict, it is {type(data)}")
            
    except Exception as e:
        print(f"Error loading file: {e}")

if __name__ == "__main__":
    inspect_keys("StockData/AllSTOCKS.pk")
