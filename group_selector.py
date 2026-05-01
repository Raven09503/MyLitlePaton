import json
import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

group_selector_router = Router()
GROUPS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'groups.json')

def update_user_group(user_id: int, group_name: str):
    data = {}
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except json.JSONDecodeError:
                data = {}
    
    data[str(user_id)] = group_name
    with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@group_selector_router.message(Command("group"))
async def cmd_group(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="ПЗ-23-1/9")
    builder.button(text="КМП-23-1/9")
    builder.button(text="ПЗ-22-1/9")
    builder.adjust(1)
    
    await message.answer(
        "Please select your group from the list below:",
        reply_markup=builder.as_markup(
            resize_keyboard=True, 
            one_time_keyboard=True
        )
    )

@group_selector_router.message(F.text.in_({"ПЗ-23-1/9", "КМП-23-1/9", "ПЗ-22-1/9"})) # Line 42
async def handle_group_selection(message: types.Message):
    update_user_group(message.from_user.id, message.text)
    await message.answer(
        f"Success – your group has been set to {message.text}."
    )