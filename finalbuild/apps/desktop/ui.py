from __future__ import annotations
from pathlib import Path
import json
import re
import sys
from typing import Any, Callable
from PySide6.QtCore import Qt, QThread, Signal, QRectF, QTimer, QSettings
from PySide6.QtGui import QAction, QColor, QPainter, QPen, QBrush, QIcon
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QProgressBar,
    QScrollArea, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget, QSplitter
)
from .api_client import DiagnosticApiClient, ApiError
from .models import Vehicle, Session, TestCandidate
from .storage import VehicleStore

APP_QSS = """
QMainWindow, QWidget { background: #0b0f14; color: #e9eef5; font-family: Segoe UI, Arial; }
QFrame, QGroupBox { background: #111720; border: 1px solid #202a36; border-radius: 10px; }
QGroupBox { margin-top: 12px; padding: 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #a9b8c8; }
QPushButton { background: #1c2a39; border: 1px solid #304155; border-radius: 8px; padding: 9px 14px; }
QPushButton:hover { background: #24374a; }
QPushButton:pressed { background: #172330; }
QPushButton#primary { border: 1px solid #4d8fd4; background: #173b5d; font-weight: 700; }
QLineEdit, QPlainTextEdit, QSpinBox, QComboBox { background: #0f141c; border: 1px solid #263243; border-radius: 7px; padding: 8px; }
QListWidget { background: #0f141c; border: 0; }
QListWidget::item { padding: 11px; border-radius: 6px; }
QListWidget::item:selected { background: #1e3348; }
QHeaderView::section, QTableWidget { background: #0f141c; color: #d9e3ee; border: 1px solid #263243; }
QTableWidget { gridline-color: #202a36; }
QProgressBar { background: #0f141c; border: 1px solid #263243; border-radius: 6px; height: 10px; }
QProgressBar::chunk { background: #5595d9; border-radius: 6px; }
QLabel#title { font-size: 22px; font-weight: 700; }
QLabel#muted { color: #8e9bab; }
QLabel#ok { color: #6ed0a4; font-weight: 600; }
QLabel#warn { color: #e6be6c; font-weight: 600; }
"""

APP_QSS_LIGHT = (
    APP_QSS.replace("#0b0f14", "#f4f6f8").replace("#e9eef5", "#18212b")
    .replace("#111720", "#ffffff").replace("#202a36", "#d9e0e7")
    .replace("#a9b8c8", "#526170").replace("#1c2a39", "#e6edf3")
    .replace("#304155", "#c6d0da").replace("#24374a", "#d8e3ec")
    .replace("#172330", "#edf1f5").replace("#173b5d", "#d7eaff")
    .replace("#0f141c", "#ffffff").replace("#263243", "#c6d0da")
    .replace("#1e3348", "#d7eaff").replace("#d9e3ee", "#18212b")
    .replace("#5595d9", "#3978b8").replace("#8e9bab", "#526170")
)


