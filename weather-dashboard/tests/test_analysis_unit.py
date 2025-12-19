import pandas as pd
import numpy as np

from src.analysis import rolling_mean, detect_heatwaves, detect_cold_spells, estimate_trend


def make_series(start='2000-01-01', periods=365*3):
    idx = pd.date_range(start, periods=periods, freq='D')
    # create a sinusoidal temperature + trend
    t = 10 + 10 * np.sin(2 * np.pi * idx.dayofyear / 365) + 0.01 * (idx.year - 2000)
    pr = np.random.RandomState(0).poisson(1, size=len(idx)).astype(float)
    df = pd.DataFrame({'T': t, 'TMIN': t - 5, 'TMAX': t + 5, 'PRCP': pr}, index=idx)
    return df


def test_rolling_mean():
    df = make_series()
    r = rolling_mean(df, 'T', window_days=30)
    assert r.isna().sum() < len(r)
    assert len(r) == len(df)


def test_heatwaves_and_coldspells():
    df = make_series()
    hw = detect_heatwaves(df, var='TMAX', percentile=95.0, min_duration=2)
    cs = detect_cold_spells(df, var='TMIN', percentile=5.0, min_duration=2)
    assert isinstance(hw, list)
    assert isinstance(cs, list)


def test_estimate_trend():
    df = make_series()
    slope, p = estimate_trend(df, 'T', resample_rule='A')
    assert slope is not None
