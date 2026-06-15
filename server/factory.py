"""
Файл factory.py — паттерн Factory (Фабрика).
Создаёт нужный репозиторий (ORM или SQL) по запросу.

Использование:
    repo = RepositoryFactory.create(use_orm=True)   # ORM-версия
    repo = RepositoryFactory.create(use_orm=False)  # SQL-версия
"""

from server.repositories.base import IShipmentRepository
from server.repositories.orm_repo import OrmShipmentRepository
from server.repositories.sql_repo import SqlRawShipmentRepository


class RepositoryFactory:
    """
    Фабрика репозиториев.
    Позволяет создавать ORM или SQL реализацию по требованию.
    """

    @staticmethod
    def create(use_orm: bool = True) -> IShipmentRepository:
        """
        Создаёт и возвращает репозиторий.

        Параметры:
        - use_orm: True → ORM (SQLAlchemy), False → SQL (psycopg2)

        Возвращает:
        - Объект, реализующий интерфейс IShipmentRepository
        """
        if use_orm:
            print("🏭 [Factory] Создан ORM-репозиторий (SQLAlchemy)")
            return OrmShipmentRepository()
        else:
            print("🏭 [Factory] Создан SQL-репозиторий (psycopg2)")
            return SqlRawShipmentRepository()