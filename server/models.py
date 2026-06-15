"""
Файл models.py — описание всех таблиц базы данных в виде Python-классов.
Это ORM-модели: SQLAlchemy автоматически переводит их в SQL-запросы.

Каждый класс = одна таблица в PostgreSQL.
Каждый атрибут = одна колонка в таблице.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, Date, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ═══════════════════════════════════════════════════════════════
# БАЗОВЫЙ КЛАСС (родитель для всех моделей)
# ═══════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """
    Базовый класс. От него наследуются все остальные модели.
    Сам по себе ничего не делает, нужен для SQLAlchemy.
    """
    pass


# ═══════════════════════════════════════════════════════════════
# СПРАВОЧНИКИ (таблицы-каталоги, меняются редко)
# ═══════════════════════════════════════════════════════════════

class City(Base):
    """
    Таблица cities — города, откуда/куда осуществляются перевозки.
    Пример: Москва, Санкт-Петербург, Минск.
    """
    __tablename__ = 'cities'  # Имя таблицы в PostgreSQL (обязательно!)

    # Колонки таблицы:
    city_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)

    # Связь с таблицей offices (один город -> много офисов)
    offices: Mapped[List["Office"]] = relationship("Office", back_populates="city")


class CargoType(Base):
    """
    Таблица cargotypes — типы грузов.
    Пример: Хрупкий, Опасный, Жидкость, Скоропортящийся.
    """
    __tablename__ = 'cargotypes'

    cargo_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requires_temp_control: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связь с таблицей shipments
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="cargo_type")


class DeliveryMethod(Base):
    """
    Таблица deliverymethods — способы доставки.
    Пример: Наземный (Авто), Воздушный, Железнодорожный.
    """
    __tablename__ = 'deliverymethods'

    delivery_method_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    method_name: Mapped[str] = mapped_column(String(50), nullable=False)
    speed_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связь с таблицей shipments
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="delivery_method")


# ═══════════════════════════════════════════════════════════════
# ОРГАНИЗАЦИОННЫЕ ТАБЛИЦЫ
# ═══════════════════════════════════════════════════════════════

class Office(Base):
    """
    Таблица offices — отделения компании в разных городах.
    Пример: "Логистик-Мск Центр" в Москве.
    """
    __tablename__ = 'offices'

    office_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    office_name: Mapped[str] = mapped_column(String(100), nullable=False)
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.city_id'), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Связь: у каждого офиса есть один город
    city: Mapped["City"] = relationship("City", back_populates="offices")


class Client(Base):
    """
    Таблица clients — клиенты (отправители грузов).
    Пример: Иван Петров, отправляющий посылку.
    """
    __tablename__ = 'clients'

    client_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    registration_date: Mapped[datetime] = mapped_column(Date, default=datetime.utcnow)

    # Связь: один клиент может иметь много отправлений
    shipments: Mapped[List["Shipment"]] = relationship("Shipment", back_populates="client")

    # Метод для красивого отображения объекта (удобно при отладке)
    def __repr__(self):
        return f"<Клиент(id={self.client_id}, имя='{self.first_name} {self.last_name}')>"


class User(Base):
    """
    Таблица users — пользователи системы (сотрудники компании).
    Это те, кто логинится в программу.
    """
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # Хэш пароля (bcrypt)
    role: Mapped[str] = mapped_column(String(20), default='user')  # admin / manager / user
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Пользователь(id={self.user_id}, логин='{self.username}', роль='{self.role}')>"


# ═══════════════════════════════════════════════════════════════
# ГЛАВНЫЕ БИЗНЕС-ТАБЛИЦЫ
# ═══════════════════════════════════════════════════════════════

class Rate(Base):
    """
    Таблица rates — тарифы на перевозку.
    Хранит цену за кг по маршруту "город А -> город Б" для конкретного типа груза.
    """
    __tablename__ = 'rates'

    rate_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_method_id: Mapped[int] = mapped_column(Integer, ForeignKey('deliverymethods.delivery_method_id'),
                                                    nullable=False)
    cargo_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('cargotypes.cargo_type_id'), nullable=False)
    from_city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.city_id'), nullable=False)
    to_city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.city_id'), nullable=False)
    price_per_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)


class Shipment(Base):
    """
    Таблица shipments — отправления. ЭТО ГЛАВНАЯ ТАБЛИЦА СИСТЕМЫ!
    Каждая запись = одно отправление груза от клиента.
    """
    __tablename__ = 'shipments'

    shipment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey('clients.client_id', ondelete='CASCADE'), nullable=False)
    office_from_id: Mapped[int] = mapped_column(Integer, ForeignKey('offices.office_id'), nullable=False)
    office_to_id: Mapped[int] = mapped_column(Integer, ForeignKey('offices.office_id'), nullable=False)
    delivery_method_id: Mapped[int] = mapped_column(Integer, ForeignKey('deliverymethods.delivery_method_id'),
                                                    nullable=False)
    cargo_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('cargotypes.cargo_type_id'), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    special_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20),
                                        default='registered')  # registered / in_transit / delivered / cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Связи с другими таблицами (это "магия" ORM — можно обращаться через точку)
    client: Mapped["Client"] = relationship("Client", back_populates="shipments")
    cargo_type: Mapped["CargoType"] = relationship("CargoType", back_populates="shipments")
    delivery_method: Mapped["DeliveryMethod"] = relationship("DeliveryMethod", back_populates="shipments")
    tracking_events: Mapped[List["ShipmentTracking"]] = relationship("ShipmentTracking", back_populates="shipment")

    def __repr__(self):
        return f"<Отправление(id={self.shipment_id}, статус='{self.status}', вес={self.weight_kg} кг)>"


class ShipmentTracking(Base):
    """
    Таблица shipmenttracking — история перемещений отправления (лог событий).
    Пример: "Груз принят на складе", "Груз в пути", "Груз доставлен".
    """
    __tablename__ = 'shipmenttracking'

    tracking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey('shipments.shipment_id', ondelete='CASCADE'),
                                             nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связь: каждая запись относится к одному отправлению
    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="tracking_events")


# ═══════════════════════════════════════════════════════════════
# ПРОВЕРКА: если файл запущен напрямую, выводим список моделей
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("📋 Список всех ORM-моделей:")
    print(f"   1. {City.__name__} — города")
    print(f"   2. {CargoType.__name__} — типы грузов")
    print(f"   3. {DeliveryMethod.__name__} — способы доставки")
    print(f"   4. {Office.__name__} — отделения компании")
    print(f"   5. {Client.__name__} — клиенты")
    print(f"   6. {User.__name__} — пользователи системы")
    print(f"   7. {Rate.__name__} — тарифы")
    print(f"   8. {Shipment.__name__} — отправления (главная таблица)")
    print(f"   9. {ShipmentTracking.__name__} — история перемещений")
    print("\n✅ Файл models.py успешно загружен!")
    print("   Теперь Python 'понимает' структуру вашей базы данных.")