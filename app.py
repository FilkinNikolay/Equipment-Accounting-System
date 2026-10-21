# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import database as db
import qrcode
from io import BytesIO
import base64
import sqlite3
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-12345'

# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ПРИ ЗАПУСКЕ
print("Проверка и создание базы данных...")
db.init_db()

# АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ ДАТ (чтобы график "Динамика" не был пустым)
with sqlite3.connect('equipment.db') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM equipment")
    eq_ids = [row[0] for row in cursor.fetchall()]
    for eq_id in eq_ids:
        days_ago = random.randint(0, 180)
        random_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE equipment SET created_at = ? WHERE id = ?", (random_date, eq_id))
    conn.commit()
print("База данных готова к работе!")

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# ========== ГЛАВНАЯ ==========
@app.route('/')
def index():
    stats = db.get_statistics()
    return render_template('index.html', stats=stats)

# ========== ДАШБОРД ==========
@app.route('/dashboard')
def dashboard():
    dashboard_stats = db.get_statistics_for_dashboard()
    stats = db.get_statistics()
    return render_template('dashboard.html', dashboard_stats=dashboard_stats, stats=stats)

# ========== РАСШИРЕННАЯ АНАЛИТИКА ==========
@app.route('/analytics/extended')
def extended_analytics():
    stats = db.get_statistics()
    ratings = {
        'most_problematic': db.get_most_problematic_equipment(10),
        'oldest': db.get_oldest_equipment(10),
        'requires_maintenance': db.get_requires_maintenance(10),
        'expiring_warranty': db.get_expiring_warranty_equipment(10),
        'most_moved': db.get_most_moved_equipment(10),
        'most_expensive': db.get_most_expensive_equipment(10),
    }
    return render_template('extended_analytics.html', stats=stats, ratings=ratings)

# ========== СПИСОК ОБОРУДОВАНИЯ ==========
@app.route('/equipment')
def equipment_list():
    equipment = db.get_all_equipment()
    return render_template('equipment_list.html', equipment=equipment)

# ========== QR-КОД ==========
@app.route('/equipment/<int:equipment_id>/qrcode')
def show_qrcode(equipment_id):
    equipment = db.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('❌ Оборудование не найдено', 'error')
        return redirect(url_for('equipment_list'))
    qr_data = f"http://127.0.0.1:5000/equipment/{equipment_id}"
    qr_image = generate_qr_code(qr_data)
    return render_template('qrcode.html', equipment=equipment, qr_image=qr_image)

# ========== ДОБАВЛЕНИЕ ОБОРУДОВАНИЯ (ИСПРАВЛЕНО) ==========
@app.route('/equipment/add', methods=['GET', 'POST'])
def add_equipment():
    if request.method == 'POST':
        inventory_number = request.form['inventory_number']
        name = request.form['name']
        serial_number = request.form.get('serial_number', '')
        location = request.form.get('location', '')
        status = request.form.get('status', 'in_stock')
        type_id = request.form.get('type_id')
        type_id = int(type_id) if type_id else None

        try:
            equipment_id = db.add_equipment(
                inventory_number=inventory_number,
                name=name,
                serial_number=serial_number,
                status=status,
                location=location,
                type_id=type_id
            )
            qr_data = f"http://127.0.0.1:5000/equipment/{equipment_id}"
            qr_image = generate_qr_code(qr_data)
            db.update_qr_code(equipment_id, qr_image)
            flash('✅ Оборудование добавлено!', 'success')
            return redirect(url_for('equipment_list'))
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'error')
            
    # Используем функцию из database.py
    types = db.get_all_types()
    return render_template('add_equipment.html', types=types)

# ========== ПРОСМОТР ==========
@app.route('/equipment/<int:equipment_id>')
def view_equipment(equipment_id):
    equipment = db.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('❌ Оборудование не найдено', 'error')
        return redirect(url_for('equipment_list'))
    history = db.get_equipment_history(equipment_id)
    return render_template('view_equipment.html', equipment=equipment, history=history)

# ========== РЕДАКТИРОВАНИЕ ==========
@app.route('/equipment/edit/<int:equipment_id>', methods=['GET', 'POST'])
def edit_equipment(equipment_id):
    equipment = db.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('❌ Оборудование не найдено', 'error')
        return redirect(url_for('equipment_list'))
    if request.method == 'POST':
        inventory_number = request.form['inventory_number']
        name = request.form['name']
        serial_number = request.form.get('serial_number', '')
        location = request.form.get('location', '')
        status = request.form.get('status', 'in_stock')
        db.update_equipment(equipment_id, inventory_number, name, serial_number, status, location)
        flash('✅ Оборудование обновлено!', 'success')
        return redirect(url_for('view_equipment', equipment_id=equipment_id))
    return render_template('edit_equipment.html', equipment=equipment)

# ========== УДАЛЕНИЕ ==========
@app.route('/equipment/delete/<int:equipment_id>', methods=['POST'])
def delete_equipment(equipment_id):
    db.delete_equipment(equipment_id)
    flash('✅ Оборудование удалено', 'success')
    return redirect(url_for('equipment_list'))

