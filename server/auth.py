"""
Файл auth.py — система авторизации и работы с паролями.
Здесь мы хэшируем пароли (чтобы не хранить их в открытом виде)
и проверяем логин/пароль при входе в систему.
"""

import bcrypt
from server.database import get_session
from server.models import User
from sqlalchemy import select


class AuthService:
    """Класс для управления авторизацией"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Превращает обычный пароль в безопасный хэш.
        Например: 'admin123' -> '$2b$12$xyz...'
        """
        # Генерируем "соль" (случайные символы для уникальности хэша)
        salt = bcrypt.gensalt()
        # Хэшируем пароль (преобразуем строку в байты, хэшируем, обратно в строку)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Проверяет, совпадает ли введенный пароль с хэшем из базы.
        Возвращает True (совпадает) или False (не совпадает).
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def register(username: str, password: str, role: str = 'user') -> dict:
        """
        Регистрирует нового пользователя и сохраняет его в БД.
        Возвращает словарь с результатом (успех или ошибка).
        """
        session = get_session()
        try:
            # 1. Проверяем, нет ли уже такого логина в базе
            existing_user = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()

            if existing_user:
                return {'success': False, 'message': 'Пользователь уже существует'}

            # 2. Создаем нового пользователя
            new_user = User(
                username=username,
                password_hash=AuthService.hash_password(password),  # Хэшируем пароль!
                role=role
            )

            # 3. Сохраняем в БД
            session.add(new_user)
            session.commit()

            return {'success': True, 'message': f'Пользователь {username} успешно создан'}

        except Exception as e:
            session.rollback()  # Отменяем изменения в БД, если была ошибка
            return {'success': False, 'message': f'Ошибка базы данных: {str(e)}'}
        finally:
            session.close()  # Всегда закрываем сессию!

    @staticmethod
    def login(username: str, password: str) -> dict:
        """
        Авторизация: проверка логина и пароля.
        """
        session = get_session()
        try:
            # 1. Ищем пользователя в БД по логину
            user = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()

            if not user:
                return {'success': False, 'message': 'Пользователь не найден'}

            # 2. Проверяем пароль (сравниваем введенный с хэшем из БД)
            if not AuthService.verify_password(password, user.password_hash):
                return {'success': False, 'message': 'Неверный пароль'}

            # 3. Если всё верно, возвращаем успех и данные пользователя
            return {
                'success': True,
                'message': 'Вход выполнен успешно',
                'user_id': user.user_id,
                'role': user.role
            }

        except Exception as e:
            return {'success': False, 'message': f'Ошибка: {str(e)}'}
        finally:
            session.close()