_UI_TRANSLATIONS = {
    "ru": {
        "AI Auto Diagnostic Workstation": "Рабочая станция диагностики автомобилей с ИИ", "Evidence-driven automotive diagnostics.": "Диагностика на основе доказательств.", "Settings saved": "Настройки сохранены",
        "Add Vehicle": "Добавить автомобиль", "OK": "ОК", "Make": "Марка", "Model": "Модель",
        "Chassis": "Кузов", "Year": "Год", "Engine": "Двигатель", "Fuel": "Топливо", "ECU": "ЭБУ",
        "Dashboard": "Обзор", "Vehicles": "Автомобили", "VCI / Devices": "VCI / Устройства",
        "Diagnostic": "Диагностика", "Live Data": "Текущие данные", "ECU Network": "Сеть ЭБУ", "Tests": "Тесты",
        "Backend": "Сервер", "Vehicle": "Автомобиль", "Session": "Сеанс", "ECUs": "ЭБУ",
        "Diagnostic workflow": "Процесс диагностики",
        "Evidence → Reasoning → Next Test → Result → Re-analysis": "Данные → Анализ → Следующий тест → Результат → Повторный анализ",
        "LLM explains and orchestrates; deterministic rules and measured evidence remain authoritative.": "LLM объясняет и координирует; правила и измеренные данные остаются основой выводов.",
        "Refresh status": "Обновить статус", "+ Add vehicle": "+ Добавить автомобиль", "Delete selected": "Удалить выбранное",
        "No active session": "Нет активного сеанса", "New session": "Новый сеанс",
        "Describe the symptom naturally… Example: engine shakes below 2000 RPM during acceleration on LPG; petrol is normal.": "Опишите симптом. Пример: двигатель трясётся ниже 2000 об/мин при разгоне на LPG, на бензине работает нормально.",
        "Symptoms / observations": "Симптомы / наблюдения", "DTC": "Код неисправности (DTC)",
        "Add evidence + Analyze": "Добавить данные и анализировать", "Analysis": "Анализ", "Evidence": "Данные", "Hypotheses": "Гипотезы", "Missing info": "Недостающие данные",
        "No evidence yet.": "Пока нет данных.", "No hypotheses yet.": "Пока нет гипотез.",
        "No high-value missing information identified.": "Не выявлена критически важная недостающая информация.",
        "Session state:": "Состояние сеанса:", "Current diagnostic interpretation:": "Текущая диагностическая интерпретация:",
        "No diagnostic hypotheses generated yet.": "Диагностические гипотезы ещё не сформированы.",
        "Important: hypotheses are not confirmed component failures. Confirmation requires measured or test evidence.": "Важно: гипотезы не подтверждают неисправность детали. Подтверждение требует измерений или результатов тестов.",
        "Stopped": "Остановлено", "Start simulator": "Запустить симулятор", "Stop": "Остановить",
        "Analyze telemetry": "Анализировать телеметрию", "AI Analyze Live Data": "ИИ-анализ текущих данных",
        "PID / Channel": "PID / Канал", "Count": "Количество", "Min": "Мин.", "Max": "Макс.", "Mean": "Среднее", "Events": "События",
        "AI live-data interpretation will appear here...": "Здесь появится интерпретация текущих данных ИИ...",
        "Technician notes / measurements": "Заметки техника / измерения", "Record selected result": "Сохранить результат",
        "PASS": "Пройден", "FAIL": "Не пройден", "INCOMPLETE": "Неполно",
        "VCI / Adapter Connection": "Подключение VCI / адаптера",
        "Discover USB/BLE adapters or connect to a Wi-Fi OBD endpoint. Physical writes/programming are not exposed here.": "Найдите USB/BLE-адаптеры или подключитесь к Wi-Fi OBD. Запись и программирование блоков здесь недоступны.",
        "Scan USB": "Поиск USB", "Scan BLE": "Поиск BLE", "Add Simulator": "Добавить симулятор", "Probe Wi-Fi": "Проверить Wi-Fi",
        "Selected device": "Выбранное устройство", "Wi-Fi host": "Хост Wi-Fi", "Wi-Fi port": "Порт Wi-Fi",
        "USB baudrate": "Скорость USB", "BLE TX UUID": "UUID BLE TX", "BLE RX UUID": "UUID BLE RX",
        "Connect": "Подключить", "Disconnect": "Отключить", "Reconnect": "Переподключить",
        "Read VIN": "Считать VIN", "Read DTCs": "Считать DTC", "Read Live Data": "Считать текущие данные", "Device result": "Результат устройства",
        "Refresh network map": "Обновить карту сети", "Active read-only probe": "Активная проверка (только чтение)",
        "PASSIVE / INFERRED NETWORK": "ПАССИВНАЯ / ПРЕДПОЛАГАЕМАЯ СЕТЬ", "ACTIVE CORRELATION": "АКТИВНАЯ КОРРЕЛЯЦИЯ",
        "No discovered ECU candidates yet.": "Кандидаты ЭБУ ещё не обнаружены.",
        "Application": "Приложение", "Settings…": "Настройки…", "Exit": "Выход", "Help": "Справка", "About": "О программе",
        "Application settings": "Настройки приложения", "Language": "Язык", "Theme": "Тема", "Dark": "Тёмная", "Light": "Светлая",
        "Save": "Сохранить", "Cancel": "Отмена", "Ready": "Готово", "Error": "Ошибка",
        "Select a vehicle to delete.": "Выберите автомобиль для удаления.",
        "Selected vehicle is no longer available.": "Выбранный автомобиль больше недоступен.",
        "Delete vehicle": "Удалить автомобиль", "Delete": "Удалить", "from local vehicle profiles?": "из локальных профилей автомобилей?",
        "Existing diagnostic sessions are not deleted.": "Существующие диагностические сеансы не удаляются.",
        "Enter the Wi-Fi OBD adapter host, for example 192.168.0.10.": "Введите адрес Wi-Fi OBD-адаптера, например 192.168.0.10.",
        "Select a VCI/device first.": "Сначала выберите VCI/устройство.", "Device connected": "Устройство подключено",
        "Device disconnected": "Устройство отключено", "Device reconnected": "Устройство переподключено",
        "No active session.": "Нет активного сеанса.", "Select a diagnostic test first.": "Сначала выберите диагностический тест.",
        "Backend is offline. Start the FastAPI backend first.": "Сервер недоступен. Сначала запустите FastAPI backend.",
        "Enter a symptom, observation or DTC.": "Введите симптом, наблюдение или DTC.",
        "Create a diagnostic session first.": "Сначала создайте диагностический сеанс.",
        "AI is analyzing live vehicle data...": "ИИ анализирует текущие данные автомобиля...",
        "Diagnostic session created": "Диагностический сеанс создан", "Diagnostic reasoning updated": "Диагностический анализ обновлён",
        "Telemetry analysis completed": "Анализ телеметрии завершён", "Network map refreshed": "Карта сети обновлена",
        "Active read-only ECU probe completed": "Активная проверка ЭБУ завершена", "Live-data AI analysis completed": "ИИ-анализ текущих данных завершён",
        "Vehicle deleted:": "Автомобиль удалён:", "Backend online": "Сервер доступен", "Backend offline": "Сервер недоступен",
        "ONLINE": "В СЕТИ", "OFFLINE": "НЕ В СЕТИ", "RUNNING": "РАБОТАЕТ", "Unknown": "Неизвестно",
        "AI: checking...": "ИИ: проверка...", "AI: unavailable": "ИИ: недоступен", "AI: READY": "ИИ: ГОТОВ",
        "AI: OFFLINE": "ИИ: НЕ В СЕТИ", "No active session": "Нет активного сеанса", "Risk": "Риск", "Purpose": "Цель",
        "Make:": "Марка:", "Model:": "Модель:", "Chassis:": "Кузов:", "Year:": "Год:", "Engine:": "Двигатель:", "Fuel:": "Топливо:", "ECU:": "ЭБУ:",
        "ID:": "ID:", "Manufacturer:": "Производитель:", "Connection:": "Подключение:", "Protocol:": "Протокол:", "Status:": "Статус:",
        "Firmware:": "Прошивка:", "Capabilities:": "Возможности:", "Metadata:": "Метаданные:", "VIN:": "VIN:",
        "Not available": "Недоступно", "No stored generic OBD-II DTCs": "Нет сохранённых стандартных OBD-II DTC",
        "DTCs:": "Коды неисправностей:", "Provider:": "Провайдер:", "Model:": "Модель:", "Available:": "Доступен:",
        "No AI result.": "Нет результата ИИ.", "Provider error:": "Ошибка провайдера:",
        "Session": "Сеанс", "Risk": "Риск", "Purpose": "Цель",
    },
    "hy": {
        "AI Auto Diagnostic Workstation": "Ավտոմեքենաների AI ախտորոշման աշխատակայան", "Evidence-driven automotive diagnostics.": "Ապացույցների վրա հիմնված ախտորոշում։", "Settings saved": "Կարգավորումները պահպանվել են",
        "Add Vehicle": "Ավելացնել մեքենա", "OK": "Լավ", "Make": "Արտադրող", "Model": "Մոդել",
        "Chassis": "Թափք", "Year": "Տարի", "Engine": "Շարժիչ", "Fuel": "Վառելիք", "ECU": "ԷԿՀ",
        "Dashboard": "Գլխավոր", "Vehicles": "Մեքենաներ", "VCI / Devices": "VCI / Սարքեր",
        "Diagnostic": "Ախտորոշում", "Live Data": "Ընթացիկ տվյալներ", "ECU Network": "ԷԿՀ ցանց", "Tests": "Թեստեր",
        "Backend": "Սերվեր", "Vehicle": "Մեքենա", "Session": "Սեսիա", "ECUs": "ԷԿՀ-ներ",
        "Diagnostic workflow": "Ախտորոշման ընթացք",
        "Evidence → Reasoning → Next Test → Result → Re-analysis": "Տվյալներ → Վերլուծություն → Հաջորդ թեստ → Արդյունք → Կրկնակի վերլուծություն",
        "LLM explains and orchestrates; deterministic rules and measured evidence remain authoritative.": "LLM-ը բացատրում և համակարգում է, իսկ կանոններն ու չափված տվյալները մնում են հիմնական ապացույցը։",
        "Refresh status": "Թարմացնել կարգավիճակը", "+ Add vehicle": "+ Ավելացնել մեքենա", "Delete selected": "Ջնջել ընտրվածը",
        "No active session": "Ակտիվ սեսիա չկա", "New session": "Նոր սեսիա",
        "Describe the symptom naturally… Example: engine shakes below 2000 RPM during acceleration on LPG; petrol is normal.": "Նկարագրեք ախտանիշը։ Օրինակ՝ LPG-ով արագացնելիս շարժիչը դողում է 2000 RPM-ից ցածր, բենզինով՝ նորմալ։",
        "Symptoms / observations": "Ախտանիշներ / դիտարկումներ", "DTC": "Սխալի կոդ (DTC)",
        "Add evidence + Analyze": "Ավելացնել տվյալներ և վերլուծել", "Analysis": "Վերլուծություն", "Evidence": "Ապացույցներ", "Hypotheses": "Վարկածներ", "Missing info": "Բացակայող տվյալներ",
        "No evidence yet.": "Դեռ տվյալներ չկան։", "No hypotheses yet.": "Դեռ վարկածներ չկան։",
        "No high-value missing information identified.": "Կարևոր բացակայող տեղեկություն չի հայտնաբերվել։",
        "Session state:": "Սեսիայի վիճակ՝", "Current diagnostic interpretation:": "Ընթացիկ ախտորոշիչ մեկնաբանություն՝",
        "No diagnostic hypotheses generated yet.": "Ախտորոշիչ վարկածներ դեռ չեն ստեղծվել։",
        "Important: hypotheses are not confirmed component failures. Confirmation requires measured or test evidence.": "Կարևոր է․ վարկածները մասի խափանման հաստատում չեն։ Հաստատման համար անհրաժեշտ են չափումներ կամ թեստի արդյունքներ։",
        "Stopped": "Կանգնեցված է", "Start simulator": "Գործարկել սիմուլյատորը", "Stop": "Կանգնեցնել",
        "Analyze telemetry": "Վերլուծել հեռաչափությունը", "AI Analyze Live Data": "AI վերլուծել ընթացիկ տվյալները",
        "PID / Channel": "PID / ալիք", "Count": "Քանակ", "Min": "Նվազագույն", "Max": "Առավելագույն", "Mean": "Միջին", "Events": "Իրադարձություններ",
        "AI live-data interpretation will appear here...": "Այստեղ կհայտնվի ընթացիկ տվյալների AI մեկնաբանությունը...",
        "Technician notes / measurements": "Տեխնիկի նշումներ / չափումներ", "Record selected result": "Գրանցել արդյունքը",
        "PASS": "Անցավ", "FAIL": "Չանցավ", "INCOMPLETE": "Անորոշ",
        "VCI / Adapter Connection": "VCI / ադապտերի միացում",
        "Discover USB/BLE adapters or connect to a Wi-Fi OBD endpoint. Physical writes/programming are not exposed here.": "Գտեք USB/BLE ադապտերներ կամ միացեք Wi-Fi OBD-ին։ Կառավարման բլոկների գրանցումն ու ծրագրավորումն այստեղ հասանելի չեն։",
        "Scan USB": "Փնտրել USB", "Scan BLE": "Փնտրել BLE", "Add Simulator": "Ավելացնել սիմուլյատոր", "Probe Wi-Fi": "Ստուգել Wi-Fi",
        "Selected device": "Ընտրված սարք", "Wi-Fi host": "Wi-Fi հասցե", "Wi-Fi port": "Wi-Fi պորտ",
        "USB baudrate": "USB արագություն", "BLE TX UUID": "BLE TX UUID", "BLE RX UUID": "BLE RX UUID",
        "Connect": "Միացնել", "Disconnect": "Անջատել", "Reconnect": "Կրկին միացնել",
        "Read VIN": "Կարդալ VIN", "Read DTCs": "Կարդալ DTC-ները", "Read Live Data": "Կարդալ ընթացիկ տվյալները", "Device result": "Սարքի արդյունք",
        "Refresh network map": "Թարմացնել ցանցի քարտեզը", "Active read-only probe": "Ակտիվ ստուգում (միայն ընթերցում)",
        "PASSIVE / INFERRED NETWORK": "ՊԱՍԻՎ / ԵՆԹԱԴՐՎՈՂ ՑԱՆՑ", "ACTIVE CORRELATION": "ԱԿՏԻՎ ՀԱՄԱԴՐՈՒՄ",
        "No discovered ECU candidates yet.": "ԷԿՀ-ի հնարավոր թեկնածուներ դեռ չեն հայտնաբերվել։",
        "Application": "Հավելված", "Settings…": "Կարգավորումներ…", "Exit": "Ելք", "Help": "Օգնություն", "About": "Մասին",
        "Application settings": "Հավելվածի կարգավորումներ", "Language": "Լեզու", "Theme": "Թեմա", "Dark": "Մուգ", "Light": "Բաց",
        "Save": "Պահպանել", "Cancel": "Չեղարկել", "Ready": "Պատրաստ է", "Error": "Սխալ",
        "Select a vehicle to delete.": "Ընտրեք ջնջվող մեքենան։",
        "Selected vehicle is no longer available.": "Ընտրված մեքենան այլևս հասանելի չէ։",
        "Delete vehicle": "Ջնջել մեքենան", "Delete": "Ջնջել", "from local vehicle profiles?": "տեղական մեքենաների պրոֆիլներից՞",
        "Existing diagnostic sessions are not deleted.": "Գոյություն ունեցող ախտորոշիչ սեսիաները չեն ջնջվի։",
        "Enter the Wi-Fi OBD adapter host, for example 192.168.0.10.": "Մուտքագրեք Wi-Fi OBD ադապտերի հասցեն, օրինակ՝ 192.168.0.10։",
        "Select a VCI/device first.": "Նախ ընտրեք VCI/սարքը։", "Device connected": "Սարքը միացված է",
        "Device disconnected": "Սարքն անջատված է", "Device reconnected": "Սարքը կրկին միացված է",
        "No active session.": "Ակտիվ սեսիա չկա։", "Select a diagnostic test first.": "Նախ ընտրեք ախտորոշիչ թեստը։",
        "Backend is offline. Start the FastAPI backend first.": "Սերվերն անհասանելի է։ Նախ գործարկեք FastAPI backend-ը։",
        "Enter a symptom, observation or DTC.": "Մուտքագրեք ախտանիշ, դիտարկում կամ DTC։",
        "Create a diagnostic session first.": "Նախ ստեղծեք ախտորոշիչ սեսիա։",
        "AI is analyzing live vehicle data...": "AI-ն վերլուծում է մեքենայի ընթացիկ տվյալները...",
        "Diagnostic session created": "Ախտորոշիչ սեսիան ստեղծվել է", "Diagnostic reasoning updated": "Ախտորոշիչ վերլուծությունը թարմացվել է",
        "Telemetry analysis completed": "Հեռաչափության վերլուծությունն ավարտվել է", "Network map refreshed": "Ցանցի քարտեզը թարմացվել է",
        "Active read-only ECU probe completed": "ԷԿՀ-ի ակտիվ ստուգումն ավարտվել է", "Live-data AI analysis completed": "Ընթացիկ տվյալների AI վերլուծությունն ավարտվել է",
        "Vehicle deleted:": "Մեքենան ջնջվել է՝", "Backend online": "Սերվերը հասանելի է", "Backend offline": "Սերվերն անհասանելի է",
        "ONLINE": "ՀԱՍԱՆԵԼԻ", "OFFLINE": "ԱՆՀԱՍԱՆԵԼԻ", "RUNNING": "ԱՇԽԱՏՈՒՄ Է", "Unknown": "Անհայտ",
        "AI: checking...": "AI՝ ստուգվում է...", "AI: unavailable": "AI-ն հասանելի չէ", "AI: READY": "AI՝ ՊԱՏՐԱՍՏ",
        "AI: OFFLINE": "AI՝ ԱՆՀԱՍԱՆԵԼԻ", "Risk": "Ռիսկ", "Purpose": "Նպատակ",
        "Make:": "Արտադրող՝", "Model:": "Մոդել՝", "Chassis:": "Թափք՝", "Year:": "Տարի՝", "Engine:": "Շարժիչ՝", "Fuel:": "Վառելիք՝", "ECU:": "ԷԿՀ՝",
        "ID:": "ID:", "Manufacturer:": "Արտադրող՝", "Connection:": "Միացում՝", "Protocol:": "Արձանագրություն՝", "Status:": "Կարգավիճակ՝",
        "Firmware:": "Ծրագրային ապահովում՝", "Capabilities:": "Հնարավորություններ՝", "Metadata:": "Մետատվյալներ՝", "VIN:": "VIN:",
        "Not available": "Հասանելի չէ", "No stored generic OBD-II DTCs": "Պահված ստանդարտ OBD-II DTC-ներ չկան",
        "DTCs:": "Սխալի կոդեր՝", "Provider:": "Մատակարար՝", "Available:": "Հասանելի է՝",
        "No AI result.": "AI արդյունք չկա։", "Provider error:": "Մատակարարի սխալ՝",
    }
}


