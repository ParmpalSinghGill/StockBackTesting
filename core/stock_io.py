from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def split_dict_to_df(stock_data: Dict[str, Any]) -> pd.DataFrame:
    """Convert {'data','columns','index'} payload to DataFrame."""
    try:
        columns = stock_data["columns"]
        if len(columns) > 0 and isinstance(columns[0], tuple):
            columns = [c[0] for c in columns]
        return pd.DataFrame(stock_data["data"], columns=columns, index=stock_data["index"])
    except Exception:
        # Keep old behavior: surface payload then fail loudly.
        print(stock_data)
        raise


def df_to_split_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """Convert DataFrame into split-dict payload used by project pickle files."""
    return {"data": df.values, "columns": list(df.columns), "index": df.index}


def load_pickle(path: Path | str) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)


def dump_pickle(path: Path | str, payload: Any) -> None:
    with open(path, "wb") as f:
        pickle.dump(payload, f)

