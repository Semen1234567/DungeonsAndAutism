import asyncio
from telegram.error import TimedOut, NetworkError
import html

async def safe_send(bot_method, *args, **kwargs):
    try:
        return await bot_method(*args, **kwargs)
    except (NetworkError, TimedOut) as e:
        print(f"⚠️ Telegram send error: {e} — retrying once...")
        await asyncio.sleep(1)
        try:
            return await bot_method(*args, **kwargs)
        except Exception as e:
            print(f"❌ Failed to send message: {e}")


def escape_html(text: str) -> str:
    return html.escape(text)