def _translate_ui_text(text: str, language: str) -> str:
    if not isinstance(text, str):
        return text
    # Normalize all known translations back to English first, including phrases
    # inside dynamic status messages and multiline diagnostic summaries.
    canonical = text
    for translations in _UI_TRANSLATIONS.values():
        for source, translated in sorted(translations.items(), key=lambda item: len(item[1]), reverse=True):
            canonical = re.sub(r"(?<!\w)" + re.escape(translated) + r"(?!\w)", source, canonical)
    if language == "en":
        return canonical
    translations = _UI_TRANSLATIONS.get(language, {})
    for source in sorted(translations, key=len, reverse=True):
        canonical = re.sub(r"(?<!\w)" + re.escape(source) + r"(?!\w)", translations[source], canonical)
    return canonical



def _translate_ui_block(text: str, language: str) -> str:
    """Translate UI labels/static messages without rewriting vehicle or ECU values."""
    if not isinstance(text, str):
        return text
    return "\n".join(_translate_known_ui_line(line, language) for line in text.splitlines())


def _translate_known_ui_line(line: str, language: str) -> str:
    bullet = ""
    body = line
    if body.startswith("• "):
        bullet, body = "• ", body[2:]
    all_maps = list(_UI_TRANSLATIONS.values())
    known = any(body == key or body == value for mapping in all_maps for key, value in mapping.items())
    if known:
        return bullet + _translate_ui_text(body, language)
    label_keys = (
        "Current diagnostic interpretation:", "Session state:", "Important:",
        "Manufacturer:", "Capabilities:", "Connection:", "Protocol:", "Metadata:",
        "Provider:", "Available:", "Firmware:", "Chassis:", "Engine:", "Status:",
        "DTCs:", "Make:", "Model:", "Year:", "Fuel:", "ECU:", "VIN:", "ID:",
    )
    translated = body
    # Normalize translated labels back to their English keys before applying the
    # selected language, allowing RU ↔ HY ↔ EN switching without touching values.
    for label in sorted(label_keys, key=len, reverse=True):
        for mapping in all_maps:
            localized = mapping.get(label)
            if localized and localized != label:
                translated = re.sub(r"(?<!\w)" + re.escape(localized), label, translated)
    for label in sorted(label_keys, key=len, reverse=True):
        translated = re.sub(
            r"(?<!\w)" + re.escape(label),
            _translate_ui_text(label, language),
            translated,
        )
    return bullet + translated


class Worker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)
    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__(); self.fn = fn
    def run(self) -> None:
        try: self.finished_ok.emit(self.fn())
        except Exception as exc: self.failed.emit(str(exc))

