from tkinter import *
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import json
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
CONFIG_FILE = "courses_config.json"

# Глобальные переменные
conn = None
cursor = None
menubar = None
courses_menu = None
tree = None
lbl_current_course = None

# Конфигурация курсов
COURSES = {
    "ИСИП": {"file": "isip.db", "table": "deduction"},
    "Юристы": {"file": "lawyers.db", "table": "deduction"},
    "БД": {"file": "bd.db", "table": "deduction"}
}

window = Tk()
window.title("Deduction Student")
window.geometry('1920x1080')
window.configure(bg='#2d3e50')


# ================= ФУНКЦИИ КОНФИГУРАЦИИ =================

def load_courses_config():
    """Загружает сохраненные курсы из файла"""
    global COURSES
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_courses = json.load(f)
                for course_name, config in saved_courses.items():
                    if course_name not in COURSES:
                        COURSES[course_name] = config
            print(f"Загружено {len(saved_courses)} сохраненных курсов")
        except Exception as e:
            print(f"⚠Ошибка загрузки конфигурации: {e}")


def save_courses_config():
    """Сохраняет пользовательские курсы в файл"""
    standard_courses = {"ИСИП", "Юристы", "БД"}
    user_courses = {name: config for name, config in COURSES.items()
                    if name not in standard_courses}

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_courses, f, ensure_ascii=False, indent=4)
    print(f"сохранено {len(user_courses)} пользовательских курсов")


def rebuild_courses_menu():
    """Пересоздает меню курсов"""
    global courses_menu
    menubar.delete(1, 'end')

    new_courses_menu = Menu(menubar, tearoff=0)
    for course_name in COURSES.keys():
        course_submenu = Menu(new_courses_menu, tearoff=0)
        course_submenu.add_command(label="↻ Переключиться",
                                   command=lambda c=course_name: switch_database(c))

        db_file = COURSES[course_name]["file"]
        course_submenu.add_command(label=f"📄 {db_file}", state=DISABLED)
        course_submenu.add_separator()

        if course_name not in ["ИСИП", "Юристы", "БД"]:
            course_submenu.add_command(label="🗑 Удалить курс",
                                       command=lambda c=course_name: delete_course(c),
                                       foreground="red")

        new_courses_menu.add_cascade(label=course_name, menu=course_submenu)

    menubar.add_cascade(label='Курсы', menu=new_courses_menu)
    courses_menu = new_courses_menu


# ================= ЛОГИКА БД =================

