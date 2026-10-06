import json
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class StateStore:
    def __init__(self, filepath: str = "state.json"):
        self.filepath = filepath
        self._state: Dict[str, Any] = {
            "is_bullish": None,
            "last_candle_time": None,
            "last_updated": None,
        }
        self.load()

    def load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
                    logger.info(f"Loaded existing state from {self.filepath}: {self._state}")
            except Exception as e:
                logger.warning(f"Failed to read state file ({e}). Starting with default state.")

    def save(self) -> None:
        try:
            self._state["last_updated"] = datetime.now(timezone.utc).isoformat()
            temp_file = f"{self.filepath}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            os.replace(temp_file, self.filepath)
        except Exception as e:
            logger.error(f"Failed to save state to {self.filepath}: {e}")

    @property
    def is_bullish(self) -> Optional[bool]:
        return self._state.get("is_bullish")

    @is_bullish.setter
    def is_bullish(self, value: Optional[bool]) -> None:
        self._state["is_bullish"] = value

    @property
    def last_candle_time(self) -> Optional[int]:
        return self._state.get("last_candle_time")

    @last_candle_time.setter
    def last_candle_time(self, value: Optional[int]) -> None:
        self._state["last_candle_time"] = value
