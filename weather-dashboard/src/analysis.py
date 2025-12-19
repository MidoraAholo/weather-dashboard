"""Analysis utilities for weather data.

Functions:
- get_monthly_records
- rolling_mean
- estimate_trend
- detect_heatwaves, detect_cold_spells, detect_droughts
"""
from __future__ import annotations

from typing import List, Tuple, Optional

import numpy as np
import pandas as pd

try:
    from scipy import stats
except Exception:  # pragma: no cover
    stats = None


def get_monthly_records(df: pd.DataFrame, var: str) -> pd.DataFrame:
    """Return for each month of year the record (max and min) and the date it occurred."""
    if var not in df.columns:
        raise KeyError(var)
    series = df[var].dropna()
    if series.empty:
        return pd.DataFrame()
    max_idx = series.idxmax()
    min_idx = series.idxmin()
    return pd.DataFrame({"max_value": [series.loc[max_idx]], "max_date": [max_idx], "min_value": [series.loc[min_idx]], "min_date": [min_idx]})


def rolling_mean(df: pd.DataFrame, var: str, window_days: int = 30) -> pd.Series:
    """Compute rolling mean on a daily-indexed series with window size in days."""
    s = df[var].dropna()
    if s.empty:
        return s
    # Convert window_days to number of samples assuming daily data; use time-based window
    return s.rolling(f"{window_days}D").mean()


def estimate_trend(df: pd.DataFrame, var: str, resample_rule: str = "A") -> Tuple[Optional[float], Optional[float]]:
    """Estimate linear trend (slope per year) on resampled mean series (e.g., annual).

    Returns (slope, pvalue). If scipy.stats is not available, pvalue will be None.
    """
    if var not in df.columns:
        raise KeyError(var)
    ser = df[var].dropna().resample(resample_rule).mean()
    if ser.empty or len(ser) < 2:
        return (None, None)
    years = (ser.index.year.values).astype(float)
    vals = ser.values.astype(float)
    mask = ~np.isnan(vals)
    if mask.sum() < 2:
        return (None, None)
    x = years[mask]
    y = vals[mask]
    slope, intercept = np.polyfit(x, y, 1)
    pvalue = None
    if stats is not None:
        r = stats.linregress(x, y)
        pvalue = r.pvalue
        slope = r.slope
    return slope, pvalue


def _consecutive_ranges(mask: np.ndarray) -> List[Tuple[int, int]]:
    """Return list of (start_idx, end_idx) inclusive for True runs in boolean mask."""
    ranges = []
    if not mask.any():
        return ranges
    idx = np.where(mask)[0]
    starts = [idx[0]]
    ends = []
    for i in range(1, len(idx)):
        if idx[i] != idx[i - 1] + 1:
            ends.append(idx[i - 1])
            starts.append(idx[i])
    ends.append(idx[-1])
    ranges = list(zip(starts, ends))
    return ranges


def detect_heatwaves(df: pd.DataFrame, var: str = "TMAX", percentile: float = 90.0, min_duration: int = 3) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """Detect heatwaves as runs of at least `min_duration` days with var > percentile threshold."""
    if var not in df.columns:
        raise KeyError(var)
    s = df[var]
    thresh = np.nanpercentile(s.dropna(), percentile)
    mask = s > thresh
    ranges = _consecutive_ranges(mask.values)
    results = []
    for start_i, end_i in ranges:
        if (end_i - start_i + 1) >= min_duration:
            results.append((s.index[start_i], s.index[end_i]))
    return results


def detect_cold_spells(df: pd.DataFrame, var: str = "TMIN", percentile: float = 10.0, min_duration: int = 3) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """Detect cold spells as runs of at least `min_duration` days with var < percentile threshold."""
    if var not in df.columns:
        raise KeyError(var)
    s = df[var]
    thresh = np.nanpercentile(s.dropna(), percentile)
    mask = s < thresh
    ranges = _consecutive_ranges(mask.values)
    results = []
    for start_i, end_i in ranges:
        if (end_i - start_i + 1) >= min_duration:
            results.append((s.index[start_i], s.index[end_i]))
    return results


def detect_droughts(df: pd.DataFrame, prcp_var: str = "PRCP", season_months: Tuple[int, int] = (4, 9), percentile: float = 20.0) -> pd.DataFrame:
    """Detect low-precipitation seasons. By default checks April-September cumulative precipitation.

    Returns a DataFrame with season-year and cumulative precipitation and a flag if below percentile.
    """
    if prcp_var not in df.columns:
        raise KeyError(prcp_var)
    pr = df[prcp_var].fillna(0)
    # create a season-year index: seasons starting in the first month
    months = season_months
    # Use rolling season sums per year
    seasons = []
    years = sorted(set(df.index.year))
    for y in years:
        start = pd.Timestamp(year=y, month=months[0], day=1)
        end = pd.Timestamp(year=y, month=months[1], day=1) + pd.offsets.MonthEnd(0)
        mask = (pr.index >= start) & (pr.index <= end)
        cum = pr.loc[mask].sum()
        seasons.append({"year": y, "start": start, "end": end, "precip": float(cum)})
    out = pd.DataFrame(seasons).set_index("year")
    cutoff = np.nanpercentile(out["precip"].values, percentile)
    out["is_drought"] = out["precip"] <= cutoff
    out["cutoff"] = cutoff
    return out
