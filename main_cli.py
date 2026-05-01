import db_manager

def print_hot_deadlines():
    """Виводить гарячі дедлайни, якщо вони є."""
    hot = db_manager.get_hot_deadlines()
    if hot:
        print("\n" + "="*40)
        print("🔥 УВАГА! ДЕДЛАЙНИ, ЩО ГОРЯТЬ! 🔥")
        for d in hot:
            days = d['days_left']
            day_word = "днів" if days > 1 else "день" if days == 1 else "сьогодні!"
            time_left = f"Залишилось: {days} {day_word}" if days > 0 else "Здати потрібно СЬОГОДНІ!"
            
            print(f"- {d['subject']}: {d['task']} (До: {d['due_date']}) | {time_left}")
        print("="*40 + "\n")

def menu():
    while True:
        # При кожному показі меню відображаємо гарячі дедлайни
        print_hot_deadlines()
        
        print("=== СТУДЕНТСЬКИЙ ТРЕКЕР ===")
        print("1. Показати всі дедлайни")
        print("2. Додати дедлайн")
        print("3. Додати оцінку")
        print("4. Рейтинг з предмета")
        print("5. Синхронізувати з Google Таблицею") # НОВИЙ РЯДОК
        print("0. Вихід")
        
        choice = input("Оберіть дію: ").strip()

        if choice == '1':
            deadlines = db_manager.get_all_deadlines()
            print("\n--- Всі дедлайни ---")
            if not deadlines:
                print("Дедлайнів поки немає.")
            for d in deadlines:
                print(f"[{d['due_date']}] {d['subject']} - {d['task']} (Сповіщення за {d['alert_days']} дн.)")
            print("-" * 20 + "\n")

        elif choice == '2':
            print("\n--- Додавання дедлайну ---")
            subject = input("Предмет (ООП, Основи філософських знань, Фізичне виховання): ")
            task = input("Завдання (напр. Лабораторна 1): ")
            due_date = input("Дата здачі (ДД.ММ.РРРР): ")
            alert_days = input("За скільки днів попередити (число): ")
            
            if alert_days.isdigit():
                response = db_manager.add_deadline(subject, task, due_date, int(alert_days))
                print(f"\n{response}\n")
            else:
                print("\nПомилка: Дні сповіщення мають бути числом.\n")

        elif choice == '3':
            print("\n--- Додавання оцінки ---")
            student = input("Ім'я студента: ")
            subject = input("Предмет: ")
            grade = input("Оцінка (1-5): ")
            
            response = db_manager.add_grade(student, subject, grade)
            print(f"\n{response}\n")

        elif choice == '4':
            print("\n--- Рейтинг з предмета ---")
            subject = input("Введіть предмет: ")
            result = db_manager.get_subject_rating(subject)
            
            if isinstance(result, str):
                # Це означає, що повернулась помилка
                print(f"\n{result}\n")
            else:
                # Це успішний словник з рейтингами
                print(f"\nРейтинг з предмета: {result['subject']}")
                for student, rating in result['ratings'].items():
                    print(f"- {student}: {rating}")
                print("\n")
                
        elif choice == '5':
            print("\n--- Синхронізація баз даних ---")
            import sync_sheets
            result = sync_sheets.sync_data()
            print(f"\n{result}\n")

        elif choice == '0':
            print("Вихід з програми. До побачення!")
            break
        else:
            print("Невідома команда. Спробуйте ще раз.\n")

if __name__ == "__main__":
    menu()