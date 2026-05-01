from .settings import bot, disp
from aiogram.filters import CommandStart, Command
import aiogram
from admin_broadcast import save_chat_id

@disp.message(CommandStart())
async def start(msg: aiogram.types.Message):
    save_chat_id(msg.chat.id)
    await bot.send_message(chat_id = msg.chat.id, text = "Hello you use my litle paton bot")
    await delete(msg)
    
async def delete( msg: aiogram.types.Message):
    await bot.delete_message(chat_id = msg.chat.id, message_id = msg.message_id )
