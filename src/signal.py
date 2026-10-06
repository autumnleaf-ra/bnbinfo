from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime, timezone, timedelta

SignalTransition = Literal["ACTIVATED", "DEACTIVATED"]


@dataclass
class SignalResult:
    close: float
    ema_fast: float
    ema_slow: float
    volume: float
    volume_avg: float
    timestamp_ms: int

    @property
    def above_ema_fast(self) -> bool:
        return self.close > self.ema_fast

    @property
    def above_ema_slow(self) -> bool:
        return self.close > self.ema_slow

    @property
    def volume_above_avg(self) -> bool:
        return self.volume > self.volume_avg

    @property
    def is_bullish(self) -> bool:
        return self.above_ema_fast and self.above_ema_slow and self.volume_above_avg


def evaluate_signal(
    close: float,
    ema_fast: float,
    ema_slow: float,
    volume: float,
    volume_avg: float,
    timestamp_ms: int,
) -> SignalResult:
    return SignalResult(
        close=close,
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        volume=volume,
        volume_avg=volume_avg,
        timestamp_ms=timestamp_ms,
    )


def detect_transition(
    prev_state: Optional[bool],
    current_state: bool,
) -> Optional[SignalTransition]:
    """
    Detects transition between bullish states:
    - False -> True: ACTIVATED
    - True -> False: DEACTIVATED
    - None -> True/False: Returns None (initial bootstrap, avoid false trigger)
    """
    if prev_state is None:
        return None
    if not prev_state and current_state:
        return "ACTIVATED"
    if prev_state and not current_state:
        return "DEACTIVATED"
    return None


def format_wib_time(timestamp_ms: int) -> str:
    """Formats epoch ms to UTC+7 (WIB)."""
    tz_wib = timezone(timedelta(hours=7))
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc).astimezone(tz_wib)
    return dt.strftime("%Y-%m-%d %H:%M:%S WIB")


def build_telegram_message(
    transition: SignalTransition,
    signal: SignalResult,
    symbol: str = "BNB/USDT",
    interval: str = "15m",
    fast_period: int = 20,
    slow_period: int = 50,
) -> str:
    time_str = format_wib_time(signal.timestamp_ms)
    vol_ratio = (signal.volume / signal.volume_avg) if signal.volume_avg > 0 else 0.0

    if transition == "ACTIVATED":
        return (
            f"🟢 <b>{symbol} — SINYAL BULLISH AKTIF ({interval})</b>\n\n"
            f"💰 <b>Close</b>: <code>{signal.close:,.2f}</code>\n"
            f"📈 <b>EMA {fast_period}</b>: <code>{signal.ema_fast:,.2f}</code> ✅ <i>(Price di atas EMA)</i>\n"
            f"📈 <b>EMA {slow_period}</b>: <code>{signal.ema_slow:,.2f}</code> ✅ <i>(Price di atas EMA)</i>\n"
            f"📊 <b>Volume</b>: <code>{signal.volume:,.2f}</code> vs Avg: <code>{signal.volume_avg:,.2f}</code> ✅ <i>({vol_ratio:.2f}x)</i>\n\n"
            f"🕒 <b>Waktu Candle</b>: <code>{time_str}</code>"
        )
    else:  # DEACTIVATED
        failed_reasons = []
        if not signal.above_ema_fast:
            failed_reasons.append(f"❌ Close di bawah EMA {fast_period} ({signal.close:,.2f} &lt;= {signal.ema_fast:,.2f})")
        if not signal.above_ema_slow:
            failed_reasons.append(f"❌ Close di bawah EMA {slow_period} ({signal.close:,.2f} &lt;= {signal.ema_slow:,.2f})")
        if not signal.volume_above_avg:
            failed_reasons.append(f"❌ Volume di bawah rata-rata ({signal.volume:,.2f} &lt;= {signal.volume_avg:,.2f})")

        reasons_text = "\n".join(failed_reasons)
        return (
            f"🔴 <b>{symbol} — SINYAL BATAL / BERAKHIR ({interval})</b>\n\n"
            f"💰 <b>Close Terakhir</b>: <code>{signal.close:,.2f}</code>\n"
            f"<b>Penyebab Pembatalan:</b>\n{reasons_text}\n\n"
            f"🕒 <b>Waktu Candle</b>: <code>{time_str}</code>"
        )
