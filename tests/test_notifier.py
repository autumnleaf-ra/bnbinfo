import pytest
import respx
import httpx
from src.notifier import TelegramNotifier


@pytest.mark.asyncio
async def test_telegram_notifier_dry_run():
    notifier = TelegramNotifier(dry_run=True)
    success = await notifier.send_message("<b>Hello Test</b>")
    assert success is True


@pytest.mark.asyncio
async def test_telegram_notifier_missing_creds():
    notifier = TelegramNotifier(bot_token="", chat_id="", dry_run=False)
    success = await notifier.send_message("<b>Hello Test</b>")
    assert success is False


@pytest.mark.asyncio
@respx.mock
async def test_telegram_notifier_success():
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    chat_id = "987654321"

    respx.post(f"https://api.telegram.org/bot{bot_token}/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})
    )

    notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id, dry_run=False)
    success = await notifier.send_message("<b>Hello Real Test</b>")
    assert success is True