# ========== ПОИСК ==========
@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = db.search_equipment(query) if query else []
    return render_template('search_results.html', results=results, query=query)

# ========== СТАТИСТИКА ==========
@app.route('/statistics')
def statistics():
    stats = db.get_statistics()
    return render_template('statistics.html', stats=stats)

# ========== ЭКСПОРТ В EXCEL ==========
@app.route('/export/excel')
def export_excel():
    try:
        excel_file = db.export_to_excel()
        return send_file(excel_file, as_attachment=True, download_name='equipment_export.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'❌ Ошибка при экспорте: {str(e)}', 'error')
        return redirect(url_for('equipment_list'))

# ========== ОТЧЁТЫ ==========
@app.route('/reports/repairs')
def report_repairs():
    repairs = db.get_all_repairs_with_equipment()
    problem_equipment = db.get_problem_equipment()
    return render_template('reports_repairs.html', repairs=repairs, problem_equipment=problem_equipment)

@app.route('/reports/licenses')
def report_licenses():
    all_licenses = db.get_all_licenses_with_equipment()
    expiring_licenses = db.get_expiring_licenses(30)
    return render_template('reports_licenses.html', all_licenses=all_licenses, expiring_licenses=expiring_licenses)

@app.route('/reports/maintenance')
def report_maintenance():
    upcoming_maintenance = db.get_upcoming_maintenance(30)
    return render_template('reports_maintenance.html', upcoming_maintenance=upcoming_maintenance)

# ========== РЕМОНТЫ И ЛИЦЕНЗИИ ==========
@app.route('/equipment/<int:equipment_id>/add_repair', methods=['GET', 'POST'])
def add_repair(equipment_id):
    equipment = db.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('❌ Оборудование не найдено', 'error')
        return redirect(url_for('equipment_list'))
    if request.method == 'POST':
        repair_date = request.form['repair_date']
        description = request.form['description']
        cost = request.form.get('cost', '').strip()
        cost = float(cost) if cost else None
        db.add_repair(equipment_id, repair_date, description, cost)
        flash('✅ Запись о ремонте добавлена', 'success')
        return redirect(url_for('view_equipment', equipment_id=equipment_id))
    return render_template('add_repair.html', equipment=equipment)

@app.route('/equipment/<int:equipment_id>/add_license', methods=['GET', 'POST'])
def add_license(equipment_id):
    equipment = db.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('❌ Оборудование не найдено', 'error')
        return redirect(url_for('equipment_list'))
    if request.method == 'POST':
        software_name = request.form['software_name']
        license_key = request.form.get('license_key', '')
        expiration_date = request.form['expiration_date']
        db.add_license(equipment_id, software_name, license_key, expiration_date)
        flash('✅ Лицензия добавлена', 'success')
        return redirect(url_for('view_equipment', equipment_id=equipment_id))
    return render_template('add_license.html', equipment=equipment)

# ========== РАСХОДНИКИ ==========
@app.route('/consumables')
def consumables_list():
    consumables = db.get_all_consumables()
    low_stock = db.get_low_stock_consumables()
    return render_template('consumables_list.html', consumables=consumables, low_stock=low_stock)

@app.route('/consumables/add', methods=['GET', 'POST'])
def add_consumable():
    if request.method == 'POST':
        name = request.form['name']
        compatible_models = request.form['compatible_models']
        quantity = int(request.form['quantity'])
        min_quantity = int(request.form.get('min_quantity', 5))
        unit = request.form.get('unit', 'шт')
        price = request.form.get('price', '').strip()
        price = float(price) if price else None
        db.add_consumable(name, compatible_models, quantity, min_quantity, unit, price)
        flash('✅ Расходный материал добавлен', 'success')
        return redirect(url_for('consumables_list'))
    return render_template('add_consumable.html')

@app.route('/consumables/use/<int:consumable_id>', methods=['POST'])
def use_consumable(consumable_id):
    try:
        quantity = int(request.form['quantity'])
        reason = request.form.get('reason', '')
        db.use_consumable(consumable_id, None, quantity, reason)
        flash('✅ Расходный материал списан', 'success')
    except ValueError as e:
        flash(f'❌ {str(e)}', 'error')
    return redirect(url_for('consumables_list'))

# ========== СОВМЕСТИМОСТЬ ==========
@app.route('/equipment/<int:equipment_id>/compatible')
def compatible_parts(equipment_id):
    equipment = db.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('❌ Оборудование не найдено', 'error')
        return redirect(url_for('equipment_list'))
    compatible_parts = db.get_compatible_parts(equipment[9])
    return render_template('compatible_parts.html', equipment=equipment, compatible_parts=compatible_parts)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК ВЕБ-СЕРВЕРА")
    print("=" * 60)
    print("📱 Откройте в браузере: http://127.0.0.1:5000")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("=" * 60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)