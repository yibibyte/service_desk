import requests as http
from nicegui import app, ui

API = 'http://localhost:8000/api'
STATUSES = ['в работе', 'в ремонте', 'в простое', 'выведено из эксплуатации']
REQ_STATUSES = ['создана', 'назначена', 'в работе', 'ожидает материалов',
                'выполнена', 'закрыта', 'отменена']


def api(path, method='GET', **kw):
    token = app.storage.user.get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    r = http.request(method, API + path, headers=headers, timeout=5, **kw)
    if r.status_code == 401 and path != '/auth/login':
        ui.navigate.to('/login')
        return []
    r.raise_for_status()
    return r.json() if r.text else []


def logout():
    app.storage.user.pop('token', None)
    app.storage.user.pop('name', None)
    ui.navigate.to('/login')


# --------------------------------- Логин ---------------------------------

@ui.page('/login')
def login_page():
    def do_login():
        try:
            data = api('/auth/login', 'POST',
                       json={'login': login_input.value, 'password': pwd.value})
        except Exception:
            ui.notify('Сервер недоступен', type='negative')
            return
        app.storage.user['token'] = data['access_token']
        app.storage.user['name'] = data['full_name']
        app.storage.user['role'] = data['role']
        ui.navigate.to('/')
    with ui.card().classes('absolute-center'):
        ui.label('Система учёта оборудования').classes('text-h6')
        login_input = ui.input('Логин').props('outlined')
        pwd = ui.input('Пароль', password=True, password_toggle_button=True).props('outlined')
        ui.button('Войти', on_click=do_login).classes('w-full')
    ui.timer(0.1, lambda: None, once=True)


# ------------------------------ Главная страница ------------------------------

def equipment_tab():
    columns = [
        {'name': 'inv', 'label': 'Инв. номер', 'field': 'inventory_number', 'align': 'left'},
        {'name': 'name', 'label': 'Наименование', 'field': 'name', 'align': 'left'},
        {'name': 'loc', 'label': 'Место', 'field': 'location', 'align': 'left'},
        {'name': 'st', 'label': 'Статус', 'field': 'status', 'align': 'left'},
    ]
    table = ui.table(columns=columns, rows=api('/equipment/'),
                     row_key='id').classes('w-full')
    status_filter = ui.select(STATUSES, value=None, label='Фильтр по статусу', clearable=True)

    def refresh():
        table.rows = api('/equipment/', params={'status': status_filter.value} if status_filter.value else None)
        table.update()
    status_filter.on('update:modelValue', lambda: refresh())
    ui.button('Обновить', on_click=refresh).props('outline')


def requests_tab():
    columns = [
        {'name': 'num', 'label': 'Номер', 'field': 'request_number', 'align': 'left'},
        {'name': 'desc', 'label': 'Описание', 'field': 'description', 'align': 'left'},
        {'name': 'pr', 'label': 'Приоритет', 'field': 'priority', 'align': 'left'},
        {'name': 'st', 'label': 'Статус', 'field': 'status', 'align': 'left'},
        {'name': 'ps', 'label': 'План. начало', 'field': 'planned_start', 'align': 'left'},
    ]
    table = ui.table(columns=columns, rows=api('/requests/'),
                     row_key='id').classes('w-full')
    equipment_options = {e['id']: f"{e['inventory_number']} — {e['name']}"
                         for e in api('/equipment/')}
    with ui.dialog() as dialog, ui.card():
        eq_sel = ui.select(equipment_options, label='Оборудование').props('outlined')
        desc = ui.textarea('Описание неисправности').props('outlined')
        prio = ui.select(['низкий', 'средний', 'высокий', 'критический'],
                         value='средний', label='Приоритет').props('outlined')
        p_start = ui.date_input('Плановое начало')
        p_end = ui.date_input('Плановое окончание')

        def save():
            try:
                api('/requests/', 'POST', json={
                    'equipment_id': eq_sel.value,
                    'description': desc.value,
                    'priority': prio.value,
                    'planned_start': str(p_start.value),
                    'planned_end': str(p_end.value),
                })
                dialog.close()
                ui.notify('Заявка создана', type='positive')
                table.rows = api('/requests/')
                table.update()
            except Exception as e:
                ui.notify(f'Ошибка: {e}', type='negative')
        ui.button('Создать', on_click=save)
    ui.button('Новая заявка', on_click=dialog.open).props('positive')
    ui.button('Обновить', on_click=lambda: (setattr(table, 'rows', api('/requests/')),
                                            table.update())).props('outline')


def maintenance_tab():
    columns = [
        {'name': 'eq', 'label': 'Оборудование', 'field': 'equipment_id', 'align': 'left'},
        {'name': 'pd', 'label': 'Плановая дата', 'field': 'planned_date', 'align': 'left'},
        {'name': 'desc', 'label': 'Описание', 'field': 'description', 'align': 'left'},
        {'name': 'done', 'label': 'Выполнено', 'field': 'performed', 'align': 'left'},
    ]
    ui.table(columns=columns, rows=api('/maintenance/'), row_key='id').classes('w-full')


def dashboard_tab():
    s = api('/reports/summary')
    with ui.row():
        ui.label(f"Оборудования всего: {s['total_equipment']}").classes('text-xl')
        ui.label(f"В ремонте: {s['equipment_in_repair']}").classes('text-xl')
        ui.label(f"Ожидают ТО: {s['pending_maintenance']}").classes('text-xl')
    ui.label('Заявки по статусам:').classes('text-h6')
    for st, cnt in s['requests_by_status'].items():
        ui.label(f'{st}: {cnt}')


@ui.page('/')
def main_page():
    if not app.storage.user.get('token'):
        ui.navigate.to('/login')
        return
    with ui.header().classes('items-center justify-between bg-blue-800'):
        ui.label('Учёт оборудования').classes('text-h6')
        with ui.row():
            ui.label(f"{app.storage.user.get('name', '')} "
                     f"({app.storage.user.get('role', '')})")
            ui.button(icon='logout', on_click=logout).props('flat')
    with ui.tabs().classes('w-full') as tabs:
        t1 = ui.tab('Сводка')
        t2 = ui.tab('Оборудование')
        t3 = ui.tab('Заявки')
        t4 = ui.tab('График ТО')
    with ui.tab_panels(tabs, value=t1).classes('w-full'):
        with ui.tab_panel(t1):
            dashboard_tab()
        with ui.tab_panel(t2):
            equipment_tab()
        with ui.tab_panel(t3):
            requests_tab()
        with ui.tab_panel(t4):
            maintenance_tab()


ui.run(title='Учёт оборудования', storage_secret='change-me', port=8081)
