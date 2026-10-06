from src.signal import (
    evaluate_signal,
    detect_transition,
    build_telegram_message,
)


def test_evaluate_signal_bullish():
    sig = evaluate_signal(
        close=620.0,
        ema_fast=600.0,
        ema_slow=590.0,
        volume=1500.0,
        volume_avg=1000.0,
        timestamp_ms=1759724100000,
    )
    assert sig.above_ema_fast is True
    assert sig.above_ema_slow is True
    assert sig.volume_above_avg is True
    assert sig.is_bullish is True


def test_evaluate_signal_not_bullish_when_volume_low():
    sig = evaluate_signal(
        close=620.0,
        ema_fast=600.0,
        ema_slow=590.0,
        volume=800.0,
        volume_avg=1000.0,
        timestamp_ms=1759724100000,
    )
    assert sig.above_ema_fast is True
    assert sig.above_ema_slow is True
    assert sig.volume_above_avg is False
    assert sig.is_bullish is False


def test_evaluate_signal_not_bullish_when_below_ema():
    sig = evaluate_signal(
        close=595.0,
        ema_fast=600.0,
        ema_slow=590.0,
        volume=1500.0,
        volume_avg=1000.0,
        timestamp_ms=1759724100000,
    )
    assert sig.above_ema_fast is False
    assert sig.is_bullish is False


def test_detect_transition():
    # Bootstrap / First run: no transition
    assert detect_transition(None, True) is None
    assert detect_transition(None, False) is None

    # False -> True (ACTIVATED)
    assert detect_transition(False, True) == "ACTIVATED"

    # True -> False (DEACTIVATED)
    assert detect_transition(True, False) == "DEACTIVATED"

    # No change
    assert detect_transition(True, True) is None
    assert detect_transition(False, False) is None


def test_build_telegram_message():
    sig_bullish = evaluate_signal(
        close=615.50,
        ema_fast=610.00,
        ema_slow=605.00,
        volume=25000.0,
        volume_avg=15000.0,
        timestamp_ms=1759724100000,
    )
    msg_act = build_telegram_message("ACTIVATED", sig_bullish)
    assert "SINYAL BULLISH AKTIF" in msg_act
    assert "615.50" in msg_act
    assert "EMA 20" in msg_act

    sig_bearish = evaluate_signal(
        close=608.00,
        ema_fast=610.00,
        ema_slow=605.00,
        volume=10000.0,
        volume_avg=15000.0,
        timestamp_ms=1759724100000,
    )
    msg_deact = build_telegram_message("DEACTIVATED", sig_bearish)
    assert "SINYAL BATAL" in msg_deact
    assert "Close di bawah EMA 20" in msg_deact
    assert "Volume di bawah rata-rata" in msg_deact
