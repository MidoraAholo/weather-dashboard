"""Data loader for Cambridge station data.

Provides:
- download_cambridge_data(url, dest)
- load_cambridge_data(path)

The parser is robust: it tries CSV, whitespace-delimited and common date columns. It returns a pandas.DataFrame with a DatetimeIndex and numeric columns.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    import requests
except Exception:  # pragma: no cover - requests may not be installed in tests
    requests = None


def download_cambridge_data(url: str, dest: str = "data/cambridge.txt", force: bool = False) -> str:
    """Download the raw Cambridge station file to `dest`.

    If `requests` is unavailable, raises RuntimeError. Returns the path to file.
    """
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        return str(dest_path)
    if requests is None:
        raise RuntimeError("requests is required to download data; install requests or place file manually")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest_path.write_bytes(resp.content)
    return str(dest_path)


def _try_read_csv(path: str) -> Optional[pd.DataFrame]:
    """Try reading the file with multiple read_csv options."""
    parsers = [
        {"delim_whitespace": True},
        {"sep": ","},
        {"sep": "\t"},
    ]
    for opts in parsers:
        try:
            df = pd.read_csv(path, **opts)
            if df.shape[0] > 0:
                return df
        except Exception:
            continue
    return None


def load_cambridge_data(path: str) -> pd.DataFrame:
    """Load and clean Cambridge station data into a pandas DataFrame.

    - Tries to detect a date column ("date", "Date", or a combination of year/month/day)
    - Converts numeric columns, coerces invalid values to NaN
    - Sets DatetimeIndex

    Returns DataFrame with DatetimeIndex and columns cleaned.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    df = _try_read_csv(str(path))
    if df is None:
        # Last resort: read as table of fixed-width or raw text -> fallback to pandas read_fwf
        try:
            df = pd.read_fwf(path)
        except Exception as exc:
            raise RuntimeError("Unable to parse data file") from exc

    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]

    # Try to detect a date column
    date_col = None
    for candidate in ["date", "Date", "DATE", "datetime"]:
        if candidate in df.columns:
            date_col = candidate
            break

    if date_col is None:
        # Look for year/month/day columns
        year_cols = [c for c in df.columns if c.lower().startswith("year")]
        month_cols = [c for c in df.columns if c.lower().startswith("month")]
        day_cols = [c for c in df.columns if c.lower().startswith("day")]
        if year_cols and month_cols and day_cols:
            df["date"] = pd.to_datetime(df[[year_cols[0], month_cols[0], day_cols[0]]])
            date_col = "date"

    if date_col is None:
        # try to parse first column as date
        try:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
            df = df.set_index(df.columns[0])
        except Exception:
            # give up
            raise RuntimeError("Could not detect a date column in the Cambridge data file")
    else:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.set_index(date_col)

    # Convert numeric columns
    for col in df.columns:
        # skip index
        try:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace("", ""), errors="coerce")
        except Exception:
            # leave as-is
            pass

    # Sort and drop fully empty columns
    df = df.sort_index()
    df = df.loc[~df.index.duplicated(keep="first")]
    df = df.loc[:, df.notna().any(axis=0)]

    return df


if __name__ == "__main__":
    # quick manual test snippet (not executed in unit tests)
    print("data_loader module")