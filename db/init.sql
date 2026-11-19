-- ============================================================
-- Учет оборудования и заявок на обслуживание (СУБД: PostgreSQL)
-- Ограничения целостности: UNIQUE / CHECK / RESTRICT / CASCADE
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    login         VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    full_name     VARCHAR(120) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    phone         VARCHAR(20)  NOT NULL UNIQUE,
    role          VARCHAR(20)  NOT NULL
        CHECK (role IN ('администратор', 'мастер', 'сотрудник'))
);

CREATE TABLE IF NOT EXISTS equipment (
    id                 SERIAL PRIMARY KEY,
    inventory_number   VARCHAR(20)  NOT NULL UNIQUE,
    name               VARCHAR(150) NOT NULL,
    model              VARCHAR(100),
    location           VARCHAR(150),
    status             VARCHAR(40)  NOT NULL DEFAULT 'в работе'
        CHECK (status IN ('в работе', 'в ремонте', 'в простое', 'выведено из эксплуатации')),
    commissioning_date DATE NOT NULL,                    -- ввод в эксплуатацию
    work_start_date    DATE,                             -- ввод в работу
    decommission_date  DATE,                             -- списание
    CHECK (work_start_date IS NULL OR work_start_date >= commissioning_date),
    CHECK (work_start_date IS NULL OR work_start_date <= CURRENT_DATE),
    CHECK (decommission_date IS NULL OR decommission_date > commissioning_date)
);

CREATE TABLE IF NOT EXISTS service_requests (
    id             SERIAL PRIMARY KEY,
    request_number VARCHAR(20)  NOT NULL UNIQUE,
    equipment_id   INTEGER      NOT NULL
        REFERENCES equipment(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    author_id      INTEGER      NOT NULL REFERENCES users(id),
    assignee_id    INTEGER      REFERENCES users(id),
    description    TEXT         NOT NULL,
    priority       VARCHAR(15)  NOT NULL DEFAULT 'средний'
        CHECK (priority IN ('низкий', 'средний', 'высокий', 'критический')),
    status         VARCHAR(25)  NOT NULL DEFAULT 'создана'
        CHECK (status IN ('создана', 'назначена', 'в работе',
                          'ожидает материалов', 'выполнена', 'закрыта', 'отменена')),
    created_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    planned_start  DATE NOT NULL,
    planned_end    DATE NOT NULL,
    actual_start   DATE,
    actual_end     DATE,
    CHECK (created_date <= planned_start AND planned_start < planned_end),
    CHECK (actual_start IS NULL OR actual_start >= created_date),
    CHECK (actual_end IS NULL OR (actual_start IS NOT NULL AND actual_start < actual_end))
);

CREATE TABLE IF NOT EXISTS materials (
    id        SERIAL PRIMARY KEY,
    name      VARCHAR(150)   NOT NULL,
    unit      VARCHAR(20)    NOT NULL DEFAULT 'шт.',
    price     NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    stock_qty NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (stock_qty >= 0)
);

CREATE TABLE IF NOT EXISTS request_materials (
    id          SERIAL PRIMARY KEY,
    request_id  INTEGER        NOT NULL
        REFERENCES service_requests(id) ON DELETE CASCADE ON UPDATE CASCADE,
    material_id INTEGER        NOT NULL
        REFERENCES materials(id) ON DELETE RESTRICT,
    qty         NUMERIC(10, 2) NOT NULL CHECK (qty > 0)
);

CREATE TABLE IF NOT EXISTS maintenance_schedule (
    id             SERIAL PRIMARY KEY,
    equipment_id   INTEGER      NOT NULL
        REFERENCES equipment(id) ON DELETE RESTRICT,
    planned_date   DATE         NOT NULL,
    description    VARCHAR(300) NOT NULL,
    performed      BOOLEAN      NOT NULL DEFAULT FALSE,
    performed_date DATE,
    performer_id   INTEGER      REFERENCES users(id),
    CHECK (performed_date IS NULL OR performed_date >= planned_date)
);

CREATE INDEX IF NOT EXISTS ix_requests_status   ON service_requests(status);
CREATE INDEX IF NOT EXISTS ix_requests_equipment ON service_requests(equipment_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_equipment ON maintenance_schedule(equipment_id);
