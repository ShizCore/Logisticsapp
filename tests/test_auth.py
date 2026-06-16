"""
Тесты системы авторизации (AuthService).
Проверяют хэширование паролей, регистрацию и вход.
"""

import pytest
from server.auth import AuthService


class TestAuthService:
    """Тесты для класса AuthService"""

    def test_hash_password_creates_valid_hash(self):
        """Тест: хэширование создаёт валидный bcrypt-хэш"""
        password = "MySecurePassword123!"
        hashed = AuthService.hash_password(password)

        # Хэш должен быть длиной 60 символов
        assert len(hashed) == 60
        # Хэш не должен совпадать с паролем
        assert hashed != password
        # Хэш должен начинаться с $2b$ (bcrypt)
        assert hashed.startswith('$2b$')

    def test_verify_password_with_correct_password(self):
        """Тест: верификация с правильным паролем возвращает True"""
        password = "TestPassword456!"
        hashed = AuthService.hash_password(password)

        is_valid = AuthService.verify_password(password, hashed)
        assert is_valid is True

    def test_verify_password_with_wrong_password(self):
        """Тест: верификация с неправильным паролем возвращает False"""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = AuthService.hash_password(password)

        is_valid = AuthService.verify_password(wrong_password, hashed)
        assert is_valid is False

    def test_register_new_user(self, test_user):
        """Тест: регистрация нового пользователя"""
        # test_user — это фикстура из conftest.py
        assert test_user['user_id'] is not None
        assert test_user['username'].startswith('test_user_')

    def test_login_with_correct_credentials(self, test_user):
        """Тест: вход с правильными учётными данными"""
        result = AuthService.login(test_user['username'], test_user['password'])

        assert result['success'] is True
        assert result['user_id'] == test_user['user_id']
        assert result['role'] == 'user'

    def test_login_with_wrong_password(self, test_user):
        """Тест: вход с неправильным паролем"""
        result = AuthService.login(test_user['username'], "wrong_password")

        assert result['success'] is False
        assert 'Неверный пароль' in result['message']

    def test_login_with_nonexistent_user(self):
        """Тест: вход с несуществующим пользователем"""
        result = AuthService.login("nonexistent_user_12345", "password")

        assert result['success'] is False
        assert 'не найден' in result['message']

    def test_register_duplicate_user(self, test_user):
        """Тест: попытка зарегистрировать дубликат"""
        result = AuthService.register(
            test_user['username'],
            "another_password",
            role='user'
        )

        assert result['success'] is False
        assert 'существует' in result['message']