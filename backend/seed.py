"""Запуск: python -m backend.seed (после init.sql или автоматом через lifespan)"""

from backend.db import SessionLocal, engine
from backend import models
from backend.security import hash_password


def run():
    models.Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            db.add_all([
                models.User(login='admin', password_hash=hash_password('admin'),
                            full_name='Иванов Иван Иванович',
                            email='admin@company.ru', phone='+79000000001',
                            role='администратор'),
                models.User(login='master', password_hash=hash_password('master'),
                            full_name='Петров Пётр Петрович',
                            email='master@company.ru', phone='+79000000002',
                            role='мастер'),
                models.User(login='user', password_hash=hash_password('user'),
                            full_name='Сидорова Анна Сергеевна',
                            email='user@company.ru', phone='+79000000003',
                            role='сотрудник'),
            ])
        if db.query(models.Equipment).count() == 0:
            db.add_all([
                models.Equipment(inventory_number='INV-0001', name='Станок токарный',
                                 model='16К20', location='Цех №1',
                                 commissioning_date='2023-03-15',
                                 work_start_date='2023-03-20'),
                models.Equipment(inventory_number='INV-0002', name='Пресс гидравлический',
                                 model='ПГ-200', location='Цех №2',
                                 status='в ремонте',
                                 commissioning_date='2022-08-01',
                                 work_start_date='2022-08-10'),
                models.Equipment(inventory_number='INV-0003', name='Компрессор',
                                 model='К-5', location='Цех №3',
                                 status='в простое',
                                 commissioning_date='2021-01-10',
                                 work_start_date='2021-01-15'),
            ])
        if db.query(models.Material).count() == 0:
            db.add_all([
                models.Material(name='Подшипник 6205', unit='шт.', price=350, stock_qty=40),
                models.Material(name='Смазка литол', unit='кг', price=500, stock_qty=15),
                models.Material(name='Ремень приводной A-1000', unit='шт.', price=420,
                                stock_qty=8),
            ])
        if db.query(models.Maintenance).count() == 0:
            db.add_all([
                models.Maintenance(equipment_id=1, planned_date='2026-12-01',
                                   description='Плановое ТО-1'),
                models.Maintenance(equipment_id=3, planned_date='2026-11-01',
                                   description='Замена масла',
                                   performed=True, performed_date='2026-11-02',
                                   performer_id=2),
            ])
        db.commit()
        print('Тестовые данные загружены.')
    finally:
        db.close()


if __name__ == '__main__':
    run()
