import pandas as pd

def get_marks_from_google_sheets(url):
    # Зчитуємо всі аркуші (sheet_name=None повертає словник {назва_аркуша: DataFrame})
    # header=None, щоб Pandas не намагався автоматично визначити заголовки з технічних рядків
    all_sheets = pd.read_excel(url, sheet_name=None, header=None, engine='openpyxl')
    
    processed_sheets = {}

    for sheet_name, df in all_sheets.items():
        # 1. Відсікаємо перші 4 технічні рядки (індекси 0, 1, 2, 3)
        # Примітка: якщо технічних рядків рівно 3, зміни на iloc[3:]
        clean_df = df.iloc[4:].copy()
        
        # 2. Видаляємо повністю порожні рядки та стовпці, які часто залишаються в кінці таблиці
        clean_df = clean_df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        
        if not clean_df.empty:
            # 3. Встановлюємо перший стовпець (ПІБ) як індекс
            clean_df.set_index(clean_df.columns[0], inplace=True)
            
            # 4. Обробляємо порожні клітинки з оцінками (замінюємо NaN на 0)
            clean_df = clean_df.fillna(0)
            
            # О необов'язково: можна дати назву індексу
            clean_df.index.name = "Студент"
            
            processed_sheets[sheet_name] = clean_df
            
    return processed_sheets

# Приклад використання:
# Заміни 'SPREADSHEET_ID' на реальний ID вашої таблиці
spreadsheet_id = "1jUGjAlY-GWw7HXJMykaR1VatQ_g6vfw1sj6fCk354r4"
url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"

# Приклад отримання оцінок конкретного студента:
def get_student_grades(data_dict, sheet_name, student_name):
    if sheet_name in data_dict:
        df = data_dict[sheet_name]
        if student_name in df.index:
            return df.loc[student_name].tolist()
    return None

if __name__ == "__main__":
    # Тестовий запуск
    marks_data = get_marks_from_google_sheets(url)
    
    # Ім'я студента для пошуку
    target_student = "Білошапка Олександр"
    print(f"Пошук оцінок для: {target_student}\n" + "="*30)
    
    found = False
    for sheet_name in marks_data:
        grades = get_student_grades(marks_data, sheet_name, target_student)
        if grades:
            print(f"Аркуш '{sheet_name}': {grades}")
            found = True
            
    if not found:
        print(f"Студента '{target_student}' не знайдено в жодній вкладці.")
