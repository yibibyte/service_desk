-- ============================================================
-- Тестовые данные для БД учета оборудования (PostgreSQL)
-- Пароль для всех пользователей: 123456
-- ============================================================

-- 1. Пользователи (users)
INSERT INTO users (login, password_hash, full_name, email, phone, role) VALUES
('admin',  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Иванов Иван Иванович',    'admin@company.ru',  '+79001112233', 'администратор'),
('master', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Петров Пётр Петрович',    'master@company.ru', '+79002223344', 'мастер'),
('user',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Сидорова Анна Сергеевна', 'user@company.ru',   '+79003334455', 'сотрудник')
ON CONFLICT (login) DO NOTHING;

-- 2. Оборудование (equipment)
INSERT INTO equipment (inventory_number, name, model, location, status, commissioning_date, work_start_date, decommission_date) VALUES
('INV-001', 'Токарный станок с ЧПУ',          'HAAS ST-10',       'Цех №1, участок А', 'в работе',                 '2022-03-15', '2022-03-20', NULL),
('INV-002', 'Фрезерный обрабатывающий центр', 'DMG MORI CMX 600', 'Цех №1, участок Б', 'в ремонте',                '2021-06-10', '2021-06-15', NULL),
('INV-003', 'Компрессор винтовой',            'Atlas Copco GA15', 'Компрессорная №2',  'в простое',                '2020-11-01', '2020-11-05', NULL),
('INV-004', 'Сварочный полуавтомат',          'Kemppi FastMig M', 'Цех №2, пост 4',    'в работе',                 '2023-01-12', '2023-01-15', NULL),
('INV-005', 'Сверлильный станок',             '2Н135',            'Склад списания',    'выведено из эксплуатации', '2010-05-10', '2010-05-12', '2025-12-01')
ON CONFLICT (inventory_number) DO NOTHING;

-- 3. Материалы и запчасти (materials)
INSERT INTO materials (name, unit, price, stock_qty) VALUES
('Подшипник радиально-упорный 7208', 'шт.', 3200.00, 12.00),
('Масло компрессорное VDL 46',       'л',    650.00, 50.00),
('Фильтр воздушный GA15',            'шт.', 4800.00,  4.00),
('Ролик подающий 1.0-1.2 мм',        'шт.', 1900.00,  6.00),
('СОЖ концентрат Универсал',         'л',    420.00, 80.00);

-- 4. Заявки на обслуживание (service_requests)
-- Даты привязаны к CURRENT_DATE для соблюдения CHECK (created_date <= planned_start < planned_end)
INSERT INTO service_requests (
    request_number, equipment_id, author_id, assignee_id, description,
    priority, status, created_date, planned_start, planned_end, actual_start, actual_end
) VALUES
(
    'REQ-2026-001',
    (SELECT id FROM equipment WHERE inventory_number = 'INV-002'),
    (SELECT id FROM users WHERE login = 'user'),
    (SELECT id FROM users WHERE login = 'master'),
    'Посторонний шум в шпинделе при высоких оборотах, замена подшипников',
    'высокий', 'в работе',
    CURRENT_DATE, CURRENT_DATE, CURRENT_DATE + INTERVAL '3 days', CURRENT_DATE, NULL
),
(
    'REQ-2026-002',
    (SELECT id FROM equipment WHERE inventory_number = 'INV-003'),
    (SELECT id FROM users WHERE login = 'user'),
    NULL,
    'Падение давления на выходе ниже 6 бар, утечка в магистрали',
    'критический', 'создана',
    CURRENT_DATE, CURRENT_DATE + INTERVAL '1 day', CURRENT_DATE + INTERVAL '2 days', NULL, NULL
),
(
    'REQ-2026-003',
    (SELECT id FROM equipment WHERE inventory_number = 'INV-001'),
    (SELECT id FROM users WHERE login = 'master'),
    (SELECT id FROM users WHERE login = 'master'),
    'Плановая замена СОЖ и калибровка резцедержателя',
    'низкий', 'назначена',
    CURRENT_DATE, CURRENT_DATE + INTERVAL '2 days', CURRENT_DATE + INTERVAL '4 days', NULL, NULL
),
(
    'REQ-2026-004',
    (SELECT id FROM equipment WHERE inventory_number = 'INV-004'),
    (SELECT id FROM users WHERE login = 'user'),
    (SELECT id FROM users WHERE login = 'master'),
    'Замена подающего ролика проволоки',
    'средний', 'ожидает материалов',
    CURRENT_DATE, CURRENT_DATE + INTERVAL '1 day', CURRENT_DATE + INTERVAL '5 days', NULL, NULL
)
ON CONFLICT (request_number) DO NOTHING;

-- 5. Расход материалов по заявкам (request_materials)
INSERT INTO request_materials (request_id, material_id, qty) VALUES
(
    (SELECT id FROM service_requests WHERE request_number = 'REQ-2026-001'),
    (SELECT id FROM materials WHERE name = 'Подшипник радиально-упорный 7208' LIMIT 1),
    2.00
),
(
    (SELECT id FROM service_requests WHERE request_number = 'REQ-2026-003'),
    (SELECT id FROM materials WHERE name = 'СОЖ концентрат Универсал' LIMIT 1),
    15.00
),
(
    (SELECT id FROM service_requests WHERE request_number = 'REQ-2026-004'),
    (SELECT id FROM materials WHERE name = 'Ролик подающий 1.0-1.2 мм' LIMIT 1),
    1.00
);

-- 6. График технического обслуживания (maintenance_schedule)
INSERT INTO maintenance_schedule (equipment_id, planned_date, description, performed, performed_date, performer_id) VALUES
(
    (SELECT id FROM equipment WHERE inventory_number = 'INV-001'),
    CURRENT_DATE + INTERVAL '10 days',
    'Ежеквартальное ТО: проверка направляющих и уровня масла',
    FALSE, NULL, NULL
),
(
    (SELECT id FROM equipment WHERE inventory_number = 'INV-002'),
    CURRENT_DATE - INTERVAL '15 days',
    'Замена воздушных фильтров и проверка гидравлики',
    TRUE, CURRENT_DATE - INTERVAL '14 days',
    (SELECT id FROM users WHERE login = 'master')
),
(
    (SELECT id FROM equipment WHERE inventory_number = 'INV-003'),
    CURRENT_DATE + INTERVAL '5 days',
    'Замена масляного сепаратора и приводного ремня',
    FALSE, NULL, (SELECT id FROM users WHERE login = 'master')
),
(
    (SELECT id FROM equipment WHERE inventory_number = 'INV-004'),
    CURRENT_DATE + INTERVAL '20 days',
    'Проверка изоляции кабелей и чистка блока охлаждения',
    FALSE, NULL, NULL
);
