from datetime import date

from sqlalchemy import (Boolean, CheckConstraint, Column, Date, ForeignKey,
                        Integer, Numeric, String)
from sqlalchemy.orm import relationship

from .db import Base

EQUIPMENT_STATUSES = ('в работе', 'в ремонте', 'в простое', 'выведено из эксплуатации')
REQUEST_STATUSES = ('создана', 'назначена', 'в работе', 'ожидает материалов',
                    'выполнена', 'закрыта', 'отменена')
PRIORITIES = ('низкий', 'средний', 'высокий', 'критический')
ROLES = ('администратор', 'мастер', 'сотрудник')


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    phone = Column(String(20), nullable=False, unique=True)
    role = Column(String(20), nullable=False)


class Equipment(Base):
    __tablename__ = 'equipment'
    __table_args__ = (
        CheckConstraint("status IN ('в работе','в ремонте','в простое',"
                        "'выведено из эксплуатации')", name='ck_equip_status'),
        CheckConstraint("work_start_date IS NULL OR work_start_date >= commissioning_date",
                        name='ck_equip_dates1'),
        CheckConstraint("work_start_date IS NULL OR work_start_date <= CURRENT_DATE",
                        name='ck_equip_dates2'),
        CheckConstraint("decommission_date IS NULL OR decommission_date > commissioning_date",
                        name='ck_equip_dates3'),
    )
    id = Column(Integer, primary_key=True)
    inventory_number = Column(String(20), nullable=False, unique=True)
    name = Column(String(150), nullable=False)
    model = Column(String(100))
    location = Column(String(150))
    status = Column(String(40), nullable=False, default='в работе')
    commissioning_date = Column(Date, nullable=False)
    work_start_date = Column(Date)
    decommission_date = Column(Date)
    requests = relationship('ServiceRequest', back_populates='equipment')


class ServiceRequest(Base):
    __tablename__ = 'service_requests'
    __table_args__ = (
        CheckConstraint("priority IN ('низкий','средний','высокий','критический')",
                        name='ck_req_priority'),
        CheckConstraint("status IN ('создана','назначена','в работе',"
                        "'ожидает материалов','выполнена','закрыта','отменена')",
                        name='ck_req_status'),
        CheckConstraint('created_date <= planned_start AND planned_start < planned_end',
                        name='ck_req_planned_dates'),
        CheckConstraint('actual_start IS NULL OR actual_start >= created_date',
                        name='ck_req_actual1'),
        CheckConstraint('actual_end IS NULL OR '
                        "(actual_start IS NOT NULL AND actual_start < actual_end)",
                        name='ck_req_actual2'),
    )
    id = Column(Integer, primary_key=True)
    request_number = Column(String(20), nullable=False, unique=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id', ondelete='RESTRICT'),
                          nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assignee_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String, nullable=False)
    priority = Column(String(15), nullable=False, default='средний')
    status = Column(String(25), nullable=False, default='создана')
    created_date = Column(Date, nullable=False, default=date.today)
    planned_start = Column(Date, nullable=False)
    planned_end = Column(Date, nullable=False)
    actual_start = Column(Date)
    actual_end = Column(Date)

    equipment = relationship('Equipment', back_populates='requests')
    materials = relationship('RequestMaterial', back_populates='request',
                             cascade='all, delete-orphan')


class Material(Base):
    __tablename__ = 'materials'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    unit = Column(String(20), nullable=False, default='шт.')
    price = Column(Numeric(12, 2), nullable=False, default=0)
    stock_qty = Column(Numeric(12, 2), nullable=False, default=0)


class RequestMaterial(Base):
    __tablename__ = 'request_materials'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('service_requests.id', ondelete='CASCADE'),
                        nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id', ondelete='RESTRICT'),
                         nullable=False)
    qty = Column(Numeric(10, 2), nullable=False)

    request = relationship('ServiceRequest', back_populates='materials')
    material = relationship('Material')


class Maintenance(Base):
    __tablename__ = 'maintenance_schedule'
    __table_args__ = (
        CheckConstraint('performed_date IS NULL OR performed_date >= planned_date',
                        name='ck_maint_dates'),
    )
    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id', ondelete='RESTRICT'),
                          nullable=False)
    planned_date = Column(Date, nullable=False)
    description = Column(String(300), nullable=False)
    performed = Column(Boolean, nullable=False, default=False)
    performed_date = Column(Date)
    performer_id = Column(Integer, ForeignKey('users.id'))
