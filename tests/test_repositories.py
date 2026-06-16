"""
Тесты паттерна Repository (ORM и SQL реализации).
Проверяют CRUD-операции и фильтрацию.
"""

import pytest
from server.models import Shipment
from server.factory import RepositoryFactory


class TestRepositoryPattern:
    """Тесты для обеих реализаций репозитория"""

    @pytest.fixture(params=[True, False])
    def repository(self, request):
        """
        Параметризованная фикстура: создаёт репозиторий.
        params=[True, False] означает, что каждый тест запустится ДВАЖДЫ:
        один раз с ORM (True), второй раз с SQL (False).
        """
        use_orm = request.param
        return RepositoryFactory.create(use_orm)

    def test_get_all_shipments(self, repository):
        """Тест: получение всех отправлений"""
        results = repository.get_filtered()

        # Должно быть минимум 4 отправления (из начального заполнения)
        assert isinstance(results, list)
        assert len(results) >= 4

    def test_filter_by_status(self, repository):
        """Тест: фильтрация по статусу"""
        results = repository.get_filtered(status='in_transit')

        # Все результаты должны иметь статус 'in_transit'
        assert all(item['status'] == 'in_transit' for item in results)

    def test_filter_by_min_weight(self, repository):
        """Тест: фильтрация по минимальному весу"""
        results = repository.get_filtered(min_weight=100.0)

        # Все результаты должны иметь вес >= 100
        assert all(item['weight_kg'] >= 100.0 for item in results)

    def test_filter_by_cargo_type(self, repository):
        """Тест: фильтрация по типу груза"""
        results = repository.get_filtered(cargo_type='Хрупкий')

        # Все результаты должны иметь тип 'Хрупкий'
        assert all(item['cargo_type'] == 'Хрупкий' for item in results)

    def test_complex_filter(self, repository):
        """Тест: комплексный фильтр (статус + вес)"""
        results = repository.get_filtered(
            status='in_transit',
            min_weight=50.0
        )

        # Все результаты должны соответствовать обоим условиям
        assert all(
            item['status'] == 'in_transit' and item['weight_kg'] >= 50.0
            for item in results
        )

    def test_add_and_retrieve_shipment(self, repository):
        """Тест: создание и чтение отправления"""
        # Создаём новое отправление
        shipment = Shipment(
            client_id=1,
            office_from_id=1,
            office_to_id=2,
            delivery_method_id=1,
            cargo_type_id=1,
            weight_kg=99.9,
            description="Тестовое отправление pytest",
            status='registered'
        )

        shipment_id = repository.add(shipment)
        assert shipment_id is not None

        # Читаем созданное отправление
        retrieved = repository.get_by_id(shipment_id)
        assert retrieved is not None
        assert float(retrieved.weight_kg) == 99.9
        assert retrieved.status == 'registered'

        # Удаляем после теста
        repository.delete(shipment_id)

    def test_update_shipment(self, repository):
        """Тест: обновление отправления"""
        # Создаём отправление
        shipment = Shipment(
            client_id=1,
            office_from_id=1,
            office_to_id=2,
            delivery_method_id=1,
            cargo_type_id=1,
            weight_kg=50.0,
            status='registered'
        )

        shipment_id = repository.add(shipment)

        # Обновляем статус
        shipment.shipment_id = shipment_id
        shipment.status = 'delivered'
        repository.update(shipment)

        # Проверяем, что обновилось
        updated = repository.get_by_id(shipment_id)
        assert updated.status == 'delivered'

        # Удаляем после теста
        repository.delete(shipment_id)

    def test_delete_shipment(self, repository):
        """Тест: удаление отправления"""
        # Создаём отправление
        shipment = Shipment(
            client_id=1,
            office_from_id=1,
            office_to_id=2,
            delivery_method_id=1,
            cargo_type_id=1,
            weight_kg=25.0,
            status='registered'
        )

        shipment_id = repository.add(shipment)

        # Удаляем
        deleted = repository.delete(shipment_id)
        assert deleted is True

        # Проверяем, что удалено
        retrieved = repository.get_by_id(shipment_id)
        assert retrieved is None

    def test_orm_and_sql_return_same_results(self):
        """Тест: ORM и SQL возвращают одинаковые результаты"""
        orm_repo = RepositoryFactory.create(use_orm=True)
        sql_repo = RepositoryFactory.create(use_orm=False)

        # Получаем все отправления через обе реализации
        orm_results = orm_repo.get_filtered(status='in_transit')
        sql_results = sql_repo.get_filtered(status='in_transit')

        # Количество должно совпадать
        assert len(orm_results) == len(sql_results)

        # ID отправлений должны совпадать
        orm_ids = {item['shipment_id'] for item in orm_results}
        sql_ids = {item['shipment_id'] for item in sql_results}
        assert orm_ids == sql_ids