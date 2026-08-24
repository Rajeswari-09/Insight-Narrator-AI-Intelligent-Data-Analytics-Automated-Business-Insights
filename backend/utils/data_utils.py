"""
data_utils.py — Utility functions for loading and profiling CSV/Excel datasets.
"""
import io
import pandas as pd
import numpy as np


def load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load a CSV or Excel file from raw bytes into a pandas DataFrame."""
    if filename.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        # Try common encodings
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Unable to decode the CSV file with common encodings.")
    
    df = _clean_dataframe(df)
    return df


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: strip whitespace from string columns, parse date columns."""
    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            # Attempt date parsing
            try:
                parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="raise")
                df[col] = parsed
            except Exception:
                pass  # Keep as string
    return df


def classify_columns(df: pd.DataFrame) -> dict:
    """
    Classify columns into: numeric, categorical, datetime.
    Returns a dict: {'numeric': [...], 'categorical': [...], 'datetime': [...]}
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    categorical_cols = [
        c for c in df.columns
        if c not in numeric_cols and c not in datetime_cols
    ]
    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
    }
