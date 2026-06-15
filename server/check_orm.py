"""
Тестовый файл для проверки работы ORM-моделей.
Читает данные из PostgreSQL через Python-объекты (без SQL-запросов).
"""

from server.database import get_session
from server.models import Client, Shipment, User, City, Office, CargoType
from sqlalchemy import select

print("🔍 Начинаю тестирование ORM-чтения данных...\n")

# Получаем сессию для работы с БД
session = get_session()

try:
    # ═══════════════════════════════════════════════════════════════
    # ТЕСТ 1: Читаем всех клиентов из таблицы clients
    # ═══════════════════════════════════════════════════════════════
    print("=" * 60)
    print("📋 ТЕСТ 1: Чтение всех клиентов")
    print("=" * 60)

    # Это эквивалент SQL: SELECT * FROM clients
    clients = session.execute(select(Client)).scalars().all()

    print(f"Найдено клиентов: {len(clients)}")
    for client in clients:
        print(f"  {client}")  # Использует метод __repr__ из models.py

    # ═══════════════════════════════════════════════════════════════
    # ТЕСТ 2: Читаем всех пользователей системы
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("👤 ТЕСТ 2: Чтение всех пользователей системы")
    print("=" * 60)

    users = session.execute(select(User)).scalars().all()

    print(f"Найдено пользователей: {len(users)}")
    for user in users:
        print(f"  {user}")
        print(f"    └─ Хэш пароля: {user.password_hash[:20]}... (обрезан для читаемости)")

    # ═══════════════════════════════════════════════════════════════
    # ТЕСТ 3: Читаем отправления со связями (главная фишка ORM!)
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("📦 ТЕСТ 3: Чтение отправлений со связями")
    print("=" * 60)

    shipments = session.execute(select(Shipment)).scalars().all()

    print(f"Найдено отправлений: {len(shipments)}\n")

    for shipment in shipments[:3]:  # Берём только первые 3 для краткости
        print(f"Отправление #{shipment.shipment_id}:")
        print(f"  Статус: {shipment.status}")
        print(f"  Вес: {shipment.weight_kg} кг")

        # Вот здесь работает "магия" ORM — обращаемся к связанным таблицам через точку!
        print(f"  Клиент: {shipment.client.first_name} {shipment.client.last_name}")
        print(f"  Тип груза: {shipment.cargo_type.type_name}")
        print(f"  Способ доставки: {shipment.delivery_method.method_name}")
        print()

    # ═══════════════════════════════════════════════════════════════
    # ТЕСТ 4: Фильтрация (как WHERE в SQL)
    # ═══════════════════════════════════════════════════════════════
    print("=" * 60)
    print("🔎 ТЕСТ 4: Фильтрация отправлений по статусу")
    print("=" * 60)

    # Это эквивалент SQL: SELECT * FROM shipments WHERE status = 'in_transit'
    in_transit = session.execute(
        select(Shipment).where(Shipment.status == 'in_transit')
    ).scalars().all()

    print(f"Отправлений в пути (status='in_transit'): {len(in_transit)}")
    for s in in_transit:
        print(f"  #{s.shipment_id}: {s.cargo_type.type_name}, {s.weight_kg} кг")

    # ═══════════════════════════════════════════════════════════════
    # ТЕСТ 5: Чтение городов и офисов
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("🏢 ТЕСТ 5: Чтение городов и офисов")
    print("=" * 60)

    cities = session.execute(select(City)).scalars().all()
    print(f"Найдено городов: {len(cities)}")
    for city in cities[:3]:  # Первые 3 города
        print(f"  {city.city_name}, {city.country}")

    offices = session.execute(select(Office)).scalars().all()
    print(f"\nНайдено офисов: {len(offices)}")
    for office in offices[:3]:  # Первые 3 офиса
        print(f"  {office.office_name} (город: {office.city.city_name})")

    # ═══════════════════════════════════════════════════════════════
    # ФИНАЛ
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    print("\nЧто это значит:")
    print("  • Python может читать данные из PostgreSQL через объекты")
    print("  • Связи между таблицами работают (client, cargo_type и т.д.)")
    print("  • Фильтрация работает (WHERE)")
    print("  • Можно переходить к созданию авторизации!")

except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    print("\nВозможные причины:")
    print("  1. Не запущен сервер PostgreSQL")
    print("  2. Неверный пароль в файле database.py")
    print("  3. Таблицы не созданы в БД")

finally:
    # Всегда закрываем сессию!
    session.close()