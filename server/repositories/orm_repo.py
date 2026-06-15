"""
Файл orm_repo.py — реализация репозитория через SQLAlchemy ORM.
Это первая стратегия работы с БД (позже добавим вторую — через сырой SQL).
"""

from typing import List, Optional
from sqlalchemy import select

from server.database import get_session
from server.models import Shipment, CargoType
from server.repositories.base import IShipmentRepository


class OrmShipmentRepository(IShipmentRepository):
    """
    Реализация репозитория отправлений через ORM (SQLAlchemy).

    Наследуется от IShipmentRepository — значит, ОБЯЗАНА реализовать
    все его абстрактные методы (add, get_by_id, get_filtered, update, delete).
    """

    def add(self, shipment: Shipment) -> int:
        """Создание нового отправления через ORM"""
        session = get_session()
        try:
            # SQLAlchemy сам превратит это в INSERT INTO shipments...
            session.add(shipment)
            session.commit()
            session.refresh(shipment)  # Обновляем объект, чтобы получить ID из БД
            return shipment.shipment_id
        except Exception as e:
            session.rollback()  # Откатываем изменения при ошибке
            raise e
        finally:
            session.close()

    def get_by_id(self, shipment_id: int) -> Optional[Shipment]:
        """Получение отправления по ID через ORM"""
        session = get_session()
        try:
            # Эквивалент SQL: SELECT * FROM shipments WHERE shipment_id = ?
            stmt = select(Shipment).where(Shipment.shipment_id == shipment_id)
            result = session.execute(stmt).scalar_one_or_none()
            return result
        finally:
            session.close()

    def get_filtered(self, status: str = None, min_weight: float = None,
                     cargo_type: str = None) -> List[dict]:
        """
        Фильтрация отправлений через ORM (аналог WHERE в SQL).

        Это самое интересное: мы динамически добавляем условия WHERE,
        в зависимости от переданных параметров.
        """
        session = get_session()
        try:
            # Начинаем строить запрос
            stmt = select(Shipment)

            # Динамически добавляем фильтры (если параметры переданы)
            if status:
                stmt = stmt.where(Shipment.status == status)
            if min_weight is not None:
                stmt = stmt.where(Shipment.weight_kg >= min_weight)
            if cargo_type:
                # Соединяем с таблицей cargotypes для фильтрации по названию
                stmt = stmt.join(CargoType).where(CargoType.type_name == cargo_type)

            # Выполняем запрос
            shipments = session.execute(stmt).scalars().all()

            # Превращаем объекты в словари (для удобной передачи по сети)
            result = []
            for s in shipments:
                result.append({
                    'shipment_id': s.shipment_id,
                    'cargo_type': s.cargo_type.type_name if s.cargo_type else None,
                    'weight_kg': float(s.weight_kg),
                    'status': s.status,
                    'client_id': s.client_id,
                    'description': s.description
                })
            return result

        finally:
            session.close()

    def update(self, shipment: Shipment) -> bool:
        """Обновление отправления через ORM"""
        session = get_session()
        try:
            # SQLAlchemy сам поймёт, что нужно сделать UPDATE
            session.merge(shipment)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, shipment_id: int) -> bool:
        """Удаление отправления через ORM"""
        session = get_session()
        try:
            # Сначала находим объект
            stmt = select(Shipment).where(Shipment.shipment_id == shipment_id)
            shipment = session.execute(stmt).scalar_one_or_none()

            if not shipment:
                return False  # Не нашли — нечего удалять

            # Удаляем (SQLAlchemy сделает DELETE FROM...)
            session.delete(shipment)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()