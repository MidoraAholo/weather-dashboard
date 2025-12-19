import pandas as pd
from src.visualization import timeseries_plot, overlay_anomalies


def test_timeseries_and_overlay():
    idx = pd.date_range('2020-01-01', periods=10, freq='D')
    df = pd.DataFrame({'T': range(10)}, index=idx)
    fig = timeseries_plot(df, 'T')
    assert fig is not None
    # overlay a single anomaly
    anomalies = [(idx[2], idx[4])]
    fig2 = overlay_anomalies(fig, anomalies)
    assert fig2 is not None
