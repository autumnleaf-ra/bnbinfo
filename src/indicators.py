from typing import Optional
import pandas as pd


def compute_indicators(
    df: pd.DataFrame,
    ema_fast_period: int = 20,
    ema_slow_period: int = 50,
    vol_ma_period: int = 20,
) -> pd.DataFrame:
    """
    Computes EMA fast, EMA slow, and Volume MA (AVL) on a DataFrame of klines.
    
    Expected DataFrame columns:
    - 'open_time': timestamp (ms or datetime)
    - 'open': float
    - 'high': float
    - 'low': float
    - 'close': float
    - 'volume': float
    """
    if df.empty:
        return df

    result_df = df.copy()

    # Ensure numeric columns
    for col in ["open", "high", "low", "close", "volume"]:
        if col in result_df.columns:
            result_df[col] = pd.to_numeric(result_df[col], errors="coerce")

    # EMA standard (matches TradingView: adjust=False)
    result_df[f"ema_{ema_fast_period}"] = (
        result_df["close"].ewm(span=ema_fast_period, adjust=False).mean()
    )
    result_df[f"ema_{ema_slow_period}"] = (
        result_df["close"].ewm(span=ema_slow_period, adjust=False).mean()
    )

    # Volume Moving Average (AVL)
    result_df[f"vol_sma_{vol_ma_period}"] = (
        result_df["volume"].rolling(window=vol_ma_period).mean()
    )

    return result_df