def init_databases():
    """Создает таблицы, если их нет"""
    for course_name, config in COURSES.items():
        db_file = config["file"]
        temp_conn = sqlite3.connect(db_file)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS deduction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                birth TEXT,
                status TEXT
            )
        """)
        temp_conn.commit()
        temp_conn.close()


def switch_database(course_name):
    """Переключает базу данных"""
    global conn, cursor

    if course_name not in COURSES:
        return

    config = COURSES[course_name]
    db_file = config["file"]

    if conn:
        try:
            conn.close()
        except:
            pass

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    window.title(f"Deduction Student - {course_name}")
    lbl_current_course.config(text=f"Текущий курс: {course_name}", fg='#000000')
    load_data()


def load_data():
    if not conn or not cursor:
        return
    for item in tree.get_children():
        tree.delete(item)
    try:
        cursor.execute("SELECT id, name, mobile, birth, status FROM deduction")
        for row in cursor.fetchall():
            tree.insert("", "end", values=row)
    except Exception as e:
        messagebox.showerror("Ошибка БД", f"Не удалось загрузить данные: {e}")


# ================= ФУНКЦИИ ИНТЕРФЕЙСА =================

def create_new_database():
    """Создаёт новую базу"""
    dialog = Toplevel(window)
    dialog.title("Создание новой базы")
    dialog.geometry("350x170")
    dialog.configure(bg='#34495e')
    dialog.resizable(False, False)

    Label(dialog, text="Название базы (без .db):", bg='#34495e').pack(pady=10)
    name_entry = Entry(dialog, width=30)
    name_entry.pack()

    Label(dialog, text="Название курса (для меню):", bg='#34495e').pack(pady=5)
    course_entry = Entry(dialog, width=30)
    course_entry.pack()

    def create():
        db_name = name_entry.get().strip()
        course_name = course_entry.get().strip()

        if not db_name or not course_name:
            messagebox.showerror("Ошибка", "Заполните оба поля")
            return

        if not db_name.endswith('.db'):
            db_name = db_name + '.db'

        if db_name in [c["file"] for c in COURSES.values()]:
            messagebox.showerror("Ошибка", "База уже существует!")
            return

        conn_temp = sqlite3.connect(db_name)
        cursor_temp = conn_temp.cursor()
        cursor_temp.execute('''
        CREATE TABLE IF NOT EXISTS deduction ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            birth TEXT NOT NULL,
            status TEXT NOT NULL
        )
        ''')
        conn_temp.commit()
        conn_temp.close()

        COURSES[course_name] = {"file": db_name, "table": "deduction"}
        save_courses_config()
        rebuild_courses_menu()

        dialog.destroy()
        messagebox.showinfo("Готово", f"База '{db_name}' создана!")

    Button(dialog, text="Создать", command=create, bg='#4CAF50', fg='white').pack(pady=15)


def delete_course(course_name):
    """Удаляет курс"""
    if course_name in ["ИСИП", "Юристы", "БД"]:
        messagebox.showerror("Ошибка", "Нельзя удалить стандартный курс!")
        return

    confirm = messagebox.askyesno("Подтверждение", f"Удалить курс '{course_name}'?")
    if not confirm:
        return

    del COURSES[course_name]
    save_courses_config()
    rebuild_courses_menu()

    first_course = list(COURSES.keys())[0]
    switch_database(first_course)

    messagebox.showinfo("Готово", f"Курс '{course_name}' удален")


def delete():
    if not conn or not cursor:
        return
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Внимание", "Выберите студента")
        return

    student_id = tree.item(selected[0])['values'][0]
    confirm = messagebox.askyesno("Подтверждение", f"Удалить студента ID {student_id}?")
    if confirm:
        cursor.execute("DELETE FROM deduction WHERE id = ?", (student_id,))
        conn.commit()
        tree.delete(selected)


def open_add_dialog():
    if not conn or not cursor:
        messagebox.showerror("Ошибка", "База не выбрана")
        return

    dialog = Toplevel(window)
    dialog.title("Добавление студента")
    dialog.geometry("400x350")
    dialog.configure(bg='#34495e')
    dialog.resizable(False, False)

    Label(dialog, text="ФИО:", bg='#34495e').pack(pady=5)
    name_entry = Entry(dialog, width=40)
    name_entry.pack()

    Label(dialog, text="Телефон:", bg='#34495e').pack(pady=5)
    mobile_entry = Entry(dialog, width=40)
    mobile_entry.pack()

    Label(dialog, text="Дата рождения (ГГГГ-ММ-ДД):", bg='#34495e').pack(pady=5)
    birth_entry = Entry(dialog, width=40)
    birth_entry.pack()

    Label(dialog, text="Статус:", bg='#34495e').pack(pady=5)
    status_combo = ttk.Combobox(dialog, values=["очная", "заочная", "очно-заочная"], width=37)
    status_combo.pack()
    status_combo.set("очная")

    def save_student():
        name = name_entry.get().strip()
        mobile = mobile_entry.get().strip()
        birth = birth_entry.get().strip()
        status = status_combo.get()

        if not name or not mobile or not birth:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        if len(mobile) != 11:
            messagebox.showerror('Ошибка', 'Номер должен быть 11 цифр')
            return
        if not mobile.isdigit():
            messagebox.showerror("Ошибка", "Только цифры в телефоне")
            return

        try:
            cursor.execute("INSERT INTO deduction (name, mobile, birth, status) VALUES (?, ?, ?, ?)",
                           (name, mobile, birth, status))
            conn.commit()
            new_id = cursor.lastrowid
            tree.insert("", "end", values=(new_id, name, mobile, birth, status))
            dialog.destroy()
            messagebox.showinfo("Готово", "Студент добавлен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    Button(dialog, text="Сохранить", command=save_student, bg='#4CAF50', fg='white').pack(pady=20)
    Button(dialog, text="Отмена", command=dialog.destroy).pack()


def edit_student():
    if not conn or not cursor:
        return
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Внимание", "Выберите студента")
        return

    values = tree.item(selected[0])['values']
    student_id = values[0]

    dialog = Toplevel(window)
    dialog.title("Редактирование")
    dialog.geometry("400x350")
    dialog.configure(bg='#34495e')
    dialog.resizable(False, False)

    Label(dialog, text="ФИО:", bg='#34495e').pack(pady=5)
    name_entry = Entry(dialog, width=40)
    name_entry.insert(0, values[1])
    name_entry.pack()

    Label(dialog, text="Телефон:", bg='#34495e').pack(pady=5)
    mobile_entry = Entry(dialog, width=40)
    mobile_entry.insert(0, values[2])
    mobile_entry.pack()

    Label(dialog, text="Дата рождения:", bg='#34495e').pack(pady=5)
    birth_entry = Entry(dialog, width=40)
    birth_entry.insert(0, values[3])
    birth_entry.pack()

    Label(dialog, text="Статус:", bg='#34495e').pack(pady=5)
    status_combo = ttk.Combobox(dialog, values=["очная", "заочная", "очно-заочная"], width=37)
    status_combo.set(values[4])
    status_combo.pack()

    def save_changes():
        new_name = name_entry.get().strip()
        new_mobile = mobile_entry.get().strip()
        new_birth = birth_entry.get().strip()
        new_status = status_combo.get()

        if not new_name or not new_mobile:
            messagebox.showerror("Ошибка", "Заполните поля")
            return
        if len(new_mobile) != 11:
            messagebox.showerror('Ошибка', '11 цифр в номере')
            return
        if not new_mobile.isdigit():
            messagebox.showerror("Ошибка", "Только цифры")
            return

        cursor.execute("""UPDATE deduction SET name=?, mobile=?, birth=?, status=? WHERE id=?""",
                       (new_name, new_mobile, new_birth, new_status, student_id))
        conn.commit()
        tree.item(selected[0], values=(student_id, new_name, new_mobile, new_birth, new_status))
        dialog.destroy()
        messagebox.showinfo("Готово", "Обновлено")

    Button(dialog, text="Сохранить", command=save_changes, bg='#4CAF50', fg='white').pack(pady=20)
    Button(dialog, text="Отмена", command=dialog.destroy).pack()

def create_report():
    """Создание отчёта из ТЕКУЩЕЙ активной базы данных"""
    if not conn or not cursor:
        messagebox.showerror("Ошибка", "База данных не выбрана")
        return

    report_window = Toplevel(window)
    report_window.title("Создание отчёта")
    report_window.geometry("400x250")
    report_window.configure(background='#34495e')
    report_window.resizable(False, False)
    report_window.transient(window)
    report_window.grab_set()

    Label(report_window, text="Выберите формат отчёта:",
          bg='#34495e', font=("Arial", 12, "bold")).pack(pady=20)

    def export_excel():
        try:
            cursor.execute("SELECT id, name, mobile, birth, status FROM deduction")
            rows = cursor.fetchall()
            if not rows:
                messagebox.showwarning("Внимание", "В базе нет записей!")
                return

            df = pd.DataFrame(rows, columns=['ID', 'ФИО', 'Телефон', 'Дата рождения', 'Статус'])
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel файлы", "*.xlsx")],
                initialfile=f"отчёт_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            if file_path:
                df.to_excel(file_path, index=False, sheet_name='Студенты')
                messagebox.showinfo("Успех", f"Excel отчёт сохранён:\n{file_path}")
                report_window.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать Excel:\n{str(e)}")

    def export_pdf():
        try:
            cursor.execute("SELECT id, name, mobile, birth, status FROM deduction")
            rows = cursor.fetchall()
            if not rows:
                messagebox.showwarning("Внимание", "В базе нет записей!")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF файлы", "*.pdf")],
                initialfile=f"отчёт_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if file_path:
                doc = SimpleDocTemplate(file_path, pagesize=A4)
                elements = []
                styles = getSampleStyleSheet()

                title = Paragraph("Отчёт по студентам", styles['Heading1'])
                elements.append(title)
                elements.append(Spacer(1, 12))

                # Получаем текущий курс для отчёта
                current_course = lbl_current_course.cget("text")
                info_text = f"Курс: {current_course}<br/>"
                info_text += f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}<br/>"
                info_text += f"Всего студентов: {len(rows)}"
                info = Paragraph(info_text, styles['Normal'])
                elements.append(info)
                elements.append(Spacer(1, 20))

                data = [['ID', 'ФИО', 'Телефон', 'Дата рождения', 'Статус']]
                for row in rows:
                    data.append([str(row[0]), row[1], row[2], row[3], row[4]])

                table = Table(data, colWidths=[50, 150, 100, 100, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))

                elements.append(table)
                doc.build(elements)

                messagebox.showinfo("Успех", f"PDF отчёт сохранён:\n{file_path}")
                report_window.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать PDF:\n{str(e)}")

    Button(report_window, text="📈 Excel", command=export_excel,
           bg='#217346', fg='white', font=("Arial", 12, "bold"),
           width=20, height=2).pack(pady=10)

    Button(report_window, text="📄 PDF", command=export_pdf,
           bg='#b30b00', fg='white', font=("Arial", 12, "bold"),
           width=20, height=2).pack(pady=10)

    Button(report_window, text="Отмена", command=report_window.destroy,
            width=20).pack(pady=10)

def on_close():
    if conn:
        conn.close()
    window.destroy()


# ================= СОЗДАНИЕ ИНТЕРФЕЙСА (ОДИН РАЗ!) =================

# 1. Инициализация БД
init_databases()
load_courses_config()

# 2. Меню
menubar = Menu(window)
file_menu = Menu(menubar, tearoff=0)
file_menu.add_command(label="создать базу", command=create_new_database)
file_menu.add_command(label="Выйти", command=window.quit)
menubar.add_cascade(label='Файл', menu=file_menu)

courses_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='Курсы', menu=courses_menu)
window.config(menu=menubar)

# 3. Панель кнопок
header = Frame(window, height=80, bg='#34495e')
header.pack(fill=X)

lbl_current_course = Label(header, text="Текущий курс: Не выбран",
                           bg='#34495e', font=("Arial", 14, "bold"))
lbl_current_course.pack(side=RIGHT, padx=20, pady=25)

buttons = [
    ("📊 Отчёт", create_report,'#3598db',),
    ("➕Создать базу", create_new_database,'#ff00c0',),
    ("👤 Добавить cтудента", open_add_dialog,'#27ae61',),
    ("✏️Редактировать", edit_student,'#f39c11',),
    ("🗑️Удалить", delete,'#e84c3d',)
]

for text, cmd, bg in buttons:
    Button(header, text=text, command=cmd, font=("Arial", 10),bg=bg).pack(side=LEFT, padx=10, pady=15)

# 4. Таблица
columns = ("id", "ФИО", "Телефон", "Дата рождения", "Статус")
tree = ttk.Treeview(window, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=170)

tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

# 5. Финальная настройка
rebuild_courses_menu()
first_course = list(COURSES.keys())[0]
switch_database(first_course)

window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()