from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

button_marks = KeyboardButton(text = "Отримати оцінки",)
button_individualmarks = KeyboardButton(text = "Оцінки по кожному предмету")
button_shedule =   KeyboardButton(text = "Отримати розклад")

buttons_list = [[button_marks, button_individualmarks], [button_shedule]]

start_std_keyboard = ReplyKeyboardMarkup(keyboard=buttons_list, resize_keyboard=True)
