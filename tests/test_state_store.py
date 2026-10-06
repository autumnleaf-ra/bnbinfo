import os
import json
import pytest
from src.state_store import StateStore


def test_state_store_save_and_load(tmp_path):
    state_file = str(tmp_path / "test_state.json")
    store = StateStore(filepath=state_file)

    assert store.is_bullish is None
    assert store.last_candle_time is None

    store.is_bullish = True
    store.last_candle_time = 1759724100000
    store.save()

    assert os.path.exists(state_file)

    # Re-instantiate to test loading
    store2 = StateStore(filepath=state_file)
    assert store2.is_bullish is True
    assert store2.last_candle_time == 1759724100000
