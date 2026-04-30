import random
from aiogram import Router, types
from aiogram.filters import Command

exam_predictor_router = Router()

PREDICTION_RESPONSES = [
    "Зірки кажуть так",
    "Тільки якщо виключиш Valorant",
    "Та вже пізно, запускай дотан",
    "Можливо",
    "Скинься на штори – і тоді поговоримо",
    "Рандом каже, що перездача – це теж досвід",
    "Якщо не знаєш відповіді, просто впевнено мовчи",
    "Твоя аура каже, що ти вивчиш все за 5 хвилин до початку",
    "Запитай у ChatGPT, він краще знає твої гріхи",
    "Іноді сама доля хоче тебе завалити",
    "Бог рандому сьогодні не на твоєму боці"
]

@exam_predictor_router.message(Command("will_i_pass"))
async def handle_exam_prediction_request(message: types.Message):
    selected_prediction = random.choice(PREDICTION_RESPONSES)
    await message.answer(selected_prediction)
