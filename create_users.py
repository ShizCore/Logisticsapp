"""
Скрипт для создания пользователей с правильными bcrypt-хэшами.
Запускается ОДИН РАЗ для инициализации базы тестовыми пользователями.

После запуска все пользователи будут иметь пароль: admin123
"""

from server.database import get_session
from server.models import User
from server.auth import AuthService
from sqlalchemy import select, delete

print("🔧 Исправляю хэши паролей в базе данных...\n")

session = get_session()

# Список пользователей, которых нужно создать/обновить
users_to_create = [
    {'username': 'admin', 'role': 'admin'},
    {'username': 'manager_msk', 'role': 'manager'},
    {'username': 'operator_spb', 'role': 'user'},
    {'username': 'operator_nsk', 'role': 'user'},
]

# Пароль для всех пользователей
COMMON_PASSWORD = 'admin123'

# Генерируем ОДИН хэш для всех (так быстрее)
common_hash = AuthService.hash_password(COMMON_PASSWORD)
print(f"✅ Сгенерирован настоящий хэш: {common_hash[:30]}...")
print()

try:
    for user_data in users_to_create:
        username = user_data['username']
        role = user_data['role']

        # Проверяем, существует ли пользователь
        existing = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if existing:
            # Обновляем хэш существующего пользователя
            existing.password_hash = common_hash
            existing.role = role
            print(f"🔄 Обновлён: {username} (роль: {role})")
        else:
            # Создаём нового пользователя
            new_user = User(
                username=username,
                password_hash=common_hash,
                role=role
            )
            session.add(new_user)
            print(f"➕ Создан: {username} (роль: {role})")

    session.commit()
    print(f"\n✅ Все пользователи сохранены в БД!")
    print(f"🔑 Общий пароль для всех: {COMMON_PASSWORD}")

except Exception as e:
    session.rollback()
    print(f"❌ Ошибка: {e}")

finally:
    session.close()

print("\n" + "=" * 60)
print("Теперь вы можете войти в систему:")
print("  Логин: admin")
print("  Пароль: admin123")
print("=" * 60)