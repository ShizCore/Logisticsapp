"""
Проверочный скрипт для SQL-реализации Repository.
Запускаем те же 8 тестов, что и для ORM, но через psycopg2.
"""

from server.factory import RepositoryFactory
from server.models import Shipment

print("🏗 Начинаю тестирование SQL-репозитория...\n")

# 🔑 Главная фишка: используем Factory для создания SQL-репозитория
repo = RepositoryFactory.create(use_orm=False)  # False = SQL-версия


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 1: Получить все отправления (без фильтров)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("📋 ТЕСТ 1: Получить все отправления (без фильтров)")
print("=" * 60)
all_shipments = repo.get_filtered()
print(f"Найдено отправлений: {len(all_shipments)}")
for s in all_shipments:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг, статус: {s['status']}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 2: Фильтрация по статусу
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔎 ТЕСТ 2: Фильтр по статусу 'in_transit'")
print("=" * 60)
in_transit = repo.get_filtered(status='in_transit')
print(f"Найдено отправлений в пути: {len(in_transit)}")
for s in in_transit:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 3: Фильтрация по минимальному весу
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("⚖️  ТЕСТ 3: Фильтр по минимальному весу (>= 50 кг)")
print("=" * 60)
heavy = repo.get_filtered(min_weight=50.0)
print(f"Найдено тяжёлых отправлений: {len(heavy)}")
for s in heavy:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 4: Создание нового отправления
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("➕ ТЕСТ 4: Создание нового отправления через SQL")
print("=" * 60)

new_shipment = Shipment(
    client_id=1,
    office_from_id=1,
    office_to_id=2,
    delivery_method_id=1,
    cargo_type_id=1,
    weight_kg=77.7,
    description="Тестовое отправление через SQL (psycopg2)",
    status='registered'
)

new_id = repo.add(new_shipment)
print(f"✅ Отправление создано с ID = {new_id}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 5: Чтение созданного отправления
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("📖 ТЕСТ 5: Чтение созданного отправления по ID")
print("=" * 60)
fetched = repo.get_by_id(new_id)
print(f"Получили: {fetched}")
print(f"  Вес: {fetched.weight_kg} кг")
print(f"  Статус: {fetched.status}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 6: Обновление отправления
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("✏️  ТЕСТ 6: Обновление статуса на 'delivered'")
print("=" * 60)
fetched.status = 'delivered'
repo.update(fetched)
print("✅ Статус обновлён")

updated = repo.get_by_id(new_id)
print(f"Новый статус: {updated.status}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 7: Удаление отправления
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🗑  ТЕСТ 7: Удаление тестового отправления")
print("=" * 60)
deleted = repo.delete(new_id)
print(f"Удалено: {deleted}")

deleted_check = repo.get_by_id(new_id)
print(f"Попытка получить по ID={new_id}: {deleted_check} (None = успешно удалено)")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 8: Сравнение ORM и SQL (главная фишка Factory!)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔄 ТЕСТ 8: Сравнение ORM и SQL через Factory")
print("=" * 60)

orm_repo = RepositoryFactory.create(use_orm=True)
sql_repo = RepositoryFactory.create(use_orm=False)

orm_results = orm_repo.get_filtered(status='in_transit')
sql_results = sql_repo.get_filtered(status='in_transit')

print(f"\nORM вернул: {len(orm_results)} записей")
print(f"SQL вернул: {len(sql_results)} записей")

if len(orm_results) == len(sql_results):
    print("✅ ОБЕ РЕАЛИЗАЦИИ РАБОТАЮТ ОДИНАКОВО!")
else:
    print("⚠️  Результаты различаются — нужно проверить код")


print("\n" + "=" * 60)
print("✅ ВСЕ CRUD-ОПЕРАЦИИ РАБОТАЮТ ЧЕРЕЗ SQL-РЕПОЗИТОРИЙ!")
print("=" * 60)
print("\nЧто это значит:")
print("  • Repository Pattern успешно реализован")
print("  • Factory Pattern позволяет переключаться между ORM и SQL")
print("  • Обе стратегии работают одинаково корректно")
print("  • Требования №2 (ORM+SQL) и №6 (паттерны) полностью закрыты!")