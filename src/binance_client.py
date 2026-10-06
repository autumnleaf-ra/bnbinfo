import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
import websockets

from src.config import settings

logger = logging.getLogger(__name__)


class BinanceClient:
    def __init__(
        self,
        symbol: Optional[str] = None,
        interval: Optional[str] = None,
        rest_base_url: Optional[str] = None,
        ws_base_url: Optional[str] = None,
    ):
        self.symbol = (symbol or settings.symbol).upper()
        self.interval = (interval or settings.interval).lower()
        self.rest_base_url = rest_base_url or settings.binance_rest_url
        self.ws_base_url = ws_base_url or settings.binance_ws_url

    async def fetch_klines(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Fetches historical klines via Binance REST API.
        
        Returns a list of dicts:
        [{ 'open_time': int, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': float, 'close_time': int }]
        """
        url = f"{self.rest_base_url}/api/v3/klines"
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": limit,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        klines = []
        for item in data:
            klines.append({
                "open_time": int(item[0]),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
                "close_time": int(item[6]),
            })
        logger.info(f"Fetched {len(klines)} historical candles for {self.symbol} {self.interval}.")
        return klines

    async def stream_closed_klines(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Connects to Binance WebSocket and yields only closed candles.
        Automatically handles reconnection with exponential backoff.
        """
        stream_name = f"{self.symbol.lower()}@kline_{self.interval}"
        ws_url = f"{self.ws_base_url}/{stream_name}"
        reconnect_delay = 2

        while True:
            try:
                logger.info(f"Connecting to Binance WebSocket: {ws_url}")
                async with websockets.connect(
                    ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                ) as ws:
                    logger.info("WebSocket connected. Listening for closed candles...")
                    reconnect_delay = 2  # Reset delay upon successful connection

                    async for message in ws:
                        payload = json.loads(message)
                        kline_data = payload.get("k", {})
                        is_closed = kline_data.get("x", False)

                        if is_closed:
                            candle = {
                                "open_time": int(kline_data.get("t")),
                                "open": float(kline_data.get("o")),
                                "high": float(kline_data.get("h")),
                                "low": float(kline_data.get("l")),
                                "close": float(kline_data.get("c")),
                                "volume": float(kline_data.get("v")),
                                "close_time": int(kline_data.get("T")),
                            }
                            logger.info(
                                f"Candle closed [{self.symbol} {self.interval}] "
                                f"Close={candle['close']} Volume={candle['volume']}"
                            )
                            yield candle

            except asyncio.CancelledError:
                logger.info("WebSocket stream cancelled.")
                break
            except Exception as e:
                logger.warning(
                    f"WebSocket connection lost: {e}. Reconnecting in {reconnect_delay}s..."
                )
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)
