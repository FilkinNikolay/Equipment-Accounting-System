# main.py
import database as db

def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

def get_status_text(status):
    statuses = {
        'in_stock': 'На складе',
        'in_use': 'В эксплуатации',
        'repair': 'В ремонте',
        'written_off': 'Списано'
    }
    return statuses.get(status, status)

def show_equipment_list():
    clear_screen()
    print_header("СПИСОК ОБОРУДОВАНИЯ")
    equipment = db.get_all_equipment()
    if not equipment:
        print("Нет данных. Добавьте оборудование.")
    else:
        print(f"{'ID':<4} {'Инв. номер':<12} {'Наименование':<25} {'Тип':<18} {'Статус':<14} {'МОЛ':<20}")
        print("-" * 95)
        for eq in equipment:
            eq_type = eq[9] if eq[9] else '—'
            responsible = eq[10] if eq[10] else '—'
            status_text = get_status_text(eq[4])
            print(f"{eq[0]:<4} {eq[1]:<12} {eq[3][:23]:<25} {eq_type[:16]:<18} {status_text:<14} {responsible[:18]:<20}")
        print(f"\nВсего: {len(equipment)} единиц")
    input("\nНажмите Enter для продолжения...")

def add_equipment_menu():
    clear_screen()
    print_header("ДОБАВЛЕНИЕ ОБОРУДОВАНИЯ")
    inv_num = input("Инвентарный номер: ").strip()
    if not inv_num:
        print("Инвентарный номер обязателен!")
        input("Нажмите Enter...")
        return
    name = input("Наименование: ").strip()
    if not name:
        print("Наименование обязательно!")
        input("Нажмите Enter...")
        return
    
    types = db.get_all_types()
    print("\nДоступные типы оборудования:")
    for t in types:
        print(f"  {t[0]}. {t[1]}")
    type_choice = input("Выберите ID типа (Enter - пропустить): ").strip()
    type_id = int(type_choice) if type_choice.isdigit() else None

    serial = input("Серийный номер (Enter - пропустить): ").strip()
    location = input("Местоположение (Enter - пропустить): ").strip()
    
    print("\nСтатусы:")
    print("  1. На складе")
    print("  2. В эксплуатации")
    print("  3. В ремонте")
    status_choice = input("Выберите статус (1-3, по умолчанию 1): ").strip()
    status_map = {'1': 'in_stock', '2': 'in_use', '3': 'repair'}
    status = status_map.get(status_choice, 'in_stock')
    
    try:
        db.add_equipment(
            inventory_number=inv_num,
            name=name,
            serial_number=serial,
            type_id=type_id,
            status=status,
            location=location
        )
        print(f"\nОборудование '{name}' успешно добавлено!")
    except Exception as e:
        print(f"\nОшибка: {e}")
    input("\nНажмите Enter для продолжения...")

def view_equipment_menu():
    clear_screen()
    print_header("ПРОСМОТР ОБОРУДОВАНИЯ")
    equipment = db.get_all_equipment()
    if not equipment:
        print("Нет данных.")
        input("Нажмите Enter...")
        return
    print("Список оборудования:")
    for eq in equipment:
        print(f"  {eq[0]}. {eq[1]} - {eq[3]}")
    try:
        eq_id = int(input("\nВведите ID оборудования для просмотра: ").strip())
        eq = db.get_equipment_by_id(eq_id)
        if eq:
            print(f"\n--- Детальная информация ---")
            print(f"Инвентарный номер: {eq[1]}")
            print(f"Наименование: {eq[3]}")
            print(f"Тип: {eq[11] or '—'}")
            print(f"Серийный номер: {eq[2] or '—'}")
            print(f"Статус: {get_status_text(eq[4])}")
            print(f"Местоположение: {eq[5] or '—'}")
            print(f"МОЛ: {eq[12] or '—'}")
            print(f"Дата покупки: {eq[6] or '—'}")
            print(f"Гарантия до: {eq[8] or '—'}")
            print(f"Стоимость: {eq[7] if eq[7] else '—'}")
            history = db.get_equipment_history(eq_id)
            if history:
                print(f"\n--- История перемещений ---")
                for h in history:
                    print(f"  {h[6]} | от: {h[7] or 'Склад'} -> к: {h[8] or 'Склад'} | {h[10] or '—'}")
        else:
            print("Оборудование не найдено")
    except ValueError:
        print("Неверный ID")
    input("\nНажмите Enter для продолжения...")

