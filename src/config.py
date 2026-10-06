from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    symbol: str = Field(default="BNBUSDT", alias="SYMBOL")
    interval: str = Field(default="15m", alias="INTERVAL")

    ema_fast: int = Field(default=20, alias="EMA_FAST")
    ema_slow: int = Field(default=50, alias="EMA_SLOW")
    volume_ma_period: int = Field(default=20, alias="VOLUME_MA_PERIOD")
    history_limit: int = Field(default=200, alias="HISTORY_LIMIT")

    state_file: str = Field(default="state.json", alias="STATE_FILE")
    dry_run: bool = Field(default=False, alias="DRY_RUN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API Endpoints (Binance Vision public endpoints by default to avoid regional ISP block)
    binance_rest_url: str = Field(
        default="https://data-api.binance.vision", alias="BINANCE_REST_URL"
    )
    binance_ws_url: str = Field(
        default="wss://data-stream.binance.vision/ws", alias="BINANCE_WS_URL"
    )


settings = Settings()
