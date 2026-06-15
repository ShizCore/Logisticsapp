"""
Файл client/main.py — оконное приложение (GUI) для системы грузоперевозок.
Использует Tkinter для создания графического интерфейса.
Подключается к TCP-серверу через ОДНО постоянное соединение.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import socket

# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКИ КЛИЕНТА
# ═══════════════════════════════════════════════════════════════
SERVER_HOST = 'localhost'
SERVER_PORT = 9999


class ShipmentClientApp:
    """Главный класс клиентского приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title("📦 Система грузоперевозок")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # 🔑 ПОСТОЯННОЕ TCP-соединение (вместо создания нового каждый раз)
        self.socket = None

        # Состояние приложения
        self.authenticated = False
        self.username = None
        self.user_id = None

        # Подключаемся к серверу при старте
        self.connect_to_server()

        # Создаём интерфейс авторизации
        self.create_login_ui()

        # Обработчик закрытия окна — закрываем сокет
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ═══════════════════════════════════════════════════════════
    # СЕТЕВОЕ ВЗАИМОДЕЙСТВИЕ (ПОСТОЯННОЕ СОЕДИНЕНИЕ)
    # ═══════════════════════════════════════════════════════════

    def connect_to_server(self):
        """Создаёт постоянное соединение с сервером"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"✅ Подключено к серверу {SERVER_HOST}:{SERVER_PORT}")
        except Exception as e:
            print(f"❌ Не удалось подключиться к серверу: {e}")
            self.socket = None

    def send_request(self, request: dict) -> dict:
        """
        Отправляет JSON-запрос на сервер через ПОСТОЯННОЕ соединение.
        """
        # Если соединения нет — пытаемся переподключиться
        if not self.socket:
            self.connect_to_server()
            if not self.socket:
                return {'success': False, 'message': 'Нет соединения с сервером'}

        try:
            # Отправляем запрос через существующее соединение
            self.socket.send(json.dumps(request).encode('utf-8'))

            # Получаем ответ
            response_data = self.socket.recv(8192).decode('utf-8')

            if not response_data:
                # Сервер закрыл соединение
                self.socket = None
                return {'success': False, 'message': 'Сервер разорвал соединение'}

            return json.loads(response_data)

        except socket.timeout:
            messagebox.showerror("Ошибка", "Сервер не отвечает (таймаут)")
            return {'success': False, 'message': 'Таймаут'}
        except ConnectionResetError:
            # Соединение разорвано — пытаемся переподключиться
            self.socket = None
            messagebox.showerror("Ошибка", "Соединение с сервером разорвано")
            return {'success': False, 'message': 'Соединение разорвано'}
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {e}")
            self.socket = None
            return {'success': False, 'message': str(e)}

    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.root.destroy()

    # ═══════════════════════════════════════════════════════════
    # ИНТЕРФЕЙС АВТОРИЗАЦИИ (без изменений)
    # ═══════════════════════════════════════════════════════════

    def create_login_ui(self):
        """Создаёт окно авторизации"""
        for widget in self.root.winfo_children():
            widget.destroy()

        login_frame = ttk.Frame(self.root, padding="30")
        login_frame.place(relx=0.5, rely=0.5, anchor='center')

        title_label = ttk.Label(login_frame, text="🔐 Вход в систему", font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

        ttk.Label(login_frame, text="Логин:", font=('Arial', 12)).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30, font=('Arial', 12))
        self.username_entry.grid(row=1, column=1, pady=5)
        self.username_entry.insert(0, "admin")

        ttk.Label(login_frame, text="Пароль:", font=('Arial', 12)).grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.password_entry = ttk.Entry(login_frame, show='*', width=30, font=('Arial', 12))
        self.password_entry.grid(row=2, column=1, pady=5)
        self.password_entry.insert(0, "admin123")

        login_btn = ttk.Button(login_frame, text="Войти", command=self.login, width=20)
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)

        register_btn = ttk.Button(login_frame, text="Регистрация", command=self.show_register_dialog, width=20)
        register_btn.grid(row=4, column=0, columnspan=2)

        self.root.bind('<Return>', lambda e: self.login())

    def login(self):
        """Обработка входа в систему"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Предупреждение", "Заполните все поля")
            return

        response = self.send_request({
            'action': 'login',
            'username': username,
            'password': password
        })

        if response.get('success'):
            self.authenticated = True
            self.username = username
            self.user_id = response.get('user_id')
            messagebox.showinfo("Успех", f"Добро пожаловать, {username}!\nРоль: {response.get('role')}")
            self.create_main_ui()
        else:
            messagebox.showerror("Ошибка входа", response.get('message', 'Неверный логин или пароль'))

    def show_register_dialog(self):
        """Показывает диалог регистрации"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Регистрация нового пользователя")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Регистрация", font=('Arial', 14, 'bold')).pack(pady=10)

        ttk.Label(dialog, text="Логин:").pack(pady=5)
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.pack()

        ttk.Label(dialog, text="Пароль:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show='*', width=30)
        password_entry.pack()

        def register():
            response = self.send_request({
                'action': 'register',
                'username': username_entry.get(),
                'password': password_entry.get()
            })

            if response.get('success'):
                messagebox.showinfo("Успех", "Регистрация успешна! Теперь войдите.")
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", response.get('message'))

        ttk.Button(dialog, text="Зарегистрироваться", command=register).pack(pady=20)

    # ═══════════════════════════════════════════════════════════
    # ГЛАВНЫЙ ИНТЕРФЕЙС (без изменений)
    # ═══════════════════════════════════════════════════════════

    def create_main_ui(self):
        """Создаёт главный интерфейс приложения"""
        for widget in self.root.winfo_children():
            widget.destroy()

        # Верхняя панель
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill='x')

        ttk.Label(top_frame, text=f"👤 {self.username}", font=('Arial', 12, 'bold')).pack(side='left')

        logout_btn = ttk.Button(top_frame, text="Выйти", command=self.logout)
        logout_btn.pack(side='right')

        list_clients_btn = ttk.Button(top_frame, text="📊 Подключённые клиенты", command=self.show_connected_clients)
        list_clients_btn.pack(side='right', padx=5)

        # Панель фильтров
        filter_frame = ttk.LabelFrame(self.root, text="🔍 Фильтры", padding="10")
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text="Статус:").grid(row=0, column=0, padx=5)
        self.status_filter = ttk.Combobox(
            filter_frame,
            values=['', 'registered', 'in_transit', 'delivered', 'cancelled'],
            width=15
        )
        self.status_filter.grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Мин. вес (кг):").grid(row=0, column=2, padx=5)
        self.weight_filter = ttk.Entry(filter_frame, width=10)
        self.weight_filter.grid(row=0, column=3, padx=5)

        ttk.Label(filter_frame, text="Тип груза:").grid(row=0, column=4, padx=5)
        self.cargo_filter = ttk.Combobox(
            filter_frame,
            values=['', 'Хрупкий', 'Опасный', 'Жидкость', 'Скоропортящийся', 'Мнущийся', 'Температурный режим'],
            width=20
        )
        self.cargo_filter.grid(row=0, column=5, padx=5)

        ttk.Button(filter_frame, text="🔍 Применить", command=self.apply_filter).grid(row=0, column=6, padx=10)
        ttk.Button(filter_frame, text="🔄 Сбросить", command=self.reset_filters).grid(row=0, column=7, padx=5)

        # Таблица отправлений
        table_frame = ttk.Frame(self.root, padding="10")
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('ID', 'Тип груза', 'Вес (кг)', 'Статус', 'Описание')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        self.tree.heading('ID', text='ID')
        self.tree.heading('Тип груза', text='Тип груза')
        self.tree.heading('Вес (кг)', text='Вес (кг)')
        self.tree.heading('Статус', text='Статус')
        self.tree.heading('Описание', text='Описание')

        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Тип груза', width=150)
        self.tree.column('Вес (кг)', width=80, anchor='center')
        self.tree.column('Статус', width=100, anchor='center')
        self.tree.column('Описание', width=300)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Панель кнопок
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(btn_frame, text="➕ Добавить груз", command=self.add_shipment_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✏️  Изменить статус", command=self.update_status_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑  Удалить", command=self.delete_shipment).pack(side='left', padx=5)

        # Загружаем данные
        self.apply_filter()

    # ═══════════════════════════════════════════════════════════
    # CRUD ОПЕРАЦИИ (без изменений)
    # ═══════════════════════════════════════════════════════════

    def apply_filter(self):
        """Применяет фильтры и загружает данные в таблицу"""
        status = self.status_filter.get() or None
        weight_str = self.weight_filter.get()
        min_weight = float(weight_str) if weight_str else None
        cargo = self.cargo_filter.get() or None

        response = self.send_request({
            'action': 'get_shipments',
            'status': status,
            'min_weight': min_weight,
            'cargo_type': cargo
        })

        for item in self.tree.get_children():
            self.tree.delete(item)

        if response.get('success'):
            for item in response['data']:
                self.tree.insert('', 'end', values=(
                    item['shipment_id'],
                    item['cargo_type'],
                    item['weight_kg'],
                    item['status'],
                    item['description']
                ))
        else:
            messagebox.showerror("Ошибка", response.get('message'))

    def reset_filters(self):
        """Сбрасывает все фильтры"""
        self.status_filter.set('')
        self.weight_filter.delete(0, 'end')
        self.cargo_filter.set('')
        self.apply_filter()

    def add_shipment_dialog(self):
        """Диалог добавления нового отправления"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить отправление")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Новое отправление", font=('Arial', 14, 'bold')).pack(pady=10)

        ttk.Label(dialog, text="Тип груза:").pack(pady=5)
        cargo_entry = ttk.Combobox(
            dialog,
            values=['Хрупкий', 'Опасный', 'Жидкость', 'Скоропортящийся', 'Мнущийся', 'Температурный режим'],
            width=30
        )
        cargo_entry.pack()
        cargo_entry.set('Хрупкий')

        ttk.Label(dialog, text="Вес (кг):").pack(pady=5)
        weight_entry = ttk.Entry(dialog, width=30)
        weight_entry.pack()
        weight_entry.insert(0, "10.0")

        ttk.Label(dialog, text="Описание:").pack(pady=5)
        desc_entry = ttk.Entry(dialog, width=30)
        desc_entry.pack()

        def submit():
            try:
                weight = float(weight_entry.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Вес должен быть числом")
                return

            cargo_map = {
                'Хрупкий': 1, 'Опасный': 2, 'Жидкость': 3,
                'Скоропортящийся': 4, 'нущийся': 5, 'Температурный режим': 6
            }

            response = self.send_request({
                'action': 'add_shipment',
                'cargo_type_id': cargo_map.get(cargo_entry.get(), 1),
                'weight_kg': weight,
                'description': desc_entry.get()
            })

            if response.get('success'):
                messagebox.showinfo("Успех", f"Отправление создано (ID: {response['shipment_id']})")
                dialog.destroy()
                self.apply_filter()
            else:
                messagebox.showerror("Ошибка", response.get('message'))

        ttk.Button(dialog, text="Создать", command=submit).pack(pady=20)

    def update_status_dialog(self):
        """Диалог изменения статуса отправления"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите отправление в таблице")
            return

        item = self.tree.item(selected[0])
        shipment_id = item['values'][0]
        current_status = item['values'][3]

        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить статус")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Отправление #{shipment_id}", font=('Arial', 12, 'bold')).pack(pady=10)
        ttk.Label(dialog, text=f"Текущий статус: {current_status}").pack(pady=5)

        ttk.Label(dialog, text="Новый статус:").pack(pady=5)
        status_combo = ttk.Combobox(
            dialog,
            values=['registered', 'in_transit', 'delivered', 'cancelled'],
            width=20
        )
        status_combo.pack()
        status_combo.set(current_status)

        def submit():
            response = self.send_request({
                'action': 'update_shipment',
                'shipment_id': shipment_id,
                'status': status_combo.get()
            })

            if response.get('success'):
                messagebox.showinfo("Успех", "Статус обновлён")
                dialog.destroy()
                self.apply_filter()
            else:
                messagebox.showerror("Ошибка", response.get('message'))

        ttk.Button(dialog, text="Обновить", command=submit).pack(pady=20)

    def delete_shipment(self):
        """Удаление выбранного отправления"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите отправление для удаления")
            return

        item = self.tree.item(selected[0])
        shipment_id = item['values'][0]

        if not messagebox.askyesno("Подтверждение", f"Удалить отправление #{shipment_id}?"):
            return

        response = self.send_request({
            'action': 'delete_shipment',
            'shipment_id': shipment_id
        })

        if response.get('success'):
            messagebox.showinfo("Успех", "Отправление удалено")
            self.apply_filter()
        else:
            messagebox.showerror("Ошибка", response.get('message'))

    # ═══════════════════════════════════════════════════════════
    # ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ (без изменений)
    # ═══════════════════════════════════════════════════════════

    def show_connected_clients(self):
        """Показывает список подключённых клиентов"""
        response = self.send_request({'action': 'list_clients'})

        if response.get('success'):
            clients = response['clients']

            dialog = tk.Toplevel(self.root)
            dialog.title("Подключённые клиенты")
            dialog.geometry("500x400")
            dialog.transient(self.root)

            ttk.Label(dialog, text=f"Всего подключений: {len(clients)}", font=('Arial', 14, 'bold')).pack(pady=10)

            text = tk.Text(dialog, height=20, width=60)
            text.pack(padx=10, pady=10)

            for client in clients:
                status = "✅ Авторизован" if client['authenticated'] else "❌ Не авторизован"
                username = client['username'] or "—"
                text.insert('end', f"{client['address']}\n  {status} ({username})\n\n")

            text.config(state='disabled')
        else:
            messagebox.showerror("Ошибка", response.get('message'))

    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Подтверждение", "Выйти из системы?"):
            self.authenticated = False
            self.username = None
            self.user_id = None
            self.create_login_ui()


# ═══════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    root = tk.Tk()
    app = ShipmentClientApp(root)
    root.mainloop()