import json
import os
from datetime import datetime

# Динамічний шлях до файлу з даними
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')

def _load_data() -> dict:
    """Допоміжна функція для завантаження даних із JSON."""
    if not os.path.exists(DATA_FILE):
        return {"students": {}, "deadlines": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_data(data: dict):
    """Допоміжна функція для збереження даних у JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _find_key_case_insensitive(dictionary: dict, search_key: str):
    """Шукає оригінальний ключ у словнику без чутливості до регістру та пробілів."""
    search_lower = search_key.strip().lower()
    for key in dictionary.keys():
        if key.strip().lower() == search_lower:
            return key
    return None

def get_all_deadlines() -> list:
    """Повертає список усіх дедлайнів."""
    data = _load_data()
    return data.get("deadlines", [])

def get_hot_deadlines() -> list:
    """Повертає дедлайни, які 'горять' (кількість днів до здачі <= alert_days)."""
    data = _load_data()
    deadlines = data.get("deadlines", [])
    hot_deadlines = []
    today = datetime.now().date()

    for d in deadlines:
        try:
            due_date = datetime.strptime(d["due_date"], "%d.%m.%Y").date()
            delta_days = (due_date - today).days
            
            # Якщо дедлайн ще не минув і вписується в кількість alert_days
            if 0 <= delta_days <= d.get("alert_days", 1):
                d_copy = d.copy()
                d_copy["days_left"] = delta_days
                hot_deadlines.append(d_copy)
        except ValueError:
            continue # Ігноруємо неправильний формат дати

    return hot_deadlines

def add_deadline(subject: str, task: str, due_date: str, alert_days: int) -> str:
    """Додає новий дедлайн. Валідує дату."""
    try:
        datetime.strptime(due_date.strip(), "%d.%m.%Y")
    except ValueError:
        return "Помилка: Неправильний формат дати. Використовуйте ДД.ММ.РРРР."

    data = _load_data()
    new_deadline = {
        "subject": subject.strip(),
        "task": task.strip(),
        "due_date": due_date.strip(),
        "alert_days": int(alert_days)
    }
    data.setdefault("deadlines", []).append(new_deadline)
    _save_data(data)
    
    return f"Успіх: Дедлайн для '{task}' успішно додано!"

def add_grade(student_name: str, subject: str, grade: int) -> str:
    """Додає оцінку студенту з перевіркою валідності (від 1 до 5) та регістру."""
    try:
        grade = int(grade)
        if not (1 <= grade <= 5):
            return "Помилка: Оцінка має бути числом від 1 до 5."
    except ValueError:
        return "Помилка: Оцінка має бути цілим числом."

    data = _load_data()
    students = data.get("students", {})

    # Пошук студента
    real_student_name = _find_key_case_insensitive(students, student_name)
    if not real_student_name:
        return f"Помилка: Студента '{student_name}' не знайдено."

    # Пошук предмета
    student_data = students[real_student_name]
    real_subject = _find_key_case_insensitive(student_data, subject)
    if not real_subject:
        return f"Помилка: Предмет '{subject}' не знайдено у студента {real_student_name}."

    # Додавання оцінки
    student_data[real_subject].append(grade)
    _save_data(data)
    return f"Успіх: Оцінку {grade} успішно додано студенту {real_student_name} з предмета {real_subject}."

def get_subject_rating(subject: str):
    """
    Повертає рейтинг студентів з конкретного предмета.
    Розраховує середній бал тільки за наявності мінімум  оцінок.
    """
    data = _load_data()
    students = data.get("students", {})
    
    # Визначаємо оригінальну назву предмета (перевіряємо по першому студенту)
    real_subject = None
    for s_data in students.values():
        real_subject = _find_key_case_insensitive(s_data, subject)
        if real_subject: 
            break

    if not real_subject:
        return f"Помилка: Предмет '{subject}' не знайдено в базі."

    ratings = {}
    for student, subjects in students.items():
        if real_subject in subjects:
            grades = subjects[real_subject]
            if len(grades) >= 3:
                avg = sum(grades) / len(grades)
                ratings[student] = f"{avg:.2f}"
            else:
                ratings[student] = "Не набрано мінімум оцінок для розрахунку"

    return {"subject": real_subject, "ratings": ratings}