"""
Файл base.py — абстрактный базовый класс для всех репозиториев.
Здесь описан "контракт": какие методы ОБЯЗАНЫ быть у любого репозитория.

Зачем это нужно?
- Мы точно знаем, какие функции можно вызывать
- Можно создать две реализации (ORM и SQL), и обе будут соответствовать этому контракту
- Это и есть паттерн Repository + Strategy
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from server.models import Shipment


class IShipmentRepository(ABC):
    """
    Интерфейс репозитория отправлений.
    ABC = Abstract Base Class (абстрактный базовый класс).
    Нельзя создать объект этого класса напрямую, можно только наследоваться от него.
    """

    @abstractmethod
    def add(self, shipment: Shipment) -> int:
        """
        Добавить новое отправление в БД.
        Возвращает ID созданного отправления.
        """
        pass  # pass означает "здесь будет код в наследниках"

    @abstractmethod
    def get_by_id(self, shipment_id: int) -> Optional[Shipment]:
        """
        Получить отправление по его ID.
        Возвращает объект Shipment или None, если не найдено.
        """
        pass

    @abstractmethod
    def get_filtered(self, status: str = None, min_weight: float = None,
                     cargo_type: str = None) -> List[dict]:
        """
        Получить список отправлений с применением фильтров.

        Параметры:
        - status: фильтр по статусу ('registered', 'in_transit', 'delivered')
        - min_weight: фильтр по минимальному весу
        - cargo_type: фильтр по типу груза

        Возвращает список словарей с данными отправлений.
        """
        pass

    @abstractmethod
    def update(self, shipment: Shipment) -> bool:
        """
        Обновить данные существующего отправления.
        Возвращает True, если успешно.
        """
        pass

    @abstractmethod
    def delete(self, shipment_id: int) -> bool:
        """
        Удалить отправление по ID.
        Возвращает True, если успешно удалено.
        """
        pass