"""
Файл main.py — TCP-сервер для системы грузоперевозок.
Это консольное приложение, которое:
- Слушает TCP-порт 9999
- Принимает подключения от клиентов
- Обрабатывает JSON-запросы (авторизация, CRUD)
- Отслеживает подключённых клиентов
"""

import socket
import json
import threading
from server.factory import RepositoryFactory
from server.auth import AuthService
from server.models import Shipment

# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКИ СЕРВЕРА
# ═══════════════════════════════════════════════════════════════
HOST = 'localhost'  # Слушаем только локальные подключения
PORT = 9999  # Порт для подключений
USE_ORM = True  # True = ORM, False = SQL (можно переключать)


class ShipmentServer:
    """TCP-сервер для обработки запросов от клиентов"""

    def __init__(self, use_orm=True):
        self.use_orm = use_orm
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)  # Максимум 5 клиентов в очереди

        # 🔑 Отслеживание подключённых клиентов (требование №4)
        self.connected_clients = {}  # {address: {'socket': ..., 'authenticated': ..., 'user_id': ...}}

        # Создаём репозиторий через Factory
        self.repository = RepositoryFactory.create(use_orm)

        print(f"🚀 Сервер запущен на {HOST}:{PORT}")
        print(f"📦 Режим БД: {'ORM (SQLAlchemy)' if use_orm else 'Raw SQL (psycopg2)'}")
        print("⏳ Ожидание подключений...\n")

    def handle_client(self, client_socket, address):
        """
        Обработка подключённого клиента.
        Запускается в отдельном потоке для каждого клиента.
        """
        client_id = f"{address[0]}:{address[1]}"

        # Регистрируем клиента в словаре
        self.connected_clients[client_id] = {
            'socket': client_socket,
            'authenticated': False,
            'user_id': None,
            'username': None
        }

        print(f"✅ Подключён клиент: {client_id}")
        print(f"📊 Всего подключений: {len(self.connected_clients)}\n")

        try:
            # Бесконечный цикл обработки запросов от этого клиента
            while True:
                # Получаем данные от клиента
                data = client_socket.recv(4096)
                if not data:
                    break  # Клиент отключился

                # Пробуем JSON-запрос
                try:
                    request = json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    response = {'success': False, 'message': 'Неверный формат JSON'}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    continue

                # Обрабатываем запрос
                response = self.process_request(request, client_id)

                # Отправляем ответ клиенту
                client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"❌ Ошибка клиента {client_id}: {e}")
        finally:
            # Клиент отключился — удаляем из словаря
            del self.connected_clients[client_id]
            client_socket.close()
            print(f"👋 Клиент отключён: {client_id}")
            print(f"📊 Осталось подключений: {len(self.connected_clients)}\n")

    def process_request(self, request: dict, client_id: str) -> dict:
        """
        Обработка запроса от клиента.
        Возвращает словарь с результатом.
        """
        action = request.get('action')

        # ═══════════════════════════════════════════════════════
        # АВТОРИЗАЦИЯ (не требует предварительной авторизации)
        # ═══════════════════════════════════════════════════════
        if action == 'login':
            username = request.get('username')
            password = request.get('password')

            result = AuthService.login(username, password)

            if result['success']:
                # Запоминаем, что клиент авторизован
                self.connected_clients[client_id]['authenticated'] = True
                self.connected_clients[client_id]['user_id'] = result['user_id']
                self.connected_clients[client_id]['username'] = username
                print(f"🔑 Клиент {client_id} авторизован как {username} (роль: {result['role']})")

            return result

        if action == 'register':
            username = request.get('username')
            password = request.get('password')
            role = request.get('role', 'user')

            return AuthService.register(username, password, role)

        # ═══════════════════════════════════════════════════════
        # ПРОВЕРКА АВТОРИЗАЦИИ для всех остальных действий
        # ═══════════════════════════════════════════════════════
        if not self.connected_clients[client_id].get('authenticated'):
            return {'success': False, 'message': 'Требуется авторизация. Выполните login.'}

        # ═══════════════════════════════════════════════════════
        # CRUD ОПЕРАЦИИ (требуют авторизации)
        # ═══════════════════════════════════════════════════════

        # Добавить отправление
        if action == 'add_shipment':
            try:
                shipment = Shipment(
                    client_id=request.get('client_id', 1),
                    office_from_id=request.get('office_from_id', 1),
                    office_to_id=request.get('office_to_id', 2),
                    delivery_method_id=request.get('delivery_method_id', 1),
                    cargo_type_id=request.get('cargo_type_id', 1),
                    weight_kg=request.get('weight_kg'),
                    description=request.get('description', ''),
                    special_requirements=request.get('special_requirements', ''),
                    status='registered'
                )

                shipment_id = self.repository.add(shipment)
                print(f"➕ Клиент {client_id} создал отправление #{shipment_id}")
                return {'success': True, 'shipment_id': shipment_id}

            except Exception as e:
                return {'success': False, 'message': f'Ошибка создания: {str(e)}'}

        # Получить отправления с фильтром
        elif action == 'get_shipments':
            results = self.repository.get_filtered(
                status=request.get('status'),
                min_weight=request.get('min_weight'),
                cargo_type=request.get('cargo_type')
            )
            return {'success': True, 'data': results}

        # Обновить отправление
        elif action == 'update_shipment':
            try:
                shipment_id = request.get('shipment_id')
                shipment = self.repository.get_by_id(shipment_id)

                if not shipment:
                    return {'success': False, 'message': 'Отправление не найдено'}

                # Обновляем поля
                if 'status' in request:
                    shipment.status = request['status']
                if 'weight_kg' in request:
                    shipment.weight_kg = request['weight_kg']

                self.repository.update(shipment)
                print(f"✏️  Клиент {client_id} обновил отправление #{shipment_id}")
                return {'success': True}

            except Exception as e:
                return {'success': False, 'message': f'Ошибка обновления: {str(e)}'}

        # 🔒 Удалить отправление (требование №5: только после авторизации!)
        elif action == 'delete_shipment':
            try:
                shipment_id = request.get('shipment_id')

                # Проверка уже выполнена выше (если не авторизован — не дойдёт сюда)
                success = self.repository.delete(shipment_id)

                if success:
                    print(f"🗑  Клиент {client_id} удалил отправление #{shipment_id}")
                    return {'success': True}
                else:
                    return {'success': False, 'message': 'Отправление не найдено'}

            except Exception as e:
                return {'success': False, 'message': f'Ошибка удаления: {str(e)}'}

        # Получить список подключённых клиентов
        elif action == 'list_clients':
            clients_info = []
            for cid, info in self.connected_clients.items():
                clients_info.append({
                    'address': cid,
                    'authenticated': info['authenticated'],
                    'username': info['username']
                })
            return {'success': True, 'clients': clients_info}

        # Неизвестное действие
        else:
            return {'success': False, 'message': f'Неизвестное действие: {action}'}

    def start(self):
        """Запуск сервера (бесконечный цикл)"""
        try:
            while True:
                # Принимаем новое подключение
                client_socket, address = self.server_socket.accept()

                # Создаём новый поток для обработки этого клиента
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                thread.daemon = True  # Поток завершится при закрытии программы
                thread.start()

        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен пользователем")
        finally:
            self.server_socket.close()


# ═══════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА: запуск сервера
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    # Инициализируем базу данных (создаём таблицы, если их нет)
    from server.database import engine
    from server.models import Base

    Base.metadata.create_all(bind=engine)

    # Запускаем сервер
    server = ShipmentServer(use_orm=USE_ORM)
    server.start()