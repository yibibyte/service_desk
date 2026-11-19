<<<<<<< HEAD
# service_desk
Сhampionship_ServiceDesk_
=======
# Учёт оборудования и заявок на обслуживание

Сквозной проект: PostgreSQL + FastAPI (бэкенд, REST API, JWT/RBAC),
NiceGUI (веб-клиент), PyQt6 + Qt Designer (десктоп), Flutter (мобильный клиент).

## Быстрый старт

### 1. База данных (Postgres)
```bash
createdb service_desk
psql -d service_desk -f db/init.sql
```
Либо не создавайте таблицы вручную: SQLAlchemy создаст их при старте
(lifespan в main.py). Для оценки по критериям ограничений (CHECK/UNIQUE/
RESTRICT/CASCADE) БД создаётся именно скриптом db/init.sql.

### 2. Бэкенд (FastAPI)
```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/service_desk
uvicorn backend.main:app --reload --port 8000
python -m backend.seed   # тестовые данные: admin/admin, master/master, user/user
```
Swagger: http://localhost:8000/docs

### 3. Веб-клиент (NiceGUI)
```bash
cd web
pip install -r requirements.txt
python app.py   # http://localhost:8080
```

### 4. Десктоп-клиент (PyQt6, вёрстка в Qt Designer)
```bash
cd desktop
pip install -r requirements.txt
python main.py
```
UI-файл ui/main_window.ui открыт в Qt Designer: там меняется вёрстка
(таблицы, кнопки, фильтр по статусу), логика — в main.py.

### 5. Мобильный клиент (Flutter)
```bash
cd mobile
flutter pub get
flutter run
```
Адрес API для Android-эмулятора — 10.0.2.2, для iOS-симулятора — 127.0.0.1
(поменять константу в lib/api.dart).

## Соответствие критериям
- UNIQUE: inventory_number, request_number, email, phone
- CHECK: хронология дат (эксплуатация/работа/списание, план/факт заявки),
  перечни статусов, приоритетов, ролей, положительные количества
- RESTRICT: оборудование и материал защищены от удаления при связанных данных
- CASCADE: строки списанных материалов удаляются вместе с заявкой
- Аутентификация: JWT, роли: администратор / мастер / сотрудник
>>>>>>> master