class Sparkline(QWidget):
    def __init__(self, values: list[float] | None = None) -> None:
        super().__init__(); self.values = values or []; self.setMinimumHeight(100)
    def set_values(self, values: list[float]) -> None:
        self.values = values[-120:]; self.update()
    def paintEvent(self, _event) -> None:
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(8, 8, -8, -8)
        p.fillRect(r, QBrush(QColor("#0f141c")))
        if len(self.values) < 2: return
        lo, hi = min(self.values), max(self.values)
        if hi - lo < 1e-9: hi = lo + 1
        pen = QPen(QColor("#5da9ff"), 2); p.setPen(pen)
        points = []
        for i, value in enumerate(self.values):
            x = r.left() + (r.width() * i / (len(self.values)-1))
            y = r.bottom() - r.height() * ((value-lo)/(hi-lo))
            points.append((x,y))
        for a,b in zip(points, points[1:]): p.drawLine(a[0],a[1],b[0],b[1])

class MetricCard(QGroupBox):
    def __init__(self, title: str, value: str = "—") -> None:
        super().__init__(); self.setTitle(title)
        layout = QVBoxLayout(self); self.value = QLabel(value); self.value.setObjectName("vehicleMetricValue" if title == "Vehicle" else ""); self.value.setStyleSheet("font-size:26px;font-weight:700;"); layout.addWidget(self.value)
    def set_value(self, value: str) -> None: self.value.setText(value)

class VehicleDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        language = getattr(parent, "language", "en")
        self.setWindowTitle(_translate_ui_text("Add Vehicle", language))
        self.resize(520, 440)
        self._catalog: list[dict[str, Any]] = []
        api = getattr(parent, "api", None)
        if api is not None:
            try:
                self._catalog = list(api.vehicle_catalog_entries())
            except Exception:
                self._catalog = []
        self._catalog_from_server = bool(self._catalog)

        # Keep the server catalog first (authoritative for exact matches), then
        # add the curated offline seed so selection still works when the API is
        # sparse or unavailable. The seed is broad guidance, not VIN-level fitment.
        try:
            offline_payload = json.loads(
                _resource_path("shared/vehicle_catalog.json").read_text(encoding="utf-8")
            )
            offline_rows = offline_payload.get("vehicles", [])
            if not isinstance(offline_rows, list):
                offline_rows = []
        except (OSError, ValueError, TypeError):
            offline_rows = []

        merged: dict[tuple[str, ...], dict[str, Any]] = {}
        for row in [*self._catalog, *offline_rows]:
            if not isinstance(row, dict):
                continue
            key = tuple(
                str(row.get(field, "")).strip().casefold()
                for field in ("make", "model", "chassis", "year", "engine", "ecu")
            )
            if all(key):
                merged.setdefault(key, row)
        self._catalog = list(merged.values())

        form = QFormLayout(self)
        if not self._catalog_from_server:
            language = getattr(parent, "language", "en")
            fallback_notice = {
                "ru": "Офлайн-каталог: список может отличаться от серверного каталога.",
                "hy": "Օֆլայն կատալոգ․ ցանկը կարող է տարբերվել սերվերի կատալոգից։",
            }.get(language, "Offline catalog: options may differ from the server catalog.")
            form.addRow(QLabel(fallback_notice))
        self.make = QComboBox()
        self.model = QComboBox()
        self.chassis = QComboBox()
        self.year = QComboBox()
        self.engine = QComboBox()
        self.ecu = QComboBox()
        self.fuel = QLineEdit("Petrol,LPG")

        for combo in (self.make, self.model, self.chassis, self.year, self.engine, self.ecu):
            combo.setEditable(False)

        form.addRow(_translate_ui_text("Make", language), self.make)
        form.addRow(_translate_ui_text("Model", language), self.model)
        form.addRow(_translate_ui_text("Chassis", language), self.chassis)
        form.addRow(_translate_ui_text("Year", language), self.year)
        form.addRow(_translate_ui_text("Engine", language), self.engine)
        form.addRow(_translate_ui_text("Fuel", language), self.fuel)
        form.addRow(_translate_ui_text("ECU", language), self.ecu)

        self.make.currentTextChanged.connect(self._refresh_models)
        self.model.currentTextChanged.connect(self._refresh_chassis)
        self.chassis.currentTextChanged.connect(self._refresh_years)
        self.year.currentTextChanged.connect(self._refresh_engines)
        self.engine.currentTextChanged.connect(self._refresh_ecus)

        self._refresh_makes()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(_translate_ui_text("OK", language))
        buttons.button(QDialogButtonBox.Cancel).setText(_translate_ui_text("Cancel", language))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _items(self, **filters: Any) -> list[dict[str, Any]]:
        rows = self._catalog
        for key, value in filters.items():
            if value in (None, "", "—"):
                continue
            rows = [row for row in rows if row.get(key) == value]
        return rows

    @staticmethod
    def _set_combo(combo: QComboBox, values: list[Any], selected: Any | None = None) -> None:
        combo.blockSignals(True)
        combo.clear()
        for value in values:
            combo.addItem(str(value))
        if selected is not None:
            idx = combo.findText(str(selected))
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _refresh_makes(self) -> None:
        if not self._catalog:
            self._set_combo(self.make, ["Mercedes-Benz"])
            self._set_combo(self.model, ["E-Class"])
            self._set_combo(self.chassis, ["W211"])
            self._set_combo(self.year, [2006])
            self._set_combo(self.engine, ["M272 E35 3.5"])
            self._set_combo(self.ecu, ["ME9.7"])
            return
        makes = sorted({row["make"] for row in self._catalog})
        self._set_combo(self.make, makes, "Mercedes-Benz" if "Mercedes-Benz" in makes else makes[0])
        self._refresh_models()

    def _refresh_models(self, *_args: Any) -> None:
        models = sorted({row["model"] for row in self._items(make=self.make.currentText())})
        self._set_combo(self.model, models, "E-Class" if "E-Class" in models else (models[0] if models else None))
        self._refresh_chassis()

    def _refresh_chassis(self, *_args: Any) -> None:
        rows = self._items(make=self.make.currentText(), model=self.model.currentText())
        chassis = sorted({row["chassis"] for row in rows if row.get("chassis")})
        self._set_combo(self.chassis, chassis, "W211" if "W211" in chassis else (chassis[0] if chassis else None))
        self._refresh_years()

    def _refresh_years(self, *_args: Any) -> None:
        rows = self._items(make=self.make.currentText(), model=self.model.currentText(), chassis=self.chassis.currentText())
        years = sorted({row["year"] for row in rows}, reverse=True)
        self._set_combo(self.year, years, 2006 if 2006 in years else (years[0] if years else None))
        self._refresh_engines()

    def _refresh_engines(self, *_args: Any) -> None:
        rows = self._items(
            make=self.make.currentText(),
            model=self.model.currentText(),
            chassis=self.chassis.currentText(),
            year=int(self.year.currentText()) if self.year.currentText().isdigit() else None,
        )
        engines = sorted({row["engine"] for row in rows})
        self._set_combo(self.engine, engines, "M272 E35 3.5" if "M272 E35 3.5" in engines else (engines[0] if engines else None))
        self._refresh_ecus()

    def _refresh_ecus(self, *_args: Any) -> None:
        rows = self._items(
            make=self.make.currentText(),
            model=self.model.currentText(),
            chassis=self.chassis.currentText(),
            year=int(self.year.currentText()) if self.year.currentText().isdigit() else None,
            engine=self.engine.currentText(),
        )
        ecus = sorted({row["ecu"] for row in rows if row.get("ecu")})
        self._set_combo(self.ecu, ecus, "ME9.7" if "ME9.7" in ecus else (ecus[0] if ecus else None))

    def vehicle(self) -> Vehicle:
        return Vehicle(
            self.make.currentText().strip(),
            self.model.currentText().strip(),
            self.chassis.currentText().strip(),
            int(self.year.currentText()) if self.year.currentText().isdigit() else None,
            self.engine.currentText().strip(),
            [x.strip() for x in self.fuel.text().split(",") if x.strip()],
            self.ecu.currentText().strip(),
        )

class DashboardPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); title=QLabel("AI Auto Diagnostic Workstation"); title.setObjectName("title"); lay.addWidget(title)
        cards=QGridLayout(); self.backend=MetricCard("Backend", "OFFLINE"); self.vehicle=MetricCard("Vehicle", "—"); self.session=MetricCard("Session", "—"); self.ecus=MetricCard("ECUs", "—")
        for i,c in enumerate((self.backend,self.vehicle,self.session,self.ecus)): cards.addWidget(c,0,i)
        lay.addLayout(cards)
        info=QGroupBox("Diagnostic workflow"); il=QVBoxLayout(info); il.addWidget(QLabel("Evidence → Reasoning → Next Test → Result → Re-analysis")); il.addWidget(QLabel("LLM explains and orchestrates; deterministic rules and measured evidence remain authoritative.")); lay.addWidget(info)
        self.refresh_btn=QPushButton("Refresh status"); self.refresh_btn.clicked.connect(app.refresh_all); lay.addWidget(self.refresh_btn, alignment=Qt.AlignLeft); lay.addStretch()
    def refresh(self):
        self.backend.set_value("ONLINE" if self.app.online else "OFFLINE")
        self.vehicle.set_value(f"{self.app.active_vehicle.make} {self.app.active_vehicle.model}" if self.app.active_vehicle else "—")
        self.session.set_value(self.app.session.session_id[:8] if self.app.session else "—")
        self.ecus.set_value(str(len(self.app.network.get("ecus", []))) if self.app.network else "—")

class VehiclesPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); bar=QHBoxLayout(); add=QPushButton("+ Add vehicle"); add.clicked.connect(app.add_vehicle); bar.addWidget(add); self.delete_btn=QPushButton("Delete selected"); self.delete_btn.clicked.connect(app.delete_selected_vehicle); self.delete_btn.setEnabled(False); bar.addWidget(self.delete_btn); bar.addStretch(); lay.addLayout(bar)
        split=QSplitter(); self.list=QListWidget(); self.details=QPlainTextEdit(); self.details.setObjectName("vehicleDetails"); self.details.setReadOnly(True); split.addWidget(self.list); split.addWidget(self.details); split.setSizes([360,700]); lay.addWidget(split)
        self.list.itemSelectionChanged.connect(self.show_selected)
    def refresh(self):
        self.list.clear()
        for idx,v in enumerate(self.app.vehicles):
            item=QListWidgetItem(f"{v.make} {v.model} ({v.year or '—'})"); item.setData(Qt.UserRole, idx); self.list.addItem(item)
        self.delete_btn.setEnabled(bool(self.app.vehicles))
        if self.app.active_vehicle:
            self.show_vehicle(self.app.active_vehicle)
        elif self.app.vehicles:
            self.list.setCurrentRow(0)
        else:
            self.details.clear()
    def show_selected(self):
        items=self.list.selectedItems()
        self.delete_btn.setEnabled(bool(items))
        if not items: return
        v=self.app.vehicles[items[0].data(Qt.UserRole)]; self.show_vehicle(v)
    def show_vehicle(self,v:Vehicle):
        self.details.setPlainText(f"Make: {v.make}\nModel: {v.model}\nChassis: {v.chassis or '—'}\nYear: {v.year or '—'}\nEngine: {v.engine or '—'}\nFuel: {', '.join(v.fuel) or '—'}\nECU: {v.ecu or '—'}")

class DiagnosticPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); head=QHBoxLayout(); self.lbl=QLabel("No active session"); self.lbl.setObjectName("muted"); head.addWidget(self.lbl); head.addStretch(); new=QPushButton("New session"); new.clicked.connect(app.new_session); head.addWidget(new); lay.addLayout(head)
        form=QGridLayout(); self.symptom=QPlainTextEdit(); self.symptom.setPlaceholderText("Describe the symptom naturally… Example: engine shakes below 2000 RPM during acceleration on LPG; petrol is normal."); self.symptom.setFixedHeight(120)
        self.dtc=QLineEdit(); self.dtc.setPlaceholderText("P0302"); submit=QPushButton("Add evidence + Analyze"); submit.clicked.connect(app.analyze_input)
        form.addWidget(QLabel("Symptoms / observations"),0,0); form.addWidget(self.symptom,1,0,1,2); form.addWidget(QLabel("DTC"),2,0); form.addWidget(self.dtc,2,1); form.addWidget(submit,3,0,1,2); lay.addLayout(form)
        out=QTabWidget(); self.summary=QPlainTextEdit(); self.summary.setReadOnly(True); out.addTab(self.summary,"Analysis"); self.evidence=QPlainTextEdit(); self.evidence.setReadOnly(True); self.hypotheses=QPlainTextEdit(); self.hypotheses.setReadOnly(True); self.questions=QPlainTextEdit(); self.questions.setReadOnly(True); out.addTab(self.evidence,"Evidence"); out.addTab(self.hypotheses,"Hypotheses"); out.addTab(self.questions,"Missing info"); lay.addWidget(out)
    def refresh(self):
        if not self.app.session: self.lbl.setText("No active session"); return
        self.lbl.setText(f"Session {self.app.session.session_id} • {self.app.session.state}")
        data=self.app.session_json
        ev=data.get("evidence",[]); hp=data.get("hypotheses",[])
        self.summary.setPlainText(self._summary_text(data, hp))
        self.evidence.setPlainText("\n".join(f"[{x.get('status','')}] {x.get('fact','')} — {x.get('source','')}" for x in ev) or "No evidence yet.")
        self.hypotheses.setPlainText("\n".join(f"• {x.get('category','Unknown')}: {x.get('statement','')} [{x.get('status','possible')}]" for x in hp) or "No hypotheses yet.")
        missing=self.app.decision.get("missing_questions",[])+self.app.decision.get("questions",[]); self.questions.setPlainText("\n".join(f"• {x if isinstance(x,str) else x.get('question',x)}" for x in missing) or "No high-value missing information identified.")

    @staticmethod
    def _summary_text(data, hypotheses):
        state = data.get("state", "—")
        lines = [f"Session state: {state}", "", "Current diagnostic interpretation:"]
        if hypotheses:
            lines.extend(f"• {h.get('category','Unknown')}: {h.get('statement','')}" for h in hypotheses)
        else:
            lines.append("• No diagnostic hypotheses generated yet.")
        lines += ["", "Important: hypotheses are not confirmed component failures. Confirmation requires measured or test evidence."]
        return "\n".join(lines)

class LiveDataPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); bar=QHBoxLayout(); self.status=QLabel("Stopped"); self.ai_status=QLabel("AI: checking..."); self.ai_status.setObjectName("muted"); self.start=QPushButton("Start simulator"); self.stop=QPushButton("Stop"); self.analyze=QPushButton("Analyze telemetry"); self.ai_analyze=QPushButton("AI Analyze Live Data"); self.ai_analyze.setObjectName("primary")
        self.start.clicked.connect(app.start_simulator); self.stop.clicked.connect(app.stop_simulator); self.analyze.clicked.connect(app.analyze_telemetry); self.ai_analyze.clicked.connect(app.ai_analyze_live_data)
        bar.addWidget(self.status); bar.addWidget(self.ai_status); bar.addStretch(); bar.addWidget(self.start); bar.addWidget(self.stop); bar.addWidget(self.analyze); bar.addWidget(self.ai_analyze); lay.addLayout(bar)
        self.cards=QGridLayout(); lay.addLayout(self.cards); self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(["PID / Channel","Count","Min","Max","Mean","Events"]); self.table.horizontalHeader().setStretchLastSection(True); lay.addWidget(self.table); self.chart=Sparkline(); lay.addWidget(self.chart)
        self.ai_box=QPlainTextEdit(); self.ai_box.setReadOnly(True); self.ai_box.setPlaceholderText("AI live-data interpretation will appear here..."); self.ai_box.setMaximumHeight(240); lay.addWidget(self.ai_box)
        self.timer=QTimer(self); self.timer.setInterval(700); self.timer.timeout.connect(self._poll)
    def _poll(self):
        if self.app.session and self.app.online:
            try:
                status=self.app.api.acquisition_status(self.app.session.session_id)
                running = status.get("state") == "RUNNING"
                self.status.setText("RUNNING" if running else status.get("state", "Stopped"))
                if running:
                    self.app.refresh_telemetry()
            except Exception:
                self.status.setText("Stopped")

    def refresh(self):
        if not self.app.session:
            self.timer.stop()
            return
        try:
            status=self.app.api.acquisition_status(self.app.session.session_id); running = status.get("state") == "RUNNING"
            self.status.setText("RUNNING" if running else status.get("state", "Stopped"))
            if running and not self.timer.isActive(): self.timer.start()
            if not running and self.timer.isActive(): self.timer.stop()
        except ApiError:
            self.status.setText("Stopped"); self.timer.stop()
        try:
            provider=self.app.api.ai_provider_info()
            available=bool(provider.get("available"))
            model=provider.get("model", "—")
            reason=provider.get("reason")
            self.ai_status.setText(f"AI: {'READY' if available else 'OFFLINE'} • {model}" + (f" • {reason}" if reason and not available else ""))
            self.ai_status.setObjectName("ok" if available else "warn")
            self.ai_status.style().unpolish(self.ai_status); self.ai_status.style().polish(self.ai_status)
        except Exception:
            self.ai_status.setText("AI: unavailable")
        self.table.setRowCount(0); summary=self.app.telemetry
        stats=summary.get("signals") or summary.get("stats") or []
        values=[]
        for st in stats:
            row=self.table.rowCount(); self.table.insertRow(row)
            vals=[st.get("pid",""),st.get("count",0),st.get("min_value","—"),st.get("max_value","—"),st.get("mean","—"),st.get("event_count",0)]
            for c,val in enumerate(vals): self.table.setItem(row,c,QTableWidgetItem(str(val)))
        try:
            rec=self.app.api.acquisition_records(self.app.session.session_id).get("records",[])
            values=[float(r["numeric_value"]) for r in rec if r.get("numeric_value") is not None]
        except Exception: pass
        self.chart.set_values(values)

class TestsPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); self.list=QListWidget(); lay.addWidget(self.list)
        bar=QHBoxLayout(); language = getattr(app, "language", "en")
        self.result=QComboBox(); self.result.addItem(_translate_ui_text("PASS", language), "PASS"); self.result.addItem(_translate_ui_text("FAIL", language), "FAIL"); self.result.addItem(_translate_ui_text("INCOMPLETE", language), "INCOMPLETE"); self.notes=QLineEdit(); self.notes.setPlaceholderText("Technician notes / measurements"); submit=QPushButton("Record selected result"); submit.clicked.connect(app.record_selected_test); bar.addWidget(self.result); bar.addWidget(self.notes); bar.addWidget(submit); lay.addLayout(bar)
    def refresh(self):
        self.list.clear(); self.app.test_candidates=[]
        for item in self.app.decision.get("candidates",[]):
            c=TestCandidate.from_json(item); self.app.test_candidates.append(c)
            label=f"{c.priority_score:.2f} • {c.name} • risk={c.risk_level}\n{c.purpose}"
            q=QListWidgetItem(label); q.setData(Qt.UserRole,c.test_id); self.list.addItem(q)

class DevicesPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self)
        title=QLabel("VCI / Adapter Connection"); title.setObjectName("title"); lay.addWidget(title)
        info=QLabel("Discover USB/BLE adapters or connect to a Wi-Fi OBD endpoint. Physical writes/programming are not exposed here."); info.setObjectName("muted"); lay.addWidget(info)

        scan=QHBoxLayout()
        usb=QPushButton("Scan USB"); ble=QPushButton("Scan BLE"); sim=QPushButton("Add Simulator"); wifi=QPushButton("Probe Wi-Fi")
        usb.clicked.connect(lambda:self.app.scan_devices("usb")); ble.clicked.connect(lambda:self.app.scan_devices("ble")); sim.clicked.connect(self.app.add_simulator_device); wifi.clicked.connect(self.app.probe_wifi)
        for b in (usb,ble,sim,wifi): scan.addWidget(b)
        scan.addStretch(); lay.addLayout(scan)

        split=QSplitter(); self.list=QListWidget(); self.list.itemSelectionChanged.connect(self._selected_changed); split.addWidget(self.list)
        detail=QWidget(); form=QFormLayout(detail)
        self.info_box=QPlainTextEdit(); self.info_box.setReadOnly(True); self.info_box.setMaximumHeight(180)
        self.host=QLineEdit(); self.host.setPlaceholderText("192.168.0.10")
        self.port=QSpinBox(); self.port.setRange(1,65535); self.port.setValue(35000)
        self.baud=QSpinBox(); self.baud.setRange(1200,4000000); self.baud.setValue(115200)
        self.tx_uuid=QLineEdit(); self.tx_uuid.setPlaceholderText("BLE TX characteristic UUID")
        self.rx_uuid=QLineEdit(); self.rx_uuid.setPlaceholderText("BLE RX characteristic UUID")
        form.addRow("Selected device", self.info_box); form.addRow("Wi-Fi host", self.host); form.addRow("Wi-Fi port", self.port); form.addRow("USB baudrate", self.baud); form.addRow("BLE TX UUID", self.tx_uuid); form.addRow("BLE RX UUID", self.rx_uuid)
        buttons=QHBoxLayout()
        connect=QPushButton("Connect"); disconnect=QPushButton("Disconnect"); reconnect=QPushButton("Reconnect")
        connect.clicked.connect(self.app.connect_selected_device); disconnect.clicked.connect(self.app.disconnect_selected_device); reconnect.clicked.connect(self.app.reconnect_selected_device)
        for b in (connect,disconnect,reconnect): buttons.addWidget(b)
        form.addRow(buttons)
        read=QHBoxLayout(); vin=QPushButton("Read VIN"); dtc=QPushButton("Read DTCs"); live=QPushButton("Read Live Data")
        vin.clicked.connect(self.app.read_device_vin); dtc.clicked.connect(self.app.read_device_dtcs); live.clicked.connect(self.app.read_device_live_data)
        for b in (vin,dtc,live): read.addWidget(b)
        form.addRow(read)
        self.result=QPlainTextEdit(); self.result.setReadOnly(True); form.addRow("Device result", self.result)
        split.addWidget(detail); split.setSizes([460,900]); lay.addWidget(split,1)

    def current(self) -> dict[str, Any] | None:
        item=self.list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _selected_changed(self):
        d=self.current()
        if not d:
            return
        meta=d.get("metadata") or {}
        self.info_box.setPlainText(
            f"ID: {d.get('device_id','')}\n"
            f"Manufacturer: {d.get('manufacturer','')}\n"
            f"Model: {d.get('model','')}\n"
            f"Connection: {d.get('connection_type','')}\n"
            f"Protocol: {d.get('protocol','')}\n"
            f"Status: {d.get('status','')}\n"
            f"Firmware: {d.get('firmware_version') or '—'}\n"
            f"Capabilities: {d.get('capabilities',{})}\n"
            f"Metadata: {meta}"
        )
        if d.get("connection_type") == "Wi-Fi":
            self.host.setText(str(meta.get("host") or "")); self.port.setValue(int(meta.get("port") or 35000))
        if d.get("connection_type") == "USB":
            self.host.clear(); self.port.setValue(int(meta.get("port") or 35000))

    def refresh(self):
        self.list.clear()
        for d in self.app.devices:
            status=d.get("status","disconnected").upper()
            text=f"{status} • {d.get('connection_type','?')} • {d.get('manufacturer','Unknown')} {d.get('model','')}\n{d.get('device_id','')}"
            item=QListWidgetItem(text); item.setData(Qt.UserRole,d); self.list.addItem(item)
        if self.app.selected_device_id:
            for i in range(self.list.count()):
                d=self.list.item(i).data(Qt.UserRole)
                if d.get("device_id") == self.app.selected_device_id:
                    self.list.setCurrentRow(i); break

    def config(self) -> dict[str, Any]:
        return {"host":self.host.text().strip(),"port":self.port.value(),"baudrate":self.baud.value(),"tx_uuid":self.tx_uuid.text().strip(),"rx_uuid":self.rx_uuid.text().strip()}

class NetworkPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); bar=QHBoxLayout(); discover=QPushButton("Refresh network map"); probe=QPushButton("Active read-only probe"); discover.clicked.connect(app.refresh_network); probe.clicked.connect(app.active_probe); bar.addWidget(discover); bar.addWidget(probe); bar.addStretch(); lay.addLayout(bar); self.tree=QPlainTextEdit(); self.tree.setReadOnly(True); lay.addWidget(self.tree)
    def refresh(self):
        data=self.app.network; active=self.app.active_network
        lines=["PASSIVE / INFERRED NETWORK",""]
        for x in (data.get("ecus",[]) if isinstance(data,dict) else []): lines.append(f"ECU {x.get('ecu_id',x.get('id','?'))} | bus={x.get('bus','?')} | state={x.get('state','INFERRED')} | confidence={x.get('confidence','—')}")
        if active: lines += ["","ACTIVE CORRELATION",str(active)]
        self.tree.setPlainText("\n".join(lines) if len(lines)>2 else "No discovered ECU candidates yet.")

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings_store = QSettings("AI-CAR-SCANER", "Desktop")
        self.language = self.settings_store.value("language", "en", type=str)
        if self.language not in {"en", "ru", "hy"}:
            self.language = "en"
        self.dark_theme = self.settings_store.value("dark_theme", True, type=bool)
        self.setWindowTitle("AI Auto Diagnostic Workstation")
        self.resize(1440, 900)
        self._apply_theme()
        self.api = DiagnosticApiClient()
        self.store = VehicleStore()
        self.vehicles = self.store.load()
        self.active_vehicle = None
        self.session = None
        self.session_json = {}
        self.decision = {}
        self.telemetry = {}
        self.network = {}
        self.active_network = {}
        self.devices = []
        self.selected_device_id = None
        self.test_candidates = []
        self.online = False
        self._workers = []
        self.stack = QStackedWidget()
        self.pages = []
        self._build_pages()
        self._build_menu()
        self.setCentralWidget(self.stack)
        self.statusBar().showMessage("Ready")
        self.refresh_all()

    def _apply_theme(self) -> None:
        self.setStyleSheet(APP_QSS if self.dark_theme else APP_QSS_LIGHT)

    def _open_settings(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr_text("Application settings"))
        dialog.setMinimumWidth(360)
        form = QFormLayout(dialog)
        language = QComboBox(dialog)
        language.addItem("English", "en")
        language.addItem("Русский", "ru")
        language.addItem("Հայերեն", "hy")
        language.setCurrentIndex(max(0, language.findData(self.language)))
        theme = QComboBox(dialog)
        theme.addItem(self.tr_text("Dark"), True)
        theme.addItem(self.tr_text("Light"), False)
        theme.setCurrentIndex(max(0, theme.findData(self.dark_theme)))
        form.addRow(self.tr_text("Language"), language)
        form.addRow(self.tr_text("Theme"), theme)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=dialog)
        buttons.button(QDialogButtonBox.Save).setText(self.tr_text("Save"))
        buttons.button(QDialogButtonBox.Cancel).setText(self.tr_text("Cancel"))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.Accepted:
            return
        self.language = str(language.currentData())
        self.dark_theme = bool(theme.currentData())
        self.settings_store.setValue("language", self.language)
        self.settings_store.setValue("dark_theme", self.dark_theme)
        self._apply_theme()
        self._apply_language()
        self.refresh_pages()
        self.statusBar().showMessage(self.tr_text("Settings saved") + " • " + self.tr_text("Language") + "=" + self.language + " • " + self.tr_text("Theme") + "=" + self.tr_text("Dark" if self.dark_theme else "Light"))

    def tr_text(self, text: str) -> str:
        return _translate_ui_text(text, self.language)

    def _apply_language(self) -> None:
        self.setWindowTitle(self.tr_text("AI Auto Diagnostic Workstation"))
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QLabel):
                if widget.objectName() != "vehicleMetricValue":
                    widget.setText(self.tr_text(widget.text()))
            elif isinstance(widget, QPushButton):
                widget.setText(self.tr_text(widget.text()))
            elif isinstance(widget, QGroupBox):
                widget.setTitle(self.tr_text(widget.title()))
            elif isinstance(widget, QLineEdit):
                widget.setPlaceholderText(self.tr_text(widget.placeholderText()))
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlaceholderText(self.tr_text(widget.placeholderText()))
                if widget.isReadOnly():
                    widget.setPlainText(_translate_ui_block(widget.toPlainText(), self.language))
            elif isinstance(widget, QListWidget):
                if widget is self.nav or (len(self.pages) > 6 and widget is self.pages[6].list):
                    for index in range(widget.count()):
                        item = widget.item(index)
                        item.setText(self.tr_text(item.text()))
            elif isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    widget.setItemText(index, self.tr_text(widget.itemText(index)))
            elif isinstance(widget, QTableWidget):
                for column in range(widget.columnCount()):
                    item = widget.horizontalHeaderItem(column)
                    if item:
                        item.setText(self.tr_text(item.text()))
        for tab_widget in self.findChildren(QTabWidget):
            for index in range(tab_widget.count()):
                tab_widget.setTabText(index, self.tr_text(tab_widget.tabText(index)))
        for action in self.findChildren(QAction):
            action.setText(self.tr_text(action.text()))
        for menu in self.menuBar().findChildren(QWidget):
            if hasattr(menu, "title") and callable(menu.title):
                try:
                    menu.setTitle(self.tr_text(menu.title()))
                except (AttributeError, TypeError):
                    pass
        self.statusBar().showMessage(self.tr_text(self.statusBar().currentMessage()))

    def _build_pages(self):
        container=QWidget(); root=QHBoxLayout(container); root.setContentsMargins(0,0,0,0)
        nav=QListWidget(); nav.setFixedWidth(210); entries=[("◉  Dashboard",DashboardPage), ("▣  Vehicles",VehiclesPage), ("🔌  VCI / Devices",DevicesPage), ("⚙  Diagnostic",DiagnosticPage), ("◌  Live Data",LiveDataPage), ("⌘  ECU Network",NetworkPage), ("✓  Tests",TestsPage)]
        self.nav=nav
        for text,_cls in entries: nav.addItem(text)
        root.addWidget(nav)
        content=QStackedWidget(); root.addWidget(content,1)
        for _text, cls in entries:
            page=cls(self); self.pages.append(page); content.addWidget(page)
        nav.currentRowChanged.connect(content.setCurrentIndex); nav.setCurrentRow(0)
        self.stack.addWidget(container)
    def _build_menu(self):
        menu = self.menuBar().addMenu("Application")
        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        helpm = self.menuBar().addMenu("Help")
        about = QAction("About", self)
        about.triggered.connect(lambda: QMessageBox.information(
            self, self.tr_text("About"), self.tr_text("AI Auto Diagnostic Workstation") + "\n" + self.tr_text("Evidence-driven automotive diagnostics.")
        ))
        helpm.addAction(about)
    def run_worker(self,fn:Callable[[],Any],done:Callable[[Any],None]) -> None:
        worker=Worker(fn); self._workers.append(worker); worker.finished_ok.connect(done); worker.failed.connect(self.show_error); worker.finished.connect(lambda: self._workers.remove(worker) if worker in self._workers else None); worker.start()
    def show_error(self,msg:str):
        translated = self.tr_text(msg)
        QMessageBox.critical(self, self.tr_text("Error"), translated)
        self.statusBar().showMessage(translated)
    def refresh_health(self):
        def done(data): self.online=data.get("status")=="ok"; self.statusBar().showMessage("Backend online" if self.online else "Backend offline"); self.refresh_pages()
        self.run_worker(self.api.health,done)
    def refresh_all(self): self.refresh_health(); self.refresh_devices(); self.refresh_pages()
    def refresh_pages(self):
        for p in self.pages:
            try: p.refresh()
            except Exception: pass
        self._apply_language()
    def add_vehicle(self):
        d=VehicleDialog(self)
        if d.exec()!=QDialog.Accepted: return
        v=d.vehicle(); self.vehicles=[x for x in self.vehicles if not (x.make==v.make and x.model==v.model and x.year==v.year and x.engine==v.engine)]; self.vehicles.append(v); self.store.save(self.vehicles); self.active_vehicle=v; self.pages[1].refresh(); self.new_session()
    def delete_selected_vehicle(self):
        page=self.pages[1]
        items=page.list.selectedItems()
        if not items:
            self.show_error("Select a vehicle to delete.")
            return
        index=int(items[0].data(Qt.UserRole))
        if index < 0 or index >= len(self.vehicles):
            self.show_error("Selected vehicle is no longer available.")
            return
        vehicle=self.vehicles[index]
        label=f"{vehicle.make} {vehicle.model} ({vehicle.year or '—'})"
        answer=QMessageBox.question(
            self,
            self.tr_text("Delete vehicle"),
            self.tr_text(f"Delete {label} from local vehicle profiles?\n\nExisting diagnostic sessions are not deleted."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.vehicles.pop(index)
        self.store.save(self.vehicles)
        if self.active_vehicle is vehicle:
            self.active_vehicle = None
        page.refresh()
        self.refresh_pages()
        self.statusBar().showMessage(f"Vehicle deleted: {label}")
    def refresh_devices(self):
        self.run_worker(self.api.list_devices, lambda data: self._devices_done(data.get("devices", [])))

    def _devices_done(self, devices):
        self.devices=devices; self.refresh_pages(); self.statusBar().showMessage(f"VCI devices: {len(devices)}")

    def scan_devices(self, transport: str):
        self.run_worker(lambda:self.api.scan_devices(transport), lambda data:self._devices_done(data.get("devices", [])))

    def add_simulator_device(self):
        self.run_worker(self.api.add_simulator_device, lambda data:self._device_added(data))

    def _device_added(self, data):
        self.selected_device_id=data.get("device_id"); self.run_worker(self.api.list_devices, lambda payload:self._devices_done(payload.get("devices", [])))

    def probe_wifi(self):
        page=self.pages[2]
        host=page.host.text().strip(); port=page.port.value()
        if not host:
            self.show_error("Enter the Wi-Fi OBD adapter host, for example 192.168.0.10."); return
        self.run_worker(lambda:self.api.probe_wifi(host,port), lambda data:self._device_added(data))

    def _selected_device(self):
        page=self.pages[2]
        data=page.current()
        if not data:
            self.show_error("Select a VCI/device first."); return None
        self.selected_device_id=str(data.get("device_id")); return data

    def connect_selected_device(self):
        data=self._selected_device()
        if not data: return
        page=self.pages[2]
        self.run_worker(lambda:self.api.connect_device(self.selected_device_id,page.config()), lambda result:self._device_action_done(result,"Device connected"))

    def disconnect_selected_device(self):
        data=self._selected_device()
        if not data: return
        self.run_worker(lambda:self.api.disconnect_device(self.selected_device_id), lambda result:self._device_action_done(result,"Device disconnected"))

    def reconnect_selected_device(self):
        data=self._selected_device()
        if not data: return
        self.run_worker(lambda:self.api.reconnect_device(self.selected_device_id), lambda result:self._device_action_done(result,"Device reconnected"))

    def _device_action_done(self, result, message):
        self.devices=[d for d in self.devices if d.get("device_id") != result.get("device_id")] + [result]
        self.refresh_pages(); self.statusBar().showMessage(message)

    def read_device_vin(self):
        if not self._selected_device(): return
        self.run_worker(lambda:self.api.device_vin(self.selected_device_id), lambda data:self.pages[2].result.setPlainText(f"VIN: {data.get('vin') or 'Not available'}"))

    def read_device_dtcs(self):
        if not self._selected_device(): return
        self.run_worker(lambda:self.api.device_dtcs(self.selected_device_id), lambda data:self.pages[2].result.setPlainText("DTCs:\n" + ("\n".join(data.get("dtcs",[])) or "No stored generic OBD-II DTCs")))

    def read_device_live_data(self):
        if not self._selected_device(): return
        self.run_worker(lambda:self.api.device_live_data(self.selected_device_id), lambda data:self.pages[2].result.setPlainText(str(data.get("values", data))))

    def new_session(self):
        if not self.active_vehicle:
            if not self.vehicles: self.add_vehicle(); return
            self.active_vehicle=self.vehicles[0]
        if not self.online: self.show_error("Backend is offline. Start the FastAPI backend first."); return
        self.run_worker(lambda:self.api.create_session(self.active_vehicle.to_json()),self._session_created)
    def _session_created(self,data):
        self.session=Session(str(data.get("session_id")),str(data.get("state","CREATED")),self.active_vehicle); self.session_json=data; self.decision={}; self.telemetry={}; self.network={}; self.active_network={}; self.nav.setCurrentRow(3); self.refresh_pages(); self.statusBar().showMessage("Diagnostic session created")
    def analyze_input(self):
        if not self.session: self.new_session(); return
        text=self.pages[3].symptom.toPlainText().strip(); dtc=self.pages[3].dtc.text().strip()
        if not text and not dtc: self.show_error("Enter a symptom, observation or DTC."); return
        def work():
            if text: self.api.ingest_evidence(self.session.session_id,text)
            if dtc: self.api.add_dtc(self.session.session_id,dtc)
            return self.api.analyze(self.session.session_id, language=self.language)
        self.run_worker(work,self._analysis_done)
    def _analysis_done(self,data): self.session_json=data; self.session=Session(str(data.get("session_id")),str(data.get("state","")),self.active_vehicle); self.run_worker(lambda:self.api.decision_plan(self.session.session_id),self._decision_done)
    def _decision_done(self,data): self.decision=data; self.nav.setCurrentRow(3); self.refresh_pages(); self.statusBar().showMessage("Diagnostic reasoning updated")
    def start_simulator(self):
        if not self.session: self.new_session(); return
        self.run_worker(lambda:self.api.start_simulator(self.session.session_id),lambda _d:self._sim_changed("Simulator acquisition started"))
    def stop_simulator(self):
        if not self.session: return
        self.run_worker(lambda:self.api.stop_acquisition(self.session.session_id),lambda _d:self._sim_changed("Acquisition stopped"))
    def _sim_changed(self,msg): self.statusBar().showMessage(msg); self.refresh_telemetry()
    def refresh_telemetry(self):
        if not self.session: return
        def work(): return {"summary":self.api.telemetry_summary(self.session.session_id),"records":self.api.acquisition_records(self.session.session_id)}
        def done(data): self.telemetry=data["summary"]; self.refresh_pages()
        self.run_worker(work,done)
    def analyze_telemetry(self):
        if not self.session: return
        self.run_worker(lambda:self.api.analyze_telemetry(self.session.session_id),lambda data:self._telemetry_done(data))
    def _telemetry_done(self,data): self.telemetry=data; self.refresh_pages(); self.statusBar().showMessage("Telemetry analysis completed")
    def ai_analyze_live_data(self):
        if not self.session:
            self.show_error("Create a diagnostic session first."); return
        self.statusBar().showMessage("AI is analyzing live vehicle data...")
        self.run_worker(lambda:self.api.ai_analyze_live_data(self.session.session_id), self._live_ai_done)

    def _live_ai_done(self,data):
        ai=data.get("ai", {})
        text=ai.get("text", "No AI result.")
        if not ai.get("available", False):
            text += "\n\nProvider error: " + str(ai.get("error", "unknown"))
        self.pages[4].ai_box.setPlainText(
            f"Provider: {ai.get('provider','—')} | Model: {ai.get('model','—')} | Available: {ai.get('available',False)}\n\n{text}"
        )
        self.telemetry=data.get("telemetry", self.telemetry)
        self.session_json=data.get("session", self.session_json)
        self.refresh_pages()
        self.statusBar().showMessage("Live-data AI analysis completed")
    def refresh_network(self):
        if not self.session: return
        self.run_worker(lambda:self.api.network_map(self.session.session_id),lambda data:self._network_done(data))
    def _network_done(self,data): self.network=data; self.refresh_pages(); self.statusBar().showMessage("Network map refreshed")
    def active_probe(self):
        if not self.session: return
        ids=[str(x.get("id") or x.get("ecu_id")) for x in self.network.get("ecus",[]) if x.get("id") or x.get("ecu_id")]
        self.run_worker(lambda:self.api.active_probe(self.session.session_id,ids or None),lambda data:self._active_done(data))
    def _active_done(self,data): self.active_network=data; self.refresh_pages(); self.statusBar().showMessage("Active read-only ECU probe completed")
    def record_selected_test(self):
        if not self.session: self.show_error("No active session."); return
        item=self.pages[6].list.currentItem()
        if not item: self.show_error("Select a diagnostic test first."); return
        tid=str(item.data(Qt.UserRole)); result=str(self.pages[6].result.currentData() or self.pages[6].result.currentText()); notes=self.pages[6].notes.text().strip()
        def work():
            data=self.api.record_test_result(self.session.session_id, tid, result, notes=notes, language=self.language); self.api.analyze(self.session.session_id, language=self.language); return self.api.decision_plan(self.session.session_id)
        self.run_worker(work,self._decision_done)


def _resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parents[2]
    return base / relative


def run() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AI-CAR-SCANER.Desktop")
        except (AttributeError, OSError):
            pass
    app = QApplication([])
    app.setApplicationName("AI Auto Diagnostic Workstation")
    icon_path = _resource_path("assets/AI-Car-Scanner-mobile.png")
    if not icon_path.is_file():
        icon_path = _resource_path("assets/AI-Car-Scanner.ico")
    app_icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    win = MainWindow()
    if not app_icon.isNull():
        win.setWindowIcon(app_icon)
    win._apply_language()
    win.show()
    app.exec()
