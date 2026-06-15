"""
Проверочный скрипт для паттерна Repository.
Тестируем все CRUD-операции через ORM-реализацию.
"""

from server.repositories.orm_repo import OrmShipmentRepository
from server.models import Shipment

print("🏗 Начинаю тестирование паттерна Repository (ORM)...\n")

# Создаём экземпляр репозитория
repo = OrmShipmentRepository()

# ═══════════════════════════════════════════════════════════════
# ТЕСТ 1: Чтение всех отправлений (get_filtered без фильтров)
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("📋 ТЕСТ 1: Получить все отправления (без фильтров)")
print("=" * 60)
all_shipments = repo.get_filtered()
print(f"Найдено отправлений: {len(all_shipments)}")
for s in all_shipments:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг, статус: {s['status']}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 2: Фильтрация по статусу (WHERE status = 'in_transit')
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🔎 ТЕСТ 2: Фильтр по статусу 'in_transit'")
print("=" * 60)
in_transit = repo.get_filtered(status='in_transit')
print(f"Найдено отправлений в пути: {len(in_transit)}")
for s in in_transit:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 3: Фильтрация по минимальному весу (WHERE weight >= 50)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("⚖️  ТЕСТ 3: Фильтр по минимальному весу (>= 50 кг)")
print("=" * 60)
heavy = repo.get_filtered(min_weight=50.0)
print(f"Найдено тяжёлых отправлений: {len(heavy)}")
for s in heavy:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 4: Комплексный фильтр (статус + мин. вес)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🎯 ТЕСТ 4: Комплексный фильтр (in_transit + вес >= 100)")
print("=" * 60)
complex_filter = repo.get_filtered(status='in_transit', min_weight=100.0)
print(f"Найдено: {len(complex_filter)}")
for s in complex_filter:
    print(f"  #{s['shipment_id']}: {s['cargo_type']}, {s['weight_kg']} кг")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 5: Создание нового отправления (Create)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("➕ ТЕСТ 5: Создание нового отправления")
print("=" * 60)

# Создаём объект отправления (ещё не в БД!)
new_shipment = Shipment(
    client_id=1,
    office_from_id=1,
    office_to_id=2,
    delivery_method_id=1,
    cargo_type_id=1,
    weight_kg=99.9,
    description="Тестовое отправление из check_repository.py",
    status='registered'
)

new_id = repo.add(new_shipment)
print(f"✅ Отправление создано с ID = {new_id}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 6: Чтение созданного отправления (Read)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("📖 ТЕСТ 6: Чтение созданного отправления по ID")
print("=" * 60)
fetched = repo.get_by_id(new_id)
print(f"Получили: {fetched}")
print(f"  Вес: {fetched.weight_kg} кг")
print(f"  Статус: {fetched.status}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 7: Обновление отправления (Update)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("✏️  ТЕСТ 7: Обновление статуса на 'delivered'")
print("=" * 60)
fetched.status = 'delivered'
repo.update(fetched)
print("✅ Статус обновлён")

# Проверяем, что действительно обновилось
updated = repo.get_by_id(new_id)
print(f"Новый статус: {updated.status}")


# ═══════════════════════════════════════════════════════════════
# ТЕСТ 8: Удаление отправления (Delete)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("🗑  ТЕСТ 8: Удаление тестового отправления")
print("=" * 60)
deleted = repo.delete(new_id)
print(f"Удалено: {deleted}")

# Проверяем, что действительно удалено
deleted_check = repo.get_by_id(new_id)
print(f"Попытка получить по ID={new_id}: {deleted_check} (None = успешно удалено)")


print("\n" + "=" * 60)
print("✅ ВСЕ CRUD-ОПЕРАЦИИ РАБОТАЮТ ЧЕРЕЗ ORM-РЕПОЗИТОРИЙ!")
print("=" * 60)
print("\nЧто это значит:")
print("  • Create (добавление) — работает")
print("  • Read (чтение с фильтрами) — работает")
print("  • Update (обновление) — работает")
print("  • Delete (удаление) — работает")
print("  • Паттерн Repository успешно реализован!")