import json
import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Dynamic path to the data file
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'groups.json')

# Define admin user ID (replace with actual admin ID)
# IMPORTANT: Replace this with the actual Telegram User ID of your admin.
# You can find your User ID by forwarding a message from yourself to a bot like @userinfobot.
ADMIN_ID = 123456789  # Placeholder for admin's Telegram User ID

# Initialize router for group management features
group_manager_router = Router()

# --- Data Management Functions ---
def _load_groups_data() -> dict:
    """
    Loads group data from the JSON file.
    Returns an empty dictionary if the file does not exist or is malformed.
    """
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Handle empty or malformed JSON file
            return {}

def _save_groups_data(data: dict):
    """Saves group data to the JSON file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- States for FSM (Finite State Machine) ---
class RegistrationStates(StatesGroup):
    """States for the user registration process."""
    waiting_for_group_selection = State()

class AdminNoticeStates(StatesGroup):
    """States for the admin notification feature."""
    waiting_for_target_group = State()
    waiting_for_notice_message = State()

# --- Constants for Reply Keyboards ---
GROUP_BUTTONS = ["ПЗ-23-1/9", "КМП-23-1/9", "ПЗ-22-1/9"]
GROUP_KEYBOARD = types.ReplyKeyboardMarkup(
    keyboard=[[types.KeyboardButton(text=group_name)] for group_name in GROUP_BUTTONS],
    resize_keyboard=True,
    one_time_keyboard=True
)
REMOVE_KEYBOARD = types.ReplyKeyboardRemove()

# --- Handlers ---

@group_manager_router.message(Command("start", "register"))
async def handle_registration_command(message: types.Message, state: FSMContext):
    """
    Handles the /start and /register commands.
    Checks if the user is already registered; if not, prompts for group selection.
    """
    user_id = str(message.from_user.id)
    groups_data = _load_groups_data()

    if user_id in groups_data:
        await message.answer(f"Ви вже зареєстровані в групі: {groups_data[user_id]}.", reply_markup=REMOVE_KEYBOARD)
        await state.clear()
    else:
        await message.answer(
            "Ласкаво просимо! Будь ласка, оберіть свою групу:",
            reply_markup=GROUP_KEYBOARD
        )
        await state.set_state(RegistrationStates.waiting_for_group_selection)

@group_manager_router.message(RegistrationStates.waiting_for_group_selection, F.text.in_(GROUP_BUTTONS))
async def handle_group_selection(message: types.Message, state: FSMContext):
    """
    Handles the user's group selection during registration.
    Saves the user's ID and selected group to groups.json.
    """
    user_id = str(message.from_user.id)
    selected_group = message.text
    groups_data = _load_groups_data()

    groups_data[user_id] = selected_group
    _save_groups_data(groups_data)

    await message.answer(
        f"Групу збережено – успіху! Ваша група: {selected_group}.",
        reply_markup=REMOVE_KEYBOARD
    )
    await state.clear()

@group_manager_router.message(RegistrationStates.waiting_for_group_selection)
async def handle_invalid_group_selection(message: types.Message):
    """
    Handles invalid input when the bot is waiting for group selection.
    Prompts the user to select from the provided buttons.
    """
    await message.answer(
        "Будь ласка, оберіть групу зі списку, використовуючи кнопки.",
        reply_markup=GROUP_KEYBOARD
    )

@group_manager_router.message(Command("send_notice"))
async def handle_send_notice_command(message: types.Message, state: FSMContext):
    """
    Handles the /send_notice command (admin-only).
    Prompts the admin to select a target group for the notice.
    """
    if message.from_user.id != ADMIN_ID:
        await message.answer("Ця команда доступна лише адміністраторам.", reply_markup=REMOVE_KEYBOARD)
        await state.clear()
        return

    await message.answer(
        "Оберіть групу, якій ви хочете надіслати повідомлення:",
        reply_markup=GROUP_KEYBOARD
    )
    await state.set_state(AdminNoticeStates.waiting_for_target_group)

@group_manager_router.message(AdminNoticeStates.waiting_for_target_group, F.text.in_(GROUP_BUTTONS))
async def handle_target_group_selection(message: types.Message, state: FSMContext):
    """
    Handles the admin's selection of the target group for the notice.
    Prompts the admin to send the message content.
    """
    target_group = message.text
    await state.update_data(target_group=target_group)
    await message.answer(
        f"Ви обрали групу '{target_group}'. Тепер надішліть повідомлення, яке буде розіслано цій групі.",
        reply_markup=REMOVE_KEYBOARD
    )
    await state.set_state(AdminNoticeStates.waiting_for_notice_message)

@group_manager_router.message(AdminNoticeStates.waiting_for_target_group)
async def handle_invalid_target_group_selection(message: types.Message):
    """
    Handles invalid input when the admin is waiting for target group selection.
    Prompts the admin to select from the provided buttons.
    """
    await message.answer(
        "Будь ласка, оберіть групу зі списку, використовуючи кнопки.",
        reply_markup=GROUP_KEYBOARD
    )

@group_manager_router.message(AdminNoticeStates.waiting_for_notice_message)
async def handle_notice_message(message: types.Message, state: FSMContext):
    """
    Handles the message content from the admin and broadcasts it to the selected group.
    """
    if message.from_user.id != ADMIN_ID:
        await message.answer("Ця команда доступна лише адміністраторам.", reply_markup=REMOVE_KEYBOARD)
        await state.clear()
        return

    user_data = await state.get_data()
    target_group = user_data.get("target_group")
    notice_text = message.text

    if not target_group:
        await message.answer("Помилка: Цільова група не була обрана. Будь ласка, спробуйте ще раз з /send_notice.", reply_markup=REMOVE_KEYBOARD)
        await state.clear()
        return

    groups_data = _load_groups_data()
    sent_count = 0
    for user_id_str, group_name in groups_data.items():
        if group_name == target_group:
            try:
                # aiogram handlers automatically receive the bot instance.
                # message.bot refers to the Bot instance that received the message.
                await message.bot.send_message(chat_id=int(user_id_str), text=f"Оголошення для групи {target_group}:\n\n{notice_text}")
                sent_count += 1
            except Exception as e:
                print(f"Failed to send message to user {user_id_str} in group {target_group}: {e}") # Log the error for debugging

    await message.answer(f"Повідомлення успішно надіслано {sent_count} користувачам групи '{target_group}'.", reply_markup=REMOVE_KEYBOARD)
    await state.clear()

@group_manager_router.message(AdminNoticeStates.waiting_for_notice_message)
async def handle_admin_other_messages_in_notice_state(message: types.Message):
    """
    Guides the admin if they send an unexpected message while waiting for the notice content.
    """
    if message.from_user.id == ADMIN_ID:
        await message.answer("Будь ласка, надішліть повідомлення, яке ви хочете розіслати, або скасуйте дію командою /cancel.", reply_markup=REMOVE_KEYBOARD)
    else:
        # This case should ideally not be reached if admin check is done first, but as a general fallback
        await message.answer("Невідома команда. Будь ласка, спробуйте /start або /register.", reply_markup=REMOVE_KEYBOARD)

@group_manager_router.message(Command("cancel"))
async def handle_cancel_command(message: types.Message, state: FSMContext):
    """
    Handles the /cancel command to clear any active FSM state.
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Немає активних дій для скасування.", reply_markup=REMOVE_KEYBOARD)
        return
    await state.clear()
    await message.answer("Дію скасовано.", reply_markup=REMOVE_KEYBOARD)