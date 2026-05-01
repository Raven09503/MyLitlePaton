import json
import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.settings import bot

ADMIN_ID = 5416300111
admin_broadcast_router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_target = State()
    waiting_for_message = State()

GROUPS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'groups.json')

def get_broadcast_data():
    if not os.path.exists(GROUPS_FILE): return {}
    with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_chat_id(chat_id: int):
    data = {}
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: pass
    
    if str(chat_id) not in data:
        data[str(chat_id)] = "Unknown"
        with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

@admin_broadcast_router.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def cmd_broadcast(message: types.Message, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    for option in ["Всім", "ПЗ-23-1/9", "КМП-23-1/9", "ПЗ-22-1/9"]:
        builder.button(text=option)
    builder.adjust(2)
    
    await message.answer(
        "Select the target audience for the broadcast:",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.set_state(BroadcastStates.waiting_for_target)

@admin_broadcast_router.message(BroadcastStates.waiting_for_target, F.from_user.id == ADMIN_ID)
async def process_target_selection(message: types.Message, state: FSMContext):
    await state.update_data(target=message.text)
    await message.answer(f"Target selected: {message.text}\nNow send the message content.", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(BroadcastStates.waiting_for_message)

@admin_broadcast_router.message(BroadcastStates.waiting_for_message, F.from_user.id == ADMIN_ID)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("target")
    await state.clear()
    
    raw_text = message.text
    formatted_text = raw_text.replace('—', '–')
    content = f"<b>📢 Повідомлення від адміністрації</b>\n\n{formatted_text}"

    all_users = get_broadcast_data()
    targets = []

    match target:
        case "Всім":
            targets = list(all_users.keys())
        case group if group in ["ПЗ-23-1/9", "КМП-23-1/9", "ПЗ-22-1/9"]:
            targets = [uid for uid, gname in all_users.items() if gname == group]
        case _:
            await message.answer("Invalid target selected.")
            return

    sent_count = 0
    blocked_count = 0

    for chat_id in targets:
        try:
            await bot.send_message(chat_id=chat_id, text=content, parse_mode="HTML")
            sent_count += 1
        except TelegramForbiddenError:
            blocked_count += 1
        except Exception:
            pass

    await message.answer(
        f"Broadcast finished.\nTarget: {target}\nSent: {sent_count}\nBlocked: {blocked_count}"
    )

@admin_broadcast_router.message(Command("broadcast"))
async def cmd_broadcast_non_admin(message: types.Message):
    await message.answer("Access denied.")