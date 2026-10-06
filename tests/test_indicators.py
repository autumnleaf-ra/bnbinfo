import pandas as pd
import numpy as np
from src.indicators import compute_indicators


def test_compute_indicators_empty():
    df = pd.DataFrame()
    res = compute_indicators(df)
    assert res.empty


def test_compute_indicators_calculation():
    # 60 candles dummy
    data = {
        "open_time": list(range(1000, 1060)),
        "open": [100.0 + i for i in range(60)],
        "high": [105.0 + i for i in range(60)],
        "low": [95.0 + i for i in range(60)],
        "close": [100.0 + i * 2 for i in range(60)],
        "volume": [1000.0 + (i % 5) * 100 for i in range(60)],
    }
    df = pd.DataFrame(data)

    res = compute_indicators(df, ema_fast_period=20, ema_slow_period=50, vol_ma_period=20)

    assert "ema_20" in res.columns
    assert "ema_50" in res.columns
    assert "vol_sma_20" in res.columns

    # Check non-null on tail
    assert not pd.isna(res["ema_20"].iloc[-1])
    assert not pd.isna(res["ema_50"].iloc[-1])
    assert not pd.isna(res["vol_sma_20"].iloc[-1])

    # Check SMA calculation matches manual mean
    expected_sma20 = res["volume"].iloc[-20:].mean()
    assert np.isclose(res["vol_sma_20"].iloc[-1], expected_sma20)
