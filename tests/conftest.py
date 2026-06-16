"""
Файл conftest.py — общие настройки и фикстуры для pytest.
Фикстуры — это подготовительные функции, которые создают тестовые данные.
"""

import pytest
from server.database import get_session
from server.models import User
from server.auth import AuthService


@pytest.fixture(scope="session")
def db_session():
    """
    Фикстура: создаёт сессию БД для всех тестов.
    scope="session" означает, что сессия создаётся один раз на все тесты.
    """
    session = get_session()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """
    Фикстура: создаёт тестового пользователя.
    Автоматически удаляет его после теста.
    """
    import time
    from sqlalchemy import select
    from server.models import User

    username = f"test_user_{int(time.time())}"
    password = "test_password_123"

    # Создаём пользователя через AuthService
    result = AuthService.register(username, password, role='user')

    # Ищем пользователя по username (надёжнее, чем брать из result)
    user = db_session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()

    user_id = user.user_id if user else None

    yield {
        'user_id': user_id,
        'username': username,
        'password': password
    }

    # Удаляем пользователя после теста
    if user:
        db_session.delete(user)
        db_session.commit()