def delete_equipment_menu():
    clear_screen()
    print_header("УДАЛЕНИЕ ОБОРУДОВАНИЯ")
    equipment = db.get_all_equipment()
    if not equipment:
        print("Нет данных для удаления.")
        input("Нажмите Enter...")
        return
    print("Список оборудования:")
    for eq in equipment:
        print(f"  {eq[0]}. {eq[1]} - {eq[3]}")
    try:
        eq_id = int(input("\nВведите ID оборудования для удаления: ").strip())
        eq = db.get_equipment_by_id(eq_id)
        if eq:
            confirm = input(f"Удалить '{eq[3]}'? (да/нет): ").strip().lower()
            if confirm == 'да':
                db.delete_equipment(eq_id)
                print("Оборудование удалено")
            else:
                print("Удаление отменено")
        else:
            print("Оборудование не найдено")
    except ValueError:
        print("Неверный ID")
    input("Нажмите Enter для продолжения...")

def search_equipment_menu():
    clear_screen()
    print_header("ПОИСК ОБОРУДОВАНИЯ")
    search_term = input("Введите поисковый запрос (инв. номер или наименование): ").strip()
    if not search_term:
        print("Введите запрос для поиска")
    else:
        results = db.search_equipment(search_term)
        if results:
            print(f"\nНайдено {len(results)} результатов:\n")
            for eq in results:
                print(f"  [{eq[0]}] {eq[1]} - {eq[2]} ({get_status_text(eq[3])}) - {eq[4]}")
        else:
            print(f"\nНичего не найдено по запросу '{search_term}'")
    input("\nНажмите Enter для продолжения...")

def statistics_menu():
    clear_screen()
    print_header("СТАТИСТИКА")
    stats = db.get_statistics()
    print(f"Всего единиц оборудования: {stats['total']}\n")
    print(f"  В эксплуатации: {stats['in_use']}")
    print(f"  На складе: {stats['in_stock']}")
    print(f"  В ремонте: {stats['repair']}")
    input("\nНажмите Enter для продолжения...")

def show_info():
    clear_screen()
    print_header("О СИСТЕМЕ")
    print("""
    Система учета технических средств
    Версия: 1.0
    База данных: SQLite
    Разработчик: Филькин Н.А.
    Группа: ИС-О-22/1
    
    Функции:
    - Учет оборудования (ПК, ноутбуки, принтеры и т.д.)
    - Отслеживание статуса (склад/эксплуатация/ремонт)
    - Поиск по инвентарному номеру
    - Статистика по оборудованию
    - История перемещений
    """)
    input("Нажмите Enter для продолжения...")

def main():
    print("Загрузка системы...")
    db.init_db()
    while True:
        clear_screen()
        print_header("СИСТЕМА УЧЕТА ТЕХНИЧЕСКИХ СРЕДСТВ")
        print("\nМЕНЮ:")
        print("  1. Список оборудования")
        print("  2. Добавить оборудование")
        print("  3. Просмотр оборудования (детально)")
        print("  4. Удалить оборудование")
        print("  5. Поиск оборудования")
        print("  6. Статистика")
        print("  7. О системе")
        print("  0. Выход")
        print("-" * 40)
        choice = input("Выберите действие: ").strip()
        if choice == '1': show_equipment_list()
        elif choice == '2': add_equipment_menu()
        elif choice == '3': view_equipment_menu()
        elif choice == '4': delete_equipment_menu()
        elif choice == '5': search_equipment_menu()
        elif choice == '6': statistics_menu()
        elif choice == '7': show_info()
        elif choice == '0':
            print("\nДо свидания!")
            break
        else:
            print("Неверный выбор")
            input("Нажмите Enter...")

if __name__ == "__main__":
    main()