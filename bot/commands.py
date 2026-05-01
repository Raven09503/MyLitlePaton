from .settings import bot, disp
from aiogram.filters import CommandStart
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import datetime
import pytz
from .bot_modules.std_keyboard import start_std_keyboard
#from .bot_modules.individual_marks import calculate_student_average
from .bot_modules.marks import get_marks_from_google_sheets, url, calculate_student_average, convert_to_json, get_student_grades
from .bot_modules.scheduler_logic import load_schedule_data, get_week_type, get_today_schedule_for_week_type, format_lesson

class StudentForm(StatesGroup):
    waiting_for_name = State()
    action_type = State()

@disp.message(CommandStart())
async def start(msg: types.Message):
    await bot.send_message(chat_id = msg.chat.id, text = "Hello you use my litle paton bot",reply_markup = start_std_keyboard)
    await delete(msg)

@disp.message(F.text == "Отримати розклад")
async def show_today_schedule(msg: types.Message):
    schedule_data = load_schedule_data()
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    now = datetime.datetime.now(kyiv_tz)
    
    week_type = get_week_type(now)
    day_index = now.weekday()
    
    lessons, day_name = get_today_schedule_for_week_type(schedule_data, day_index, week_type)
    
    if not lessons:
        await msg.answer(f"Сьогодні ({day_name}) занять немає.")
        return

    response = f"🗓 *Розклад на сьогодні ({day_name}):*\n\n"
    for lesson in lessons:
        response += f"• {format_lesson(lesson)}\n"
    
    await msg.answer(response, parse_mode="Markdown")

@disp.message(F.text == "Отримати оцінки")
async def request_name_for_average(msg: types.Message, state: FSMContext):
    await state.set_state(StudentForm.waiting_for_name)
    await state.update_data(action_type="average")
    await msg.answer("Будь ласка, введіть ПІБ студента (наприклад: Олійник Андрій):")

@disp.message(F.text == "Оцінки по кожному предмету")
async def request_name_for_detailed(msg: types.Message, state: FSMContext):
    await state.set_state(StudentForm.waiting_for_name)
    await state.update_data(action_type="detailed")
    await msg.answer("Введіть ПІБ студента для отримання детальних оцінок:")

@disp.message(StudentForm.waiting_for_name)
async def process_student_name(msg: types.Message, state: FSMContext):
    student_name = msg.text.strip()
    user_data = await state.get_data()
    action = user_data.get("action_type")
    
    await state.clear() # Очищуємо стан після отримання імені
    
    marks_data = get_marks_from_google_sheets(url)
    
    if action == "average":
        averages = calculate_student_average(marks_data, student_name)
        if not averages:
            await msg.answer(f"Дані для студента '{student_name}' не знайдені.")
            return

        response = f"📊 *Середні бали ({student_name}):*\n\n"
        for subject, avg in averages.items():
            response += f"• {subject}: {avg}\n"
        await msg.answer(response, parse_mode="Markdown")
        
    elif action == "detailed":
        response = f"📝 *Детальні оцінки ({student_name}):*\n\n"
        found = False
        for sheet_name in marks_data:
            grades = get_student_grades(marks_data, sheet_name, student_name)
            if grades:
                found = True
                # Відфільтровуємо 0 або порожні значення, якщо потрібно
                grades_str = ", ".join(map(str, [g for g in grades if g != 0]))
                response += f"📘 *{sheet_name}*: {grades_str if grades_str else 'немає оцінок'}\n"
        
        if not found:
            await msg.answer(f"Дані для студента '{student_name}' не знайдені.")
        else:
            await msg.answer(response, parse_mode="Markdown")

async def delete(msg: types.Message):
    await bot.delete_message(chat_id = msg.chat.id, message_id = msg.message_id )