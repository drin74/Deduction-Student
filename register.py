import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# Подключение к БД
conn = sqlite3.connect('deduction.db')
cursor = conn.cursor()



# Функция регистрации
def register():
    username = entry_reg_username.get()
    password = entry_reg_password.get()
    password2 = entry_reg_password2.get()

    # Проверка на пустые поля
    if not username or not password or not password2 and password != password2:
        messagebox.showerror("Ошибка", "Заполните все поля правильно")
        return

    try:
        # Добавляем пользователя
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, password))
        conn.commit()
        messagebox.showinfo("Успех", "Регистрация прошла успешно!")

        # Очищаем поля
        entry_reg_username.delete(0, tk.END)
        entry_reg_password.delete(0, tk.END)
        entry_reg_password2.delete(0, tk.END)

    except sqlite3.IntegrityError:
        messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует")


# Функция входа
def login():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showerror("Ошибка", "Введите имя пользователя и пароль")
        return

    # Ищем пользователя в БД
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                   (username, password))
    user = cursor.fetchone()

    if user:
        # Здесь можно открыть главное окно программы
        window.destroy()  # закрывает окно авторизации
        import main
    else:
        messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")


# Создание окна
window = tk.Tk()
window.title("Авторизация и Регистрация")
window.geometry('300x350')
window.configure(background='#C8C8C8')

# Создание вкладок
tab_control = ttk.Notebook(window)

# ===== Вкладка входа =====
tab_login = ttk.Frame(tab_control)
tab_control.add(tab_login, text='Вход')

tk.Label(tab_login, text="Имя пользователя").pack(pady=5)
entry_username = tk.Entry(tab_login)
entry_username.pack(pady=5)

tk.Label(tab_login, text="Пароль").pack(pady=5)
entry_password = tk.Entry(tab_login, show='*')
entry_password.pack(pady=5)

tk.Button(tab_login, text="Войти", command=login, bg='#4CAF50', fg='white').pack(pady=(10, 5))

# ===== Вкладка регистрации =====
tab_register = ttk.Frame(tab_control)
tab_control.add(tab_register, text='Регистрация')

tk.Label(tab_register, text="Имя пользователя").pack(pady=5)
entry_reg_username = tk.Entry(tab_register)
entry_reg_username.pack(pady=5)

tk.Label(tab_register, text="Пароль").pack(pady=5)
entry_reg_password = tk.Entry(tab_register, show='*')
entry_reg_password.pack(pady=5)

tk.Label(tab_register, text="Повтарите Пароль").pack(pady=5)
entry_reg_password2 = tk.Entry(tab_register, show='*')
entry_reg_password2.pack(pady=5)


tk.Button(tab_register, text="Зарегистрироваться", command=register, bg='#2196F3', fg='white').pack(pady=(10, 5))

tab_control.pack(expand=1, fill='both', padx=10, pady=10)


window.mainloop()

# Закрываем соединение при выходе
conn.close()