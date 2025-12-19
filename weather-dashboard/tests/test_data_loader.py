import pandas as pd
from pathlib import Path
from src.data_loader import load_cambridge_data


def test_load_simple_csv(tmp_path):
    data = "date,T,TMIN,TMAX,PRCP\n2020-01-01,5,1,9,0.0\n2020-01-02,6,2,10,0.1\n"
    p = tmp_path / "cam.csv"
    p.write_text(data)
    df = load_cambridge_data(str(p))
    assert isinstance(df, pd.DataFrame)
    assert 'T' in df.columns
    assert len(df) == 2
