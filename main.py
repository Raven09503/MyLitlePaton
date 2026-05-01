import asyncio
import logging
from bot.settings import bot, disp

async def main():
    # Включаємо логування, щоб бачити помилки та стан бота в консолі
    logging.basicConfig(level=logging.INFO)
    await disp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())