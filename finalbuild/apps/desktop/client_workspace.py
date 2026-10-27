"""Native editors for the common backend profile/input/report contracts."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QPlainTextEdit, QFileDialog, QMessageBox
from .models import Vehicle


def tr(app, en, ru, hy):
    return {'hy': hy, 'ru': ru}.get(getattr(app, 'language', 'en'), en)


def shared_vehicles(app):
    dialog = QDialog(app)
    dialog.setWindowTitle(tr(app, 'Shared vehicles', 'Общие автомобили', 'Ընդհանուր մեքենաներ'))
    dialog.resize(620, 440)
    layout = QVBoxLayout(dialog)
    rows = QListWidget(); layout.addWidget(rows)
    bar = QHBoxLayout(); layout.addLayout(bar)
    def loaded(profiles):
        rows.clear()
        for profile in profiles:
            vehicle = profile['vehicle']
            item = QListWidgetItem(f"{vehicle['make']} {vehicle['model']} ({vehicle.get('year') or '—'})")
            item.setData(Qt.UserRole, profile); rows.addItem(item)
    def refresh(): app.run_worker(app.api.vehicle_profiles, loaded)
    def current():
        item = rows.currentItem()
        return item.data(Qt.UserRole) if item else None
    def save():
        vehicle = app.active_vehicle
        item = app.pages[1].list.currentItem()
        if item:
            index = item.data(Qt.UserRole)
            if isinstance(index, int) and 0 <= index < len(app.vehicles): vehicle = app.vehicles[index]
        if vehicle: app.run_worker(lambda: app.api.save_vehicle_profile(vehicle.to_json()), lambda _: refresh())
    def edit():
        profile = current()
        if not profile: return
        from .ui import VehicleDialog
        editor = VehicleDialog(app)
        editor.set_vehicle(Vehicle.from_json(profile['vehicle']))
        try:
            if editor.exec() == QDialog.Accepted:
                vehicle = editor.vehicle().to_json()
                app.run_worker(lambda: app.api.save_vehicle_profile(vehicle, profile['id'], profile.get('name', '')), lambda _: refresh())
        finally:
            editor.deleteLater()
    def remove():
        profile = current()
        if profile and QMessageBox.question(dialog, dialog.windowTitle(), tr(app, 'Delete selected shared vehicle?', 'Удалить выбранный общий автомобиль?', 'Ջնջե՞լ ընտրված ընդհանուր մեքենան։'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            app.run_worker(lambda: app.api.delete_vehicle_profile(profile['id']), lambda _: refresh())
    def use():
        profile = current()
        if not profile: return
        vehicle = Vehicle.from_json(profile['vehicle']); app.active_vehicle = vehicle
        if vehicle not in app.vehicles: app.vehicles.append(vehicle); app.store.save(app.vehicles)
        dialog.accept(); app.new_session()
    for labels, action in [
        (('Refresh', 'Обновить', 'Թարմացնել'), refresh),
        (('Save current', 'Сохранить текущий', 'Պահպանել ընթացիկը'), save),
        (('Edit', 'Изменить', 'Խմբագրել'), edit),
        (('Delete', 'Удалить', 'Ջնջել'), remove),
        (('Use', 'Выбрать', 'Ընտրել'), use),
    ]:
        button = QPushButton(tr(app, *labels)); button.clicked.connect(action); bar.addWidget(button)
    refresh(); dialog.exec()


def edit_inputs(app):
    if not app.session: return
    sid = app.session.session_id
    dialog = QDialog(app); dialog.resize(660, 460)
    dialog.setWindowTitle(tr(app, 'Symptoms / DTC editor', 'Редактор симптомов / DTC', 'Ախտանիշների / DTC խմբագրում'))
    layout = QVBoxLayout(dialog); rows = QListWidget(); layout.addWidget(rows)
    text = QPlainTextEdit(); layout.addWidget(text)
    def load(data):
        rows.clear()
        for kind, key in [('symptom', 'symptoms'), ('dtc', 'dtcs')]:
            for entry in data.get(key, []):
                item = QListWidgetItem(entry.get('raw_text') or entry.get('code') or '—')
                item.setData(Qt.UserRole, (kind, entry['id'])); rows.addItem(item)
    def selection():
        item = rows.currentItem()
        text.setPlainText(item.text() if item else '')
    rows.itemSelectionChanged.connect(selection)
    def mutate(delete=False):
        item = rows.currentItem()
        if not item or (not delete and not text.toPlainText().strip()): return
        if delete and QMessageBox.question(dialog, dialog.windowTitle(), tr(app, 'Delete selected input?', 'Удалить выбранную запись?', 'Ջնջե՞լ ընտրված գրառումը։'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
        kind, item_id = item.data(Qt.UserRole); value = text.toPlainText().strip()
        def work():
            if kind == 'symptom':
                if delete: app.api.delete_symptom(sid, item_id)
                else: app.api.update_symptom(sid, item_id, value)
            else:
                if delete: app.api.delete_dtc(sid, item_id)
                else: app.api.update_dtc(sid, item_id, value)
            return app.api.analyze(sid, app.language)
        def done(data):
            load(data)
            if app.session and app.session.session_id == sid:
                app.session_json = data; app.refresh_pages()
        app.run_worker(work, done)
    bar = QHBoxLayout(); layout.addLayout(bar)
    for labels, action in [(('Save and analyze', 'Сохранить и анализировать', 'Պահպանել և վերլուծել'), lambda: mutate()), (('Delete', 'Удалить', 'Ջնջել'), lambda: mutate(True))]:
        button = QPushButton(tr(app, *labels)); button.clicked.connect(action); bar.addWidget(button)
    load(app.session_json); dialog.exec()


def export_backend_report(app, format):
    if not app.session: return
    path, _ = QFileDialog.getSaveFileName(app, tr(app, 'Export report', 'Экспорт отчёта', 'Արտահանել հաշվետվություն'), f'diagnostic-report.{format}', f'{format.upper()} (*.{format})')
    if not path: return
    sid, language = app.session.session_id, app.language
    def done(data):
        try: Path(path).write_bytes(data)
        except OSError as error: app.show_error(str(error))
    app.run_worker(lambda: app.api.download_report(sid, format, language), done)
