import pandas as pd
import requests
import json
import os
import io
import re
from datetime import datetime

# Шлях до нашого JSON-файлу
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')

def sync_data():
    """Завантажує дані з Google Таблиці, парсить студентів та шукає дедлайни."""
    sheet_id = "1jUGjAlY-GWw7HXJMykaR1VatQ_g6vfw1sj6fCk354r4"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    print("⏳ Завантаження даних з Google Таблиці... Це може зайняти кілька секунд.")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        xls = pd.ExcelFile(io.BytesIO(response.content))
    except Exception as e:
        return f"❌ Помилка з'єднання: {e}"

    new_students_data = {}
    new_deadlines = []
    
    for subject in xls.sheet_names:
        # Ігноруємо непотрібні аркуші
        if subject in ["СемЕкЗал)))", "Класна година", "Рубіжне оцінювання"]:
            continue
            
        try:
            df = pd.read_excel(xls, sheet_name=subject, header=None)
            
            # --- КРОК 1: ПАРСИНГ ДЕДЛАЙНІВ (Рядок 4 в таблиці = індекс 3) ---
            if len(df) > 3:
                for col_idx in range(1, len(df.columns)):
                    val = df.iloc[3, col_idx] # Рядок 4: "коли здавати"
                    date_str = None
                    
                    if pd.notna(val):
                        # Якщо pandas перетворив це на об'єкт дати/часу
                        if isinstance(val, (pd.Timestamp, datetime)):
                            date_str = val.strftime("%d.%m.%Y")
                        else:
                            # Якщо це лишилося текстом
                            val_str = str(val).strip()
                            match = re.search(r'\b(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?\b', val_str)
                            if match:
                                d, m, y = match.groups()
                                # Додаємо нулі на початку, якщо число однозначне (напр. 5.04 -> 05.04)
                                d = d.zfill(2)
                                m = m.zfill(2)
                                if not y:
                                    y = str(datetime.now().year)
                                elif len(y) == 2:
                                    y = "20" + y
                                date_str = f"{d}.{m}.{y}"
                                
                    # Якщо ми успішно витягли дату дедлайну
                    if date_str:
                        # Шукаємо назву завдання вище (рядки 1 або 2)
                        task_name = str(df.iloc[0, col_idx]).strip()
                        if not task_name or task_name == 'nan':
                            task_name = str(df.iloc[1, col_idx]).strip()
                        if not task_name or task_name == 'nan':
                            task_name = "Завдання"
                                
                        # Запобігаємо дублям
                        if not any(d['subject'] == subject and d['due_date'] == date_str for d in new_deadlines):
                            new_deadlines.append({
                                "subject": subject,
                                "task": task_name,
                                "due_date": date_str,
                                "alert_days": 2 # Попередження за 2 дні
                            })

            # --- КРОК 2: ПАРСИНГ СТУДЕНТІВ (Починаємо суворо з рядка 5) ---
            for index in range(4, len(df)):
                row = df.iloc[index]
                student_name = str(row[0]).strip()
                
                if not student_name or student_name == 'nan': 
                    continue
                    
                if " " in student_name and len(student_name) > 5 and not student_name.startswith("202"):
                    if student_name not in new_students_data:
                        new_students_data[student_name] = {}
                    
                    if subject not in new_students_data[student_name]:
                        new_students_data[student_name][subject] = []
                    
                    for val in row[1:]:
                        try:
                            grade = float(val)
                            if pd.notna(grade) and 1 <= grade <= 100: 
                                new_students_data[student_name][subject].append(int(grade))
                        except (ValueError, TypeError):
                            pass 
        except Exception as e:
            print(f"⚠️ Помилка обробки аркуша '{subject}': {e}")

    # --- КРОК 3: ПЕРЕЗАПИС JSON ---
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"students": {}, "deadlines": []}
        
    # ЖОРСТКО замінюємо старих студентів і старі дедлайни на нові
    data["students"] = new_students_data
    data["deadlines"] = new_deadlines 
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return f"✅ Успішно оновлено! Студентів: {len(new_students_data)}. Знайдено дедлайнів з таблиці: {len(new_deadlines)}."