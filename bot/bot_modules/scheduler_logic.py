import asyncio
import logging
from datetime import datetime, timedelta
import pytz
import json
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

# --- Configuration ---
TIMEZONE = 'Europe/Kyiv'
REMINDER_OFFSET_MINUTES = 10
# Assuming schedule.json is in the project root, adjust path if needed
SCHEDULE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'schedule.json')

# --- Logger setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Schedule Data Loading ---
def load_schedule_data():
    """Loads schedule data from the JSON file."""
    if not os.path.exists(SCHEDULE_FILE):
        logger.error(f"Schedule file not found at: {SCHEDULE_FILE}")
        return []
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {SCHEDULE_FILE}: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading schedule from {SCHEDULE_FILE}: {e}")
        return []

# --- Week Type Logic ---
def get_week_type(date_obj: datetime = None) -> str:
    """
    Determines if the current week is 'num' (numerator) or 'den' (denominator).
    Odd ISO week number = num (Чисельник)
    Even ISO week number = den (Знаменник)
    """
    if date_obj is None:
        date_obj = datetime.now(pytz.timezone(TIMEZONE))
    # ISO week number starts from 1
    iso_week_number = date_obj.isocalendar()[1]
    return 'num' if iso_week_number % 2 != 0 else 'den'

# --- Schedule Formatting and Retrieval ---
def format_lesson(lesson: dict) -> str:
    """Formats a single lesson into a readable string."""
    return f"{lesson['time']} - {lesson['subject']}"

def get_today_schedule_for_week_type(schedule_data: list, day_index: int, week_type: str) -> tuple[list, str]:
    """
    Retrieves and filters today's lessons based on the week type.
    Returns a list of lesson dictionaries and the Ukrainian day name.
    """
    day_info = next((item for item in schedule_data if item['day_index'] == day_index), None)
    
    if not day_info:
        return [], "Невідомий день"

    day_name_ua = day_info['day_name_ua']
    day_schedule = day_info.get('lessons', [])
    
    filtered_lessons = []
    for lesson in day_schedule:
        if lesson['type'] == 'both' or lesson['type'] == week_type:
            filtered_lessons.append(lesson)
    return filtered_lessons, day_name_ua

async def send_daily_summary_and_schedule_reminders(bot, chat_id, scheduler_instance, schedule_data):
    """
    Sends a summary of today's lessons and schedules individual reminders.
    This function is called daily by the scheduler.
    """
    kyiv_tz = pytz.timezone(TIMEZONE)
    now = datetime.now(kyiv_tz)
    day_index = now.weekday() # Monday is 0, Sunday is 6

    # We only care about Mon-Fri (0-4)
    if day_index > 4:
        logger.info(f"Сьогодні {now.strftime('%A')}, вихідний, пар немає.")
        return

    week_type = get_week_type(now)
    today_lessons, day_name_ua = get_today_schedule_for_week_type(schedule_data, day_index, week_type)

    if not today_lessons:
        message = f"Сьогодні ({day_name_ua}, {week_type.upper()}) пар немає."
        await bot.send_message(chat_id, message)
        logger.info(f"Sent daily summary (no classes) to {chat_id}")
        return

    summary_message = f"🗓️ *Розклад на сьогодні ({day_name_ua}, {week_type.upper()}):*\n\n"
    for lesson in today_lessons:
        summary_message += f"• {format_lesson(lesson)}\n"
        
        # Schedule individual reminder for this lesson
        lesson_time_str = lesson['time'] # e.g., "10:30"
        try:
            lesson_hour, lesson_minute = map(int, lesson_time_str.split(':'))
            lesson_datetime = kyiv_tz.localize(datetime(now.year, now.month, now.day, lesson_hour, lesson_minute, 0))
            reminder_datetime = lesson_datetime - timedelta(minutes=REMINDER_OFFSET_MINUTES)

            # Only schedule if reminder time is in the future relative to now
            # and not too far in the past (e.g., if the bot restarts mid-day)
            if reminder_datetime > now - timedelta(minutes=5): # Allow a small buffer for late startup
                job_id = f"reminder_{chat_id}_{day_index}_{lesson['time']}_{lesson['subject']}_{now.date()}"
                scheduler_instance.add_job(
                    send_lesson_reminder,
                    DateTrigger(run_date=reminder_datetime),
                    args=[bot, chat_id, lesson['subject'], lesson['time']],
                    id=job_id,
                    replace_existing=True # Important to replace if the bot restarts on the same day
                )
                logger.info(f"Scheduled reminder for {lesson['subject']} at {reminder_datetime} (ID: {job_id}) for chat {chat_id}")
            else:
                logger.info(f"Reminder for {lesson['subject']} at {lesson_time_str} is in the past or too close, skipping scheduling.")
        except ValueError as e:
            logger.error(f"Invalid time format for lesson {lesson['subject']}: {lesson_time_str}. Error: {e}")
        except Exception as e:
            logger.error(f"Error scheduling reminder for {lesson['subject']}: {e}")

    await bot.send_message(chat_id, summary_message, parse_mode='Markdown')
    logger.info(f"Sent daily summary and scheduled reminders for {chat_id}")


async def send_lesson_reminder(bot, chat_id, subject, lesson_time):
    """Sends a reminder for a specific lesson."""
    message = f"🔔 *Нагадування:* Через {REMINDER_OFFSET_MINUTES} хвилин починається пара: *{subject}* о {lesson_time}!"
    await bot.send_message(chat_id, message, parse_mode='Markdown')
    logger.info(f"Sent reminder for {subject} at {lesson_time} to {chat_id}")

# --- Setup Function ---
async def setup_scheduler(bot, chat_id):
    """
    Initializes and starts the scheduler, adding all necessary jobs.
    """
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    schedule_data = load_schedule_data()

    if not schedule_data:
        logger.error("Scheduler cannot be set up: schedule data is empty or failed to load.")
        return None

    # Add the main daily job that sends summary and schedules reminders
    # This job will run every weekday (Mon-Fri) at 08:30
    scheduler.add_job(
        send_daily_summary_and_schedule_reminders,
        CronTrigger(hour=8, minute=30, day_of_week='mon-fri', timezone=TIMEZONE),
        args=[bot, chat_id, scheduler, schedule_data],
        id=f'daily_schedule_and_reminders_{chat_id}', # Unique ID per chat_id
        replace_existing=True
    )
    logger.info(f"Added daily schedule and reminder job for chat {chat_id} at 08:30 Mon-Fri.")

    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler

if __name__ == "__main__":
    print("Цей файл містить логіку планувальника. Він призначений для імпорту іншими модулями.")
    print(f"Шлях до файлу розкладу: {SCHEDULE_FILE}")