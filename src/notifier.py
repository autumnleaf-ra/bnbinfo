import asyncio
import logging
from typing import Optional
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self.dry_run = dry_run if dry_run is not None else settings.dry_run
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, text: str, max_retries: int = 3) -> bool:
        if self.dry_run:
            logger.info(f"[DRY-RUN] Telegram notification would be sent:\n{text}")
            return True

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot_token or chat_id is missing. Notification skipped.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload)

                    if response.status_code == 200:
                        logger.info("Telegram message successfully sent.")
                        return True
                    elif response.status_code == 429:
                        # Rate limited
                        retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                        logger.warning(f"Telegram rate limited. Retrying after {retry_after}s...")
                        await asyncio.sleep(retry_after)
                    else:
                        logger.error(
                            f"Telegram API error (status {response.status_code}): {response.text}"
                        )
            except Exception as e:
                logger.error(f"Attempt {attempt}/{max_retries} failed sending Telegram message: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 * attempt)

        return False


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    notifier = TelegramNotifier()
    sample_text = (
        "🤖 <b>Test Bot BNB/USDT Signal</b>\n"
        "Koneksi Telegram berhasil terhubung!"
    )
    success = asyncio.run(notifier.send_message(sample_text))
    if success:
        print("Pesan uji coba berhasil terkirim.")
    else:
        print("Gagal mengirim pesan uji coba. Periksa TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID.")
        sys.exit(1)
