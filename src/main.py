import asyncio
import signal
import logging
import pandas as pd

from src.config import settings
from src.binance_client import BinanceClient
from src.indicators import compute_indicators
from src.signal import evaluate_signal, detect_transition, build_telegram_message
from src.state_store import StateStore
from src.notifier import TelegramNotifier

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


class SignalBot:
    def __init__(self):
        self.state_store = StateStore(filepath=settings.state_file)
        self.notifier = TelegramNotifier()
        self.client = BinanceClient(symbol=settings.symbol, interval=settings.interval)
        self.candles_df = pd.DataFrame()
        self._running = True

    async def initialize_buffer(self) -> None:
        """Loads historical candles to warm up the EMA and Volume MA indicators."""
        logger.info(f"Bootstrapping historical candles (limit={settings.history_limit})...")
        klines = await self.client.fetch_klines(limit=settings.history_limit)
        self.candles_df = pd.DataFrame(klines)

        # Compute initial indicators
        computed = compute_indicators(
            self.candles_df,
            ema_fast_period=settings.ema_fast,
            ema_slow_period=settings.ema_slow,
            vol_ma_period=settings.volume_ma_period,
        )

        last_row = computed.iloc[-1]
        sig = evaluate_signal(
            close=float(last_row["close"]),
            ema_fast=float(last_row[f"ema_{settings.ema_fast}"]),
            ema_slow=float(last_row[f"ema_{settings.ema_slow}"]),
            volume=float(last_row["volume"]),
            volume_avg=float(last_row[f"vol_sma_{settings.volume_ma_period}"]),
            timestamp_ms=int(last_row["open_time"]),
        )

        logger.info(
            f"Bootstrap complete. Last candle: close={sig.close:.2f}, "
            f"EMA{settings.ema_fast}={sig.ema_fast:.2f}, EMA{settings.ema_slow}={sig.ema_slow:.2f}, "
            f"Vol={sig.volume:.2f}, VolAvg={sig.volume_avg:.2f}, Bullish={sig.is_bullish}"
        )

        # If state doesn't have an initial value, set it without sending alert
        if self.state_store.is_bullish is None:
            self.state_store.is_bullish = sig.is_bullish
            self.state_store.last_candle_time = sig.timestamp_ms
            self.state_store.save()
            logger.info(f"Initialized state: is_bullish={sig.is_bullish}")

    async def process_closed_candle(self, candle: dict) -> None:
        open_time = candle["open_time"]

        # Prevent duplicate evaluation of the same candle
        if self.state_store.last_candle_time == open_time:
            logger.debug(f"Candle {open_time} already processed. Skipping.")
            return

        # Append new candle to buffer
        new_row = pd.DataFrame([candle])
        self.candles_df = pd.concat([self.candles_df, new_row], ignore_index=True)

        # Maintain buffer size to prevent memory bloat
        if len(self.candles_df) > settings.history_limit:
            self.candles_df = self.candles_df.iloc[-settings.history_limit:].reset_index(drop=True)

        # Recalculate indicators
        computed = compute_indicators(
            self.candles_df,
            ema_fast_period=settings.ema_fast,
            ema_slow_period=settings.ema_slow,
            vol_ma_period=settings.volume_ma_period,
        )

        last_row = computed.iloc[-1]
        signal_result = evaluate_signal(
            close=float(last_row["close"]),
            ema_fast=float(last_row[f"ema_{settings.ema_fast}"]),
            ema_slow=float(last_row[f"ema_{settings.ema_slow}"]),
            volume=float(last_row["volume"]),
            volume_avg=float(last_row[f"vol_sma_{settings.volume_ma_period}"]),
            timestamp_ms=int(last_row["open_time"]),
        )

        current_bullish = signal_result.is_bullish
        prev_bullish = self.state_store.is_bullish

        logger.info(
            f"Evaluation: Close={signal_result.close:.2f} | "
            f"EMA{settings.ema_fast}={signal_result.ema_fast:.2f} (above: {signal_result.above_ema_fast}) | "
            f"EMA{settings.ema_slow}={signal_result.ema_slow:.2f} (above: {signal_result.above_ema_slow}) | "
            f"Vol={signal_result.volume:.2f} vs Avg={signal_result.volume_avg:.2f} (above: {signal_result.volume_above_avg}) | "
            f"Status={current_bullish} (prev: {prev_bullish})"
        )

        transition = detect_transition(prev_bullish, current_bullish)
        if transition:
            logger.info(f"Transition detected: {transition}. Sending notification...")
            msg = build_telegram_message(
                transition=transition,
                signal=signal_result,
                symbol=f"{settings.symbol[:3]}/{settings.symbol[3:]}",
                interval=settings.interval,
                fast_period=settings.ema_fast,
                slow_period=settings.ema_slow,
            )
            await self.notifier.send_message(msg)

        # Update and save state
        self.state_store.is_bullish = current_bullish
        self.state_store.last_candle_time = open_time
        self.state_store.save()

    async def run(self) -> None:
        await self.initialize_buffer()

        logger.info(f"Starting real-time candle listener for {settings.symbol} ({settings.interval})...")
        async for closed_candle in self.client.stream_closed_klines():
            if not self._running:
                break
            await self.process_closed_candle(closed_candle)

    def stop(self) -> None:
        logger.info("Stopping Signal Bot...")
        self._running = False


async def main():
    bot = SignalBot()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, bot.stop)
        except NotImplementedError:
            # Fallback for platforms where signal handlers are restricted
            pass

    try:
        await bot.run()
    except asyncio.CancelledError:
        logger.info("Bot execution cancelled.")


if __name__ == "__main__":
    asyncio.run(main())
