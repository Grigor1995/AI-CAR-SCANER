"""Native editors for the common backend profile/input/report contracts."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QPlainTextEdit, QFileDialog, QMessageBox, QLabel
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
    if not app.session:
        app.show_error(tr(app, 'Open a diagnostic session first.', 'Сначала откройте диагностический сеанс.', 'Նախ բացեք ախտորոշման սեսիա։'))
        return
    sid = app.session.session_id
    dialog = QDialog(app); dialog.resize(660, 460)
    dialog.setWindowTitle(tr(app, 'Symptoms / DTC editor', 'Редактор симптомов / DTC', 'Ախտանիշների / DTC խմբագրում'))
    layout = QVBoxLayout(dialog); rows = QListWidget(); layout.addWidget(rows)
    text = QPlainTextEdit(); layout.addWidget(text)
    status = QLabel(); status.setWordWrap(True); status.setObjectName('inputEditorStatus'); layout.addWidget(status)
    bar = QHBoxLayout(); layout.addLayout(bar)
    save_label = tr(app, 'Save and analyze', 'Сохранить и анализировать', 'Պահպանել և վերլուծել')
    save_button = QPushButton(save_label); bar.addWidget(save_button)
    delete_button = QPushButton(tr(app, 'Delete', 'Удалить', 'Ջնջել')); bar.addWidget(delete_button)
    busy = False

    def active():
        return app.session is not None and app.session.session_id == sid

    def controls():
        selected = rows.currentItem() is not None
        rows.setEnabled(not busy); text.setEnabled(selected and not busy and active())
        save_button.setEnabled(selected and bool(text.toPlainText().strip()) and not busy and active())
        delete_button.setEnabled(selected and not busy and active())
        save_button.setText(tr(app, 'Saving and analyzing…', 'Сохранение и анализ…', 'Պահպանում և վերլուծություն…') if busy else save_label)

    def selection():
        item = rows.currentItem()
        text.setPlainText(item.text() if item else '')
        controls()

    def load(data):
        previous = rows.currentItem()
        selected = previous.data(Qt.UserRole) if previous else None
        previous_row = rows.currentRow()
        rows.blockSignals(True)
        try:
            rows.clear()
            for kind, key in [('symptom', 'symptoms'), ('dtc', 'dtcs')]:
                for entry in data.get(key, []):
                    item = QListWidgetItem(entry.get('raw_text') or entry.get('code') or '—')
                    item.setData(Qt.UserRole, (kind, entry['id']))
                    item.setData(Qt.UserRole + 1, dict(entry))
                    rows.addItem(item)
            index = next((i for i in range(rows.count()) if rows.item(i).data(Qt.UserRole) == selected), None)
            if rows.count(): rows.setCurrentRow(index if index is not None else max(0, min(previous_row, rows.count()-1)))
        finally:
            rows.blockSignals(False)
        selection()

    rows.itemSelectionChanged.connect(selection)
    text.textChanged.connect(controls)

    def failed(message):
        nonlocal busy
        busy = False
        status.setText(tr(app, 'Save failed: ', 'Не удалось сохранить: ', 'Պահպանումը ձախողվեց․ ') + str(message).replace(sid, "[internal]"))
        controls()

    def mutate(delete=False):
        nonlocal busy
        if busy: return
        if not active():
            status.setText(tr(app, 'The active session changed. Reopen this editor.', 'Активный сеанс изменился. Откройте редактор заново.', 'Ակտիվ սեսիան փոխվել է։ Վերաբացեք խմբագրիչը։'))
            controls(); return
        item = rows.currentItem()
        if item is None:
            status.setText(tr(app, 'Select a recorded symptom or DTC.', 'Выберите записанный симптом или DTC.', 'Ընտրեք գրանցված ախտանիշը կամ DTC-ն։')); return
        value = text.toPlainText().strip()
        if not delete and not value:
            status.setText(tr(app, 'Enter a nonempty value.', 'Введите непустое значение.', 'Մուտքագրեք ոչ դատարկ արժեք։')); return
        if delete and QMessageBox.question(dialog, dialog.windowTitle(), tr(app, 'Delete selected input?', 'Удалить выбранную запись?', 'Ջնջե՞լ ընտրված գրառումը։'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
        kind, item_id = item.data(Qt.UserRole)
        original = item.data(Qt.UserRole + 1) or {}
        language = app.language
        busy = True; controls()
        status.setText(tr(app, 'Saving and analyzing…', 'Сохранение и анализ…', 'Պահպանում և վերլուծություն…'))

        def work():
            if kind == 'symptom':
                saved = app.api.delete_symptom(sid, item_id) if delete else app.api.update_symptom(sid, item_id, value)
            elif delete:
                saved = app.api.delete_dtc(sid, item_id)
            else:
                metadata = {key: original[key] for key in ('description', 'source') if key in original}
                saved = app.api.update_dtc(sid, item_id, value, **metadata)
            # Saving and analysis are distinct server operations. Never report a
            # completed save as lost if subsequent analysis/plan refresh fails.
            try:
                analyzed = app.api.analyze(sid, language)
            except Exception as error:
                return {'session': saved, 'analysis_error': str(error)}
            try:
                decision = app.api.decision_plan(sid, language=language)
            except Exception:
                decision = {'candidates': analyzed.get('recommendations', [])}
            return {'session': analyzed, 'decision': decision}

        def done(result):
            nonlocal busy
            try:
                if not active():
                    status.setText(tr(app, 'The active session changed. Reopen this editor.', 'Активный сеанс изменился. Откройте редактор заново.', 'Ակտիվ սեսիան փոխվել է։ Վերաբացեք խմբագրիչը։')); return
                data = result['session']
                app.session_json = data
                app.session.state = data.get('state', app.session.state)
                app.decision = result.get('decision', {})
                load(data); app.refresh_pages()
                if result.get('analysis_error'):
                    message = tr(app, 'Saved; analysis failed. Retry Save and analyze: ', 'Сохранено; анализ не завершён. Повторите сохранение и анализ: ', 'Պահպանված է․ վերլուծությունը ձախողվել է։ Կրկին փորձեք․ ') + result['analysis_error'].replace(sid, '[internal]')
                else:
                    message = tr(app, 'Saved and analyzed. Diagnosis and recommended tests updated.', 'Сохранено и проанализировано. Диагноз и рекомендуемые тесты обновлены.', 'Պահպանված և վերլուծված է։ Ախտորոշումն ու առաջարկվող թեստերը թարմացվել են։')
                status.setText(message)
                app.statusBar().showMessage(message)
            finally:
                busy = False; controls()

        app.run_worker(work, done, failed)

    save_button.clicked.connect(lambda: mutate())
    delete_button.clicked.connect(lambda: mutate(True))
    load(app.session_json)
    if not rows.count():
        status.setText(tr(app, 'No recorded inputs. Add a symptom or DTC on the Symptoms page first.', 'Записей нет. Сначала добавьте симптом или DTC на странице симптомов.', 'Գրանցումներ չկան։ Նախ ախտանիշների էջում ավելացրեք ախտանիշ կամ DTC։'))
    dialog.exec()


def export_backend_report(app, format):
    if not app.session: return
    path, _ = QFileDialog.getSaveFileName(app, tr(app, 'Export report', 'Экспорт отчёта', 'Արտահանել հաշվետվություն'), f'diagnostic-report.{format}', f'{format.upper()} (*.{format})')
    if not path: return
    sid, language = app.session.session_id, app.language
    def done(data):
        try: Path(path).write_bytes(data)
        except OSError as error: app.show_error(str(error))
    app.run_worker(lambda: app.api.download_report(sid, format, language), done)
