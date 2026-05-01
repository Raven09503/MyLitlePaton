import aiogram
import asyncio
bot = aiogram.Bot(token = "8629557378:AAFZk0hFxs2u2BhRk8Rf6FruKy6VSmDiAMM")

disp = aiogram.Dispatcher()

from .commands import *
<<<<<<< HEAD
from admin_broadcast import admin_broadcast_router
from group_selector import group_selector_router

disp.include_router(admin_broadcast_router)
disp.include_router(group_selector_router)

async def main():
    await disp.start_polling(bot)
asyncio.run(main())
=======
>>>>>>> 9e0e5b150fbf8cc5108101823c37a8446d4a7d7f
