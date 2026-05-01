import aiogram

bot = aiogram.Bot(token = "8629557378:AAFZk0hFxs2u2BhRk8Rf6FruKy6VSmDiAMM")

disp = aiogram.Dispatcher()

from .commands import *
