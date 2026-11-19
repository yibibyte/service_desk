import sys

import requests
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)


API = 'http://127.0.0.1:8000/api'
UI_FILE = 'ui/main_window.ui'

TOKEN = ''
HEADERS = {}
EQUIPMENT_STATUSES = ['', 'в работе', 'в ремонте', 'в простое',
                      'выведено из эксплуатации']


def api_get(path, params=None):
    r = requests.get(API + path, headers=HEADERS, params=params, timeout=5)
    if r.status_code == 401:
        raise ConnectionError('Требуется авторизация')
    r.raise_for_status()
    return r.json()


def api_post(path, payload):
    r = requests.post(API + path, headers=HEADERS, json=payload, timeout=5)
    if r.status_code >= 400:
        raise RuntimeError(r.json().get('detail', 'Ошибка запроса'))
    return r.json() if r.text else None


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Вход в систему')
        form = QFormLayout(self)
        self.login = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow('Логин:', self.login)
        form.addRow('Пароль:', self.password)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def result_login(self):
        return self.login.text(), self.password.text()


class RequestDialog(QDialog):
    def __init__(self, equipment):
        super().__init__()
        self.setWindowTitle('Новая заявка')
        form = QFormLayout(self)
        self.equipment = QComboBox()
        for e in equipment:
            self.equipment.addItem(f"{e['inventory_number']} — {e['name']}", e['id'])
        self.priority = QComboBox()
        self.priority.addItems(['низкий', 'средний', 'высокий', 'критический'])
        self.planned_start = QLineEdit()
        self.planned_start.setPlaceholderText('ГГГГ-ММ-ДД')
        self.planned_end = QLineEdit()
        self.planned_end.setPlaceholderText('ГГГГ-ММ-ДД')
        self.description = QLineEdit()
        form.addRow('Оборудование:', self.equipment)
        form.addRow('Приоритет:', self.priority)
        form.addRow('План. начало:', self.planned_start)
        form.addRow('План. окончание:', self.planned_end)
        form.addRow('Описание:', self.description)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def payload(self):
        return {
            'equipment_id': self.equipment.currentData(),
            'priority': self.priority.currentText(),
            'planned_start': self.planned_start.text(),
            'planned_end': self.planned_end.text(),
            'description': self.description.text(),
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self)
        self.btnRefresh.setText('Обновить')
        self.btnNewRequest.setText('Создать заявку')
        self.btnCompleteTo.setText('Отметить ТО выполненным')
        self.statusFilter.addItems(EQUIPMENT_STATUSES)
        self.statusFilter.currentTextChanged.connect(self.load_equipment)
        self.btnRefresh.clicked.connect(self.load_all)
        self.btnNewRequest.clicked.connect(self.new_request)
        self.btnCompleteTo.clicked.connect(self.complete_to)
        self.load_all()

    def load_all(self):
        self.load_equipment()
        self.load_requests()
        self.load_maintenance()

    def fill_table(self, table, headers, rows):
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(0)
        for row in rows:
            i = table.rowCount()
            table.insertRow(i)
            for j, value in enumerate(row):
                table.setItem(i, j, None) if False else table.setItem(
                    i, j, __import__('PyQt6.QtWidgets', fromlist=['QTableWidgetItem'])
                    .QTableWidgetItem(str(value)))

    def load_equipment(self):
        try:
            params = {'status': self.statusFilter.currentText() or None}
            items = api_get('/equipment/', params=params)
        except Exception as e:
            self.statusbar.showMessage(f'Ошибка: {e}')
            return
        self.fill_table(self.tblEquipment,
                        ['Инв. №', 'Наименование', 'Модель', 'Место', 'Статус'],
                        [(e['inventory_number'], e['name'], e['model'] or '',
                          e['location'] or '', e['status']) for e in items])
        self.statusbar.showMessage(f'Оборудование: {len(items)} записей')

    def load_requests(self):
        try:
            items = api_get('/requests/')
        except Exception:
            return
        self.fill_table(self.tblRequests,
                        ['Номер', 'Описание', 'Приоритет', 'Статус',
                         'План. начало', 'План. конец'],
                        [(r['request_number'], r['description'][:60], r['priority'],
                          r['status'], r['planned_start'], r['planned_end'])
                         for r in items])

    def load_maintenance(self):
        try:
            items = api_get('/maintenance/')
        except Exception:
            return
        self.fill_table(self.tblMaintenance,
                        ['Оборудование (id)', 'Плановая дата', 'Описание', 'Выполнено'],
                        [(m['equipment_id'], m['planned_date'], m['description'],
                          'да' if m['performed'] else 'нет') for m in items])

    def new_request(self):
        try:
            equipment = api_get('/equipment/')
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', str(e))
            return
        dlg = RequestDialog(equipment)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api_post('/requests/', dlg.payload())
                self.load_requests()
            except Exception as e:
                QMessageBox.warning(self, 'Ошибка', str(e))

    def complete_to(self):
        row = self.tblMaintenance.currentRow()
        if row < 0:
            QMessageBox.information(self, 'ТО', 'Выберите запись в таблице')
            return
        item_id = self.tblMaintenance.item(row, 0)
        QMessageBox.information(self, 'ТО', 'Завершение ТО доступно через API/веб-клиент '
                                f'(id записи: {item_id.text() if item_id else "?"})')


def main():
    global TOKEN, HEADERS
    qapp = QApplication(sys.argv)
    while True:
        dlg = LoginDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        login, password = dlg.result_login()
        try:
            r = requests.post(API + '/auth/login',
                              json={'login': login, 'password': password}, timeout=5)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            err_text = getattr(e.response, 'text', str(e)) if hasattr(e, 'response') else str(e)
            QMessageBox.warning(None, 'Ошибка', f'Детали: {err_text}')
            continue

        TOKEN = data['access_token']
        HEADERS = {'Authorization': f'Bearer {TOKEN}'}
        break
    window = MainWindow()
    window.showMaximized()
    sys.exit(qapp.exec())


if __name__ == '__main__':
    main()
