"""
Файл sql_repo.py — реализация репозитория через сырые SQL-запросы (psycopg2).
Это вторая стратегия работы с БД (первая была через ORM в orm_repo.py).

Зачем это нужно?
- Показать, что Repository Pattern позволяет легко переключаться между реализациями
- Иногда сырой SQL быстрее ORM для сложных запросов
- Требование преподавателя: "CRUD в двух вариантах: ORM и SQL"
"""

import psycopg2
from typing import List, Optional

from server.models import Shipment
from server.repositories.base import IShipmentRepository

# Настройки подключения к PostgreSQL
# ⚠️ ЗАМЕНИТЕ "ВАШ_ПАРОЛЬ" на ваш реальный пароль от PostgreSQL!
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'logistics',
    'user': 'postgres',
    'password': '1234'  # Например: 'admin' или '1234'
}


class SqlRawShipmentRepository(IShipmentRepository):
    """
    Реализация репозитория отправлений через сырой SQL (psycopg2).
    """

    def _get_connection(self):
        """Вспомогательный метод: создаёт новое подключение к БД."""
        return psycopg2.connect(**DB_CONFIG)

    def add(self, shipment: Shipment) -> int:
        """Создание нового отправления через сырой SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            query = """
                INSERT INTO shipments 
                (client_id, office_from_id, office_to_id, delivery_method_id, 
                 cargo_type_id, weight_kg, description, special_requirements, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING shipment_id
            """

            params = (
                shipment.client_id,
                shipment.office_from_id,
                shipment.office_to_id,
                shipment.delivery_method_id,
                shipment.cargo_type_id,
                float(shipment.weight_kg),
                shipment.description,
                shipment.special_requirements,
                shipment.status
            )

            cursor.execute(query, params)
            shipment_id = cursor.fetchone()[0]
            conn.commit()
            return shipment_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_by_id(self, shipment_id: int) -> Optional[Shipment]:
        """Получение отправления по ID через сырой SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            query = """
                SELECT shipment_id, client_id, office_from_id, office_to_id,
                       delivery_method_id, cargo_type_id, weight_kg, description,
                       special_requirements, status
                FROM shipments
                WHERE shipment_id = %s
            """

            cursor.execute(query, (shipment_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return Shipment(
                shipment_id=row[0],
                client_id=row[1],
                office_from_id=row[2],
                office_to_id=row[3],
                delivery_method_id=row[4],
                cargo_type_id=row[5],
                weight_kg=row[6],
                description=row[7],
                special_requirements=row[8],
                status=row[9]
            )

        finally:
            conn.close()

    def get_filtered(self, status: str = None, min_weight: float = None,
                     cargo_type: str = None) -> List[dict]:
        """Фильтрация отправлений через динамический SQL-запрос."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            query = """
                SELECT s.shipment_id, s.client_id, s.weight_kg, s.status,
                       s.description, ct.type_name
                FROM shipments s
                LEFT JOIN cargotypes ct ON s.cargo_type_id = ct.cargo_type_id
            """

            conditions = []
            params = []

            if status:
                conditions.append("s.status = %s")
                params.append(status)

            if min_weight is not None:
                conditions.append("s.weight_kg >= %s")
                params.append(min_weight)

            if cargo_type:
                conditions.append("ct.type_name = %s")
                params.append(cargo_type)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    'shipment_id': row[0],
                    'client_id': row[1],
                    'weight_kg': float(row[2]),
                    'status': row[3],
                    'description': row[4],
                    'cargo_type': row[5]
                })

            return result

        finally:
            conn.close()

    def update(self, shipment: Shipment) -> bool:
        """Обновление отправления через сырой SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            query = """
                UPDATE shipments
                SET client_id = %s,
                    office_from_id = %s,
                    office_to_id = %s,
                    delivery_method_id = %s,
                    cargo_type_id = %s,
                    weight_kg = %s,
                    description = %s,
                    special_requirements = %s,
                    status = %s
                WHERE shipment_id = %s
            """

            params = (
                shipment.client_id,
                shipment.office_from_id,
                shipment.office_to_id,
                shipment.delivery_method_id,
                shipment.cargo_type_id,
                float(shipment.weight_kg),
                shipment.description,
                shipment.special_requirements,
                shipment.status,
                shipment.shipment_id
            )

            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete(self, shipment_id: int) -> bool:
        """Удаление отправления через сырой SQL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            query = "DELETE FROM shipments WHERE shipment_id = %s"
            cursor.execute(query, (shipment_id,))
            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()