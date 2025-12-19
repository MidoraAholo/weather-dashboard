"""Visualization helpers using Plotly (interactive) and Matplotlib (fallback)."""
from __future__ import annotations

from typing import Optional, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def timeseries_plot(df: pd.DataFrame, var: str, start: Optional[pd.Timestamp] = None, end: Optional[pd.Timestamp] = None, rolling: Optional[int] = None) -> go.Figure:
    """Return a Plotly figure for the timeseries of `var`."""
    if var not in df.columns:
        raise KeyError(var)
    s = df[var].dropna()
    if start is not None:
        s = s.loc[s.index >= start]
    if end is not None:
        s = s.loc[s.index <= end]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name=var))
    if rolling is not None and rolling > 0:
        r = s.rolling(f"{rolling}D").mean()
        fig.add_trace(go.Scatter(x=r.index, y=r.values, mode="lines", name=f"{rolling}D rolling"))
    fig.update_layout(title=f"Time series of {var}", xaxis_title="Date", yaxis_title=var)
    return fig


def seasonal_boxplot(df: pd.DataFrame, var: str) -> go.Figure:
    """Boxplot by month to show seasonal distribution."""
    s = df[var].dropna().to_frame()
    s["month"] = s.index.month
    fig = px.box(s, x="month", y=var, points="outliers", labels={"month": "Month"})
    fig.update_layout(title=f"Seasonal distribution of {var}")
    return fig


def overlay_anomalies(fig: go.Figure, anomalies: List[Tuple[pd.Timestamp, pd.Timestamp]], color: str = "rgba(255,0,0,0.2)") -> go.Figure:
    """Overlay shaded regions on `fig` for each (start, end) in anomalies."""
    for start, end in anomalies:
        fig.add_vrect(x0=start, x1=end, fillcolor=color, opacity=0.5, line_width=0)
    return fig


def save_fig_html(fig: go.Figure, path: str) -> None:
    """Save a Plotly figure to an HTML file (self-contained)."""
    fig.write_html(path, include_plotlyjs="cdn")