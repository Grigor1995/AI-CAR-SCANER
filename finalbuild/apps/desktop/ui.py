from __future__ import annotations
from pathlib import Path
import json
import os
import re
import sys
from functools import lru_cache
import time
from typing import Any, Callable
from PySide6.QtCore import Qt, QThread, Signal, Slot, QRectF, QSize, QTimer, QSettings, QCoreApplication, QEvent
from PySide6.QtGui import QAction, QColor, QPainter, QPen, QBrush, QIcon, QImage, QFont
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
from .vehicle_artwork import vehicle_pixmap
from .dashboard_translations import MESSAGES
from .demo_ui import DemoDashboard, DTCPage, HypothesesPage, ReportsPage, TeachPage, SignalGrid

APP_QSS = """
QPushButton#topNav { min-height: 38px; background: #0A243B; border: 1px solid #116AB5; padding: 9px 12px; }
QLabel#metricValue { font-size: 21pt; font-weight: 700; }
QLabel#signalValue { font-size: 18pt; font-weight: 700; }
QLabel[accent="red"] { color: #FF5D79; }
QLabel[accent="green"] { color: #20C995; }
QLabel[accent="violet"] { color: #AA7CFF; }
QScrollArea { border: none; }

QMainWindow, QWidget, QDialog { background: #061121; color: #EAF4FF; font-family: Segoe UI, Arial; font-size:10pt; }
QLabel { background: transparent; border: none; }
QMainWindow { border: 1px solid #1C4B89; }
QGroupBox { background: #0C1B35; border: 1px solid #24518F; border-radius: 14px; }
QGroupBox { margin-top: 15px; padding: 15px 12px 12px; font-weight: 650; }
QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 7px; color: #A9CFFF; }
QPushButton { background: #132D56; color: #EAF4FF; border: 1px solid #2864AC; border-radius: 9px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #1A4F92; border: 1px solid #2998FF; }
QPushButton:pressed { background: #0D366A; }
QPushButton:disabled { color: #6983A5; background: #10213B; border: 1px solid #1B3556; }
QPushButton#primary { background: #0877EF; color: white; border: 1px solid #46ABFF; font-weight: 750; }
QLineEdit, QPlainTextEdit, QSpinBox, QComboBox { background: #08182F; color: #EAF4FF; border: 1px solid #28538A; border-radius: 9px; padding: 9px; selection-background-color: #1465B5; }
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #2495FF; }
QListWidget { background: #08172D; border: 1px solid #244575; border-radius: 12px; outline: 0; }
QListWidget#sideNav { background: #081B39; border: 1px solid #1C5096; border-radius: 14px; font-weight: 600; }
QListWidget::item { padding: 13px 11px; border-radius: 9px; margin: 2px 3px; }
QListWidget::item:hover { background: #123562; }
QListWidget::item:selected { background: #1054A5; color: white; border: 1px solid #268FF7; }
QTabWidget::pane { border: 1px solid #26568E; border-radius: 10px; background: #0A1C37; }
QTabBar::tab { background: #10284D; color: #C2DAF3; padding: 10px 17px; margin-right: 3px; border: 1px solid #24518F; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #1666BE; color: white; border-color: #2898FF; }
QHeaderView::section, QTableWidget { background: #0C1E3A; color: #DCEEFF; border: 1px solid #294E83; padding: 5px; }
QTableWidget { gridline-color: #1F426D; }
QProgressBar { background: #07172C; border: 1px solid #27558D; border-radius: 6px; height: 11px; text-align: center; }
QProgressBar::chunk { background: #0B8DFF; border-radius: 6px; }
QLabel#title { font-size:17pt; font-weight: 750; color: #F3FAFF; }
QLabel#heroTitle { font-size:22pt; color: #F4FAFF; font-weight: 800; }
QLabel#heroSubtitle { color: #72BEFF; font-size:9pt; letter-spacing: 2px; font-weight: 700; }
QLabel#muted { color: #93B7D8; }
QLabel#ok { color: #27DB98; font-weight: 700; }
QLabel#warn { color: #FFCC65; font-weight: 700; }
QMenuBar, QMenu, QStatusBar { background: #091B35; color: #D8ECFF; }
QMenu::item:selected { background: #165CAC; }
QScrollBar:vertical { background: #09172C; width: 12px; }
QScrollBar::handle:vertical { background: #26568F; border-radius: 5px; min-height: 24px; }

QScrollBar:vertical { background: #09172C; width: 8px; margin: 0; }
QScrollBar:horizontal { background: #09172C; height: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #2789DE; border-radius: 4px; min-height: 28px; }
QScrollBar::handle:horizontal { background: #2789DE; border-radius: 4px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""

APP_QSS_LIGHT = """
QPushButton#topNav { min-height: 38px; background: #FFFFFF; border: 1px solid #B1CAE5; padding: 9px 12px; }
QLabel#metricValue { font-size: 21pt; font-weight: 700; }
QLabel#signalValue { font-size: 18pt; font-weight: 700; }
QLabel[accent="red"] { color: #FF5D79; }
QLabel[accent="green"] { color: #20C995; }
QLabel[accent="violet"] { color: #AA7CFF; }
QScrollArea { border: none; }

QMainWindow, QWidget, QDialog { background: #F0F6FC; color: #10243F; font-family: Segoe UI, Arial; font-size:10pt; }
QLabel { background: transparent; border: none; }
QGroupBox { background: #FFFFFF; border: 1px solid #B7D1EC; border-radius: 14px; }
QGroupBox { margin-top: 15px; padding: 15px 12px 12px; font-weight: 650; }
QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 7px; color: #315C88; }
QPushButton { background: #E2EFFD; color: #0B3562; border: 1px solid #93BDE8; border-radius: 9px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #B6DDFF; border-color: #2688EB; }
QPushButton:pressed { background: #92C7FF; }
QPushButton:disabled { color: #8098AE; background: #EAF1F7; }
QPushButton#primary { background: #0877EF; color: #FFFFFF; border: 1px solid #0673E3; font-weight: 750; }
QLineEdit, QPlainTextEdit, QSpinBox, QComboBox { background: #FFFFFF; color: #12365A; border: 1px solid #B1CAE5; border-radius: 9px; padding: 9px; selection-background-color: #70B5F8; }
QLineEdit:focus, QPlainTextEdit:focus { border-color: #0877EF; }
QListWidget { background: #FFFFFF; border: 1px solid #B9D2EA; border-radius: 12px; outline: 0; }
QListWidget#sideNav { background: #E2EFFC; border: 1px solid #A5C5E9; border-radius: 14px; font-weight: 600; }
QListWidget::item { padding: 13px 11px; border-radius: 9px; margin: 2px 3px; }
QListWidget::item:hover { background: #C5E1FF; }
QListWidget::item:selected { background: #1673DB; color: #FFFFFF; border: 1px solid #0965C7; }
QTabWidget::pane { border: 1px solid #ADCBE8; border-radius: 10px; background: #FFFFFF; }
QTabBar::tab { background: #E5F0FA; color: #285078; padding: 10px 17px; margin-right: 3px; border: 1px solid #B6CFE7; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #1673DB; color: #FFFFFF; border-color: #126CCE; }
QHeaderView::section, QTableWidget { background: #F4F9FF; color: #12365A; border: 1px solid #BCD1E8; padding: 5px; }
QProgressBar { background: #E6F0FA; border: 1px solid #B2D0EC; border-radius: 6px; height: 11px; text-align: center; }
QProgressBar::chunk { background: #0877EF; border-radius: 6px; }
QLabel#title { font-size:17pt; font-weight: 750; color: #14385B; }
QLabel#heroTitle { font-size:22pt; color: #123A68; font-weight: 800; }
QLabel#heroSubtitle { color: #1169BD; font-size:9pt; letter-spacing: 2px; font-weight: 700; }
QLabel#muted { color: #547492; }
QLabel#ok { color: #078D63; font-weight: 700; }
QLabel#warn { color: #B66B05; font-weight: 700; }
QMenuBar, QMenu, QStatusBar { background: #E3EFFA; color: #12365A; }
QMenu::item:selected { background: #B2DCFF; }

QScrollBar:vertical { background: #E2EFFD; width: 8px; margin: 0; }
QScrollBar:horizontal { background: #E2EFFD; height: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #448ECC; border-radius: 4px; min-height: 28px; }
QScrollBar::handle:horizontal { background: #448ECC; border-radius: 4px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


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


_UI_TRANSLATIONS["hy"].update({
    "Home / Summary": "Գլխավոր / Ամփոփում", "Selected vehicle": "Ընտրված մեքենա",
    "Quick actions": "Արագ գործողություններ", "Recorded tests": "Գրանցված թեստեր",
    "Testing progress": "Փորձարկման ընթացք", "Reports": "Հաշվետվություններ",
    "History": "Պատմություն", "Teach AI": "Սովորեցրու AI-ին", "AI Analysis": "AI վերլուծություն",
    "Guided Tests": "Ուղղորդվող փորձարկումներ", "Diagnostics": "Ախտորոշում",
    "Search vehicle": "Փնտրել մեքենա", "DTC list & details": "DTC ցանկ և մանրամասներ",
    "Your solution": "Քո լուծումը", "Custom dashboard": "Անհատական վահանակ",
    "Save draft": "Պահել սևագիրը", "Ingest reference note": "Ներմուծել տեղեկատու նշումը",
    "Export current report": "Արտահանել հաշվետվությունը", "Refresh history": "Թարմացնել պատմությունը",
    "Open selected": "Բացել ընտրվածը", "Repair / observation title": "Վերանորոգման / դիտարկման վերնագիր",
})
_UI_TRANSLATIONS["ru"].update({
    "Home / Summary": "Обзор / Сводка", "Selected vehicle": "Выбранный автомобиль",
    "Quick actions": "Быстрые действия", "Recorded tests": "Записанные тесты",
    "Testing progress": "Ход тестирования", "Reports": "Отчёты", "History": "История",
    "Teach AI": "Обучить ИИ", "AI Analysis": "ИИ-анализ", "Guided Tests": "Пошаговые тесты",
    "Diagnostics": "Диагностика", "Search vehicle": "Поиск автомобиля",
    "DTC list & details": "Список и сведения DTC", "Your solution": "Ваше решение",
    "Custom dashboard": "Настраиваемая панель", "Save draft": "Сохранить черновик",
    "Ingest reference note": "Добавить справочный материал", "Export current report": "Экспорт отчёта",
    "Refresh history": "Обновить историю", "Open selected": "Открыть выбранное",
    "Repair / observation title": "Название ремонта / наблюдения",
})


_UI_TRANSLATIONS["hy"].update({"Edit vehicle": "Խմբագրել մեքենան"})
_UI_TRANSLATIONS["ru"].update({"Edit vehicle": "Изменить автомобиль"})

# Load bundled presentation strings before compiling the cached translation patterns.
for _language, _messages in MESSAGES.items():
    _UI_TRANSLATIONS[_language].update(_messages)

@lru_cache(maxsize=1)
def _translation_patterns():
    reverse = {}
    for mapping in _UI_TRANSLATIONS.values():
        for original, translated in sorted(mapping.items(), key=lambda pair: len(pair[1]), reverse=True):
            reverse.setdefault(translated, original)
    def pattern(mapping):
        return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(key) for key in sorted(mapping, key=len, reverse=True)) + r")(?!\w)")
    return reverse, pattern(reverse), {language: pattern(mapping) for language, mapping in _UI_TRANSLATIONS.items()}


@lru_cache(maxsize=4096)
def _translated_text(text, language):
    reverse, canonical_pattern, targets = _translation_patterns()
    canonical = canonical_pattern.sub(lambda match: reverse[match.group(0)], text)
    if language not in targets:
        return canonical
    return targets[language].sub(lambda match: _UI_TRANSLATIONS[language][match.group(0)], canonical)


def _translate_ui_text(text: str, language: str) -> str:
    return _translated_text(text, language) if isinstance(text, str) else text




def _translate_ui_block(text: str, language: str) -> str:
    """Translate UI labels/static messages without rewriting vehicle or ECU values."""
    if not isinstance(text, str):
        return text
    return "\n".join(_translate_known_ui_line(line, language) for line in text.splitlines())


@lru_cache(maxsize=4096)
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
        layout = QVBoxLayout(self); self.value = QLabel(value); self.value.setObjectName("vehicleMetricValue" if title == "Vehicle" else ""); self.value.setStyleSheet("font-size:20pt;font-weight:700;"); layout.addWidget(self.value)
    def set_value(self, value: str) -> None: self.value.setText(value)

class VehicleDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        language = getattr(parent, "language", "en")
        self.setWindowTitle(_translate_ui_text("Add Vehicle", language))
        self.resize(520, 440)
        self._catalog: list[dict[str, Any]] = []
        api = getattr(parent, "api", None)
        cached = getattr(parent, "_vehicle_catalog", None)
        if cached is not None:
            self._catalog = list(cached)
        elif api is not None:
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
        self.artwork_preview = QLabel()
        self.artwork_preview.setObjectName("vehicleArtworkPreview")
        self.artwork_preview.setMinimumHeight(140)
        self.artwork_preview.setAlignment(Qt.AlignCenter)
        form.addRow(self.artwork_preview)
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
        for combo in (self.make, self.model, self.chassis):
            combo.currentTextChanged.connect(self._update_artwork_preview)
        self._update_artwork_preview()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(_translate_ui_text("OK", language))
        buttons.button(QDialogButtonBox.Cancel).setText(_translate_ui_text("Cancel", language))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _update_artwork_preview(self, *_args: Any) -> None:
        if getattr(self, "_prefilling", False):
            return
        self.artwork_preview.setPixmap(vehicle_pixmap(
            self.make.currentText(), self.model.currentText(), self.chassis.currentText(), 270, 144
        ))

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
            year=int(self.year.currentText()) if self.year.currentText().isdigit() and int(self.year.currentText()) > 0 else None,
        )
        engines = sorted({row["engine"] for row in rows})
        self._set_combo(self.engine, engines, "M272 E35 3.5" if "M272 E35 3.5" in engines else (engines[0] if engines else None))
        self._refresh_ecus()

    def _refresh_ecus(self, *_args: Any) -> None:
        rows = self._items(
            make=self.make.currentText(),
            model=self.model.currentText(),
            chassis=self.chassis.currentText(),
            year=int(self.year.currentText()) if self.year.currentText().isdigit() and int(self.year.currentText()) > 0 else None,
            engine=self.engine.currentText(),
        )
        ecus = sorted({row["ecu"] for row in rows if row.get("ecu")})
        self._set_combo(self.ecu, ecus, "ME9.7" if "ME9.7" in ecus else (ecus[0] if ecus else None))

    def set_vehicle(self, vehicle: Vehicle) -> None:
        self.setWindowTitle(_translate_ui_text("Edit vehicle", getattr(self.parent(), "language", "en")))
        # Include custom saved profiles as well as current catalog entries.
        row = vehicle.to_json()
        self._catalog.append({key: row.get(key) or (0 if key == "year" else "") for key in ("make", "model", "chassis", "year", "engine", "ecu")})
        self._prefilling = True
        try:
            self._refresh_makes()
            for field in ("make", "model", "chassis", "year", "engine", "ecu"):
                combo = getattr(self, field)
                value = str(getattr(vehicle, field) or (0 if field == "year" else ""))
                if combo.findText(value) < 0:
                    combo.addItem(value)
                combo.setCurrentText(value)
            self.fuel.setText(",".join(vehicle.fuel))
        finally:
            self._prefilling = False
        self._update_artwork_preview()

    def vehicle(self) -> Vehicle:
        return Vehicle(
            self.make.currentText().strip(),
            self.model.currentText().strip(),
            self.chassis.currentText().strip(),
            int(self.year.currentText()) if self.year.currentText().isdigit() and int(self.year.currentText()) > 0 else None,
            self.engine.currentText().strip(),
            [x.strip() for x in self.fuel.text().split(",") if x.strip()],
            self.ecu.currentText().strip(),
        )

class DashboardPage(DemoDashboard):
    pass

class VehiclesPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); bar=QHBoxLayout(); add=QPushButton("+ Add vehicle"); add.clicked.connect(app.add_vehicle); bar.addWidget(add); self.delete_btn=QPushButton("Delete selected"); self.delete_btn.clicked.connect(app.delete_selected_vehicle); self.delete_btn.setEnabled(False); bar.addWidget(self.delete_btn); self.edit_btn=QPushButton("Edit vehicle"); self.edit_btn.clicked.connect(lambda: app.edit_selected_vehicle()); self.edit_btn.setEnabled(False); bar.addWidget(self.edit_btn); bar.addStretch(); lay.addLayout(bar)
        self.model_artwork = QLabel()
        self.model_artwork.setAlignment(Qt.AlignCenter)
        self.model_artwork.setMaximumHeight(185)
        lay.addWidget(self.model_artwork)
        split=QSplitter(); self.list=QListWidget(); self.list.setIconSize(QSize(112,56)); self.details=QPlainTextEdit(); self.details.setObjectName("vehicleDetails"); self.details.setReadOnly(True); split.addWidget(self.list); split.addWidget(self.details); split.setSizes([360,700]); lay.addWidget(split)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search vehicle")
        lay.insertWidget(1, self.search)
        self.search.textChanged.connect(lambda text: [self.list.item(i).setHidden(text.casefold() not in self.list.item(i).text().casefold()) for i in range(self.list.count())])
        self.list.itemSelectionChanged.connect(self.show_selected)
    def refresh(self):
        signature = tuple(tuple(str(value) for value in v.to_json().values()) for v in self.app.vehicles)
        if signature == getattr(self, "_vehicle_signature", None):
            return
        self._vehicle_signature = signature
        selected = self.list.currentRow()
        self.list.clear()
        for idx,v in enumerate(self.app.vehicles):
            item=QListWidgetItem(f"{v.make} {v.model} ({v.year or '—'})"); item.setData(Qt.UserRole, idx); item.setIcon(QIcon(vehicle_pixmap(v.make,v.model,v.chassis,112,56))); self.list.addItem(item)
        self.search.textChanged.emit(self.search.text())
        self.delete_btn.setEnabled(bool(self.app.vehicles))
        if self.app.vehicles:
            self.list.setCurrentRow(max(0, min(selected, len(self.app.vehicles)-1)))
        elif self.app.active_vehicle:
            self.show_vehicle(self.app.active_vehicle)
        else:
            self.details.clear()
            self.model_artwork.clear()
    def show_selected(self):
        items=self.list.selectedItems()
        self.delete_btn.setEnabled(bool(items))
        self.edit_btn.setEnabled(bool(items))
        if not items: return
        v=self.app.vehicles[items[0].data(Qt.UserRole)]; self.show_vehicle(v)
    def show_vehicle(self,v:Vehicle):
        self.model_artwork.setPixmap(vehicle_pixmap(v.make, v.model, v.chassis, 340, 175))
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
        self.lbl.setText(f"Session state: {self.app.session.state}")
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
        self.cards=QGridLayout(); lay.addLayout(self.cards); self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(["PID / Channel","Count","Min","Max","Mean","Events"]); self.table.horizontalHeader().setStretchLastSection(True); lay.addWidget(self.table); self.chart=Sparkline(); self.chart.setMaximumHeight(110); lay.addWidget(self.chart); self.signals=SignalGrid(app.settings_store,prefix="live"); lay.addWidget(self.signals)
        self.ai_box=QPlainTextEdit(); self.ai_box.setReadOnly(True); self.ai_box.setPlaceholderText("AI live-data interpretation will appear here..."); self.ai_box.setMaximumHeight(240); lay.addWidget(self.ai_box)
        self.timer=QTimer(self); self.timer.setInterval(2500); self.timer.timeout.connect(self._poll)
        self._poll_in_flight = False
        self._details_in_flight = False
        self._status_data = {}
        self._provider_data = {"available": False, "model": "local"}
        self._records_data = []

    def request_refresh(self):
        if not self.app.session or not self.app.online or self._details_in_flight:
            return
        self._details_in_flight = True
        session_id = self.app.session.session_id

        def load():
            result = {}
            for key, call in (
                ("status", lambda: self.app.api.acquisition_status(session_id)),
                ("provider", self.app.api.ai_provider_info),
                ("records", lambda: self.app.api.acquisition_records(session_id)),
            ):
                try:
                    result[key] = call()
                except Exception as exc:
                    result[key] = {"_error": str(exc)}
            return result

        def loaded(data):
            self._details_in_flight = False
            if self.app.session and self.app.session.session_id == session_id:
                self._details_loaded(data)
        self.app.run_worker(load, loaded)

    def _details_loaded(self, data):
        self._details_in_flight = False
        self._status_data = data.get("status", {})
        self._provider_data = data.get("provider", {})
        self._records_data = self._records_data_from(data.get("records", {}))
        status = self._status_data
        if not status.get("_error"):
            state = status.get("state", "STOPPED")
            self.status.setText("RUNNING" if state == "RUNNING" else state)
            if state == "RUNNING" and not self.timer.isActive():
                self.timer.start()
            elif state != "RUNNING":
                self.timer.stop()
        provider = self._provider_data
        if provider and not provider.get("_error"):
            available = bool(provider.get("available"))
            model = provider.get("model", "—")
            reason = provider.get("reason")
            self.ai_status.setText(f"AI: {'READY' if available else 'OFFLINE'} • {model}" + (f" • {reason}" if reason and not available else ""))
            self.ai_status.setObjectName("ok" if available else "warn")
            self.ai_status.style().unpolish(self.ai_status)
            self.ai_status.style().polish(self.ai_status)
        elif provider.get("_error"):
            self.ai_status.setText("AI: unavailable")
        self.refresh()

    @staticmethod
    def _records_data_from(payload):
        if isinstance(payload, dict):
            return payload.get("records", [])
        return []

    def _poll(self):
        if not self.app.session or not self.app.online or self._poll_in_flight:
            return
        self._poll_in_flight = True
        session_id = self.app.session.session_id

        def load_status():
            try:
                return self.app.api.acquisition_status(session_id)
            except Exception as exc:
                return {"_error": str(exc)}

        self.app.run_worker(load_status, self._poll_done)

    def _poll_done(self, status):
        self._poll_in_flight = False
        if status.get("_error"):
            self.status.setText("Backend unavailable")
            self.timer.stop()
            return
        state = status.get("state", "STOPPED")
        self.status.setText("RUNNING" if state == "RUNNING" else state)
        if state == "RUNNING":
            self.app.refresh_telemetry()
        else:
            self.timer.stop()

    def refresh(self):
        if not self.app.session:
            self.timer.stop()
            self.status.setText("STOPPED")
            self.table.setRowCount(0)
            self.chart.set_values([])
            return
        if self._status_data.get("_error"):
            self.status.setText("Backend unavailable")
        else:
            state = self._status_data.get("state", "STOPPED")
            self.status.setText("RUNNING" if state == "RUNNING" else state)
        provider = self._provider_data
        available = bool(provider.get("available"))
        model = provider.get("model", "—")
        if provider.get("_error"):
            self.ai_status.setText("AI: unavailable")
        else:
            self.ai_status.setText(f"AI: {'READY' if available else 'OFFLINE'} • {model}")
        self.ai_status.setObjectName("ok" if available and not provider.get("_error") else "warn")
        self.ai_status.style().unpolish(self.ai_status)
        self.ai_status.style().polish(self.ai_status)
        summary = self.app.telemetry
        stats = summary.get("signals") or summary.get("stats") or []
        self.table.setRowCount(0)
        for st in stats:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [st.get("pid", ""), st.get("count", 0), st.get("min_value", "—"), st.get("max_value", "—"), st.get("mean", "—"), st.get("event_count", 0)]
            for column, value in enumerate(vals):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        values = [float(record["numeric_value"]) for record in self._records_data if record.get("numeric_value") is not None]
        first_pid = next(((r.get("pid") or r.get("channel")) for r in self._records_data if r.get("numeric_value") is not None), None)
        values = [float(r["numeric_value"]) for r in self._records_data if r.get("numeric_value") is not None and (r.get("pid") or r.get("channel")) == first_pid]
        self.chart.set_values(values)
        self.signals.set_records(self._records_data)

class TestsPage(QWidget):
    def __init__(self, app: "MainWindow") -> None:
        super().__init__(); self.app=app
        lay=QVBoxLayout(self); title=QLabel("Guided Tests"); title.setObjectName("title"); title.setMaximumHeight(42); lay.addWidget(title)
        self.progress=QProgressBar(); self.progress.setFixedHeight(18); lay.addWidget(self.progress)
        self.list=QListWidget(); self.instructions=QPlainTextEdit(); self.instructions.setReadOnly(True); self.instructions.setPlaceholderText("Select a recommended test to view prerequisites and safety notes")
        split=QSplitter(); split.addWidget(self.list); split.addWidget(self.instructions); lay.addWidget(split,1)
        self.list.itemSelectionChanged.connect(self._show_instructions)
        outcomes=QHBoxLayout()
        for code, color in [("PASS", "#17B884"),("FAIL", "#E24C65"),("INCOMPLETE", "#CE9E31")]:
            button=QPushButton(code); button.setStyleSheet(f"border: 1px solid {color}; color: {color}; padding: 18px;")
            button.clicked.connect(lambda _=False, value=code:self._record_outcome(value)); outcomes.addWidget(button)
        lay.addLayout(outcomes)
        bar=QHBoxLayout(); language = getattr(app, "language", "en")
        self.result=QComboBox(); self.result.addItem(_translate_ui_text("PASS", language), "PASS"); self.result.addItem(_translate_ui_text("FAIL", language), "FAIL"); self.result.addItem(_translate_ui_text("INCOMPLETE", language), "INCOMPLETE"); self.result.setCurrentIndex(2); self.notes=QLineEdit(); self.notes.setPlaceholderText("Technician notes / measurements"); submit=QPushButton("Record selected result"); submit.clicked.connect(app.record_selected_test); bar.addWidget(self.result); bar.addWidget(self.notes); bar.addWidget(submit); lay.addLayout(bar)
    def _record_outcome(self, value):
        self.result.setCurrentIndex(self.result.findData(value))
        self.app.record_selected_test()

    def _show_instructions(self):
        selected=self.list.currentItem()
        if selected is None:
            self.instructions.clear(); return
        data=next((x for x in self.app.decision.get("candidates",[]) if str(x.get("test_id") or x.get("id")) == selected.data(Qt.UserRole)), {})
        lines=[data.get("name",""), data.get("purpose",""), ""]
        lines += [f"{i+1}. {step}" for i,step in enumerate(data.get("prerequisites",[]))]
        lines += ["", data.get("expected_observation") or "", ""] + data.get("safety_notes",[])
        self.instructions.setPlainText("\n".join(lines))

    def refresh(self):
        latest = {str(x.get("test_id")): x.get("result") for x in self.app.session_json.get("test_results", [])}
        completed = {tid for tid, result in latest.items() if result in {"PASS", "FAIL"}}
        current = {str(x.get("test_id") or x.get("id")) for x in self.app.decision.get("candidates", [])}
        total = len(current | latest.keys())
        done = len(completed)
        self.progress.setRange(0,max(1,total)); self.progress.setValue(done); self.progress.setFormat(f"{done}/{total}")
        candidates = self.app.decision.get("candidates", [])
        signature = json.dumps(candidates, sort_keys=True, ensure_ascii=False)
        if signature == getattr(self, "_candidate_signature", None):
            return
        self._candidate_signature = signature
        previous = self.list.currentItem()
        selected = previous.data(Qt.UserRole) if previous else None
        self.list.clear(); self.app.test_candidates=[]
        for item in candidates:
            c=TestCandidate.from_json(item); self.app.test_candidates.append(c)
            label=f"{c.priority_score:.2f} • {c.name} • risk={c.risk_level}\n{c.purpose}"
            q=QListWidgetItem(label); q.setData(Qt.UserRole,c.test_id); self.list.addItem(q)
        if self.list.count():
            row = next((i for i in range(self.list.count()) if self.list.item(i).data(Qt.UserRole) == selected), 0)
            self.list.setCurrentRow(row)

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
            status=_translate_ui_text(d.get("status","disconnected").upper(), getattr(self.app,"language","en"))
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
        self._vehicle_catalog = []
        self._catalog_pending = False
        self._catalog_loaded_at = 0.0
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
        # Workers own real HTTP operations, which can outlive a window close.
        # Never destroy a running QThread during Qt interpreter teardown.
        self._workers: list[Worker] = []
        self._closing = False
        self.stack = QStackedWidget()
        self.pages = []
        self._build_pages()
        self._build_menu()
        self.setCentralWidget(self.stack)
        self.statusBar().showMessage(self.tr_text("Ready"))
        self.refresh_all()

    def _apply_theme(self) -> None:
        if getattr(self, "_rendered_theme", None) == self.dark_theme:
            return
        self.setUpdatesEnabled(False)
        try:
            self.setStyleSheet(APP_QSS if self.dark_theme else APP_QSS_LIGHT)
            self._rendered_theme = self.dark_theme
        finally:
            self.setUpdatesEnabled(True)

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
            dialog.deleteLater()
            return
        old_language, old_theme = self.language, self.dark_theme
        self.language = str(language.currentData())
        self.dark_theme = bool(theme.currentData())
        self.settings_store.setValue("language", self.language)
        self.settings_store.setValue("dark_theme", self.dark_theme)
        if old_theme != self.dark_theme:
            self._apply_theme()
        if old_language != self.language:
            self._apply_language()
            self.refresh_pages()
            self._refresh_response_language()
        dialog.deleteLater()
        self.statusBar().showMessage(self.tr_text("Settings saved") + " • " + self.tr_text("Language") + "=" + self.language + " • " + self.tr_text("Theme") + "=" + self.tr_text("Dark" if self.dark_theme else "Light"))

    def tr_text(self, text: str) -> str:
        return _translate_ui_text(text, self.language)

    def _apply_language(self) -> None:
        self.setWindowTitle(self.tr_text("AI Auto Diagnostic Workstation"))
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QLabel):
                if widget.objectName() != "vehicleMetricValue" and widget.text():
                    translated = self.tr_text(widget.text())
                    if translated != widget.text(): widget.setText(translated)
            elif isinstance(widget, QPushButton):
                translated = self.tr_text(widget.text())
                if translated != widget.text(): widget.setText(translated)
            elif isinstance(widget, QGroupBox):
                widget.setTitle(self.tr_text(widget.title()))
            elif isinstance(widget, QLineEdit):
                widget.setPlaceholderText(self.tr_text(widget.placeholderText()))
            elif isinstance(widget, QPlainTextEdit):
                widget.setPlaceholderText(self.tr_text(widget.placeholderText()))
                if widget.isReadOnly():
                    translated = _translate_ui_block(widget.toPlainText(), self.language)
                    if translated != widget.toPlainText(): widget.setPlainText(translated)
            elif isinstance(widget, QListWidget):
                # Vehicle/device lists contain user or hardware names; translate only presentation lists.
                if widget is self.nav or widget in [self.pages[i].list for i in (6, 7, 8) if len(self.pages) > i]:
                    for index in range(widget.count()):
                        item = widget.item(index)
                        item.setText(self.tr_text(item.text()))
            elif isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    text = self.tr_text(widget.itemText(index))
                    if text != widget.itemText(index):
                        widget.blockSignals(True)
                        widget.setItemText(index, text)
                        widget.blockSignals(False)
            elif isinstance(widget, QTableWidget):
                for column in range(widget.columnCount()):
                    item = widget.horizontalHeaderItem(column)
                    if item:
                        item.setText(self.tr_text(item.text()))
        for trace in self.findChildren(QWidget):
            if hasattr(trace, "empty_text"):
                trace.empty_text = self.tr_text("No samples")
                trace.update()
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
        container=QWidget(); shell=QVBoxLayout(container); shell.setContentsMargins(16,12,16,12); shell.setSpacing(14)
        header=QHBoxLayout(); brand=QVBoxLayout(); name=QLabel("AI CAR SCANNER"); name.setObjectName("heroTitle"); brand.addWidget(name)
        subtitle=QLabel("SMART DIAGNOSTICS  •  AI ANALYSIS  •  BETTER DRIVING"); subtitle.setObjectName("heroSubtitle"); subtitle.setWordWrap(True); brand.addWidget(subtitle); header.addLayout(brand,2)
        header_nav=QWidget(); header_buttons=QHBoxLayout(header_nav); header_buttons.setContentsMargins(0,0,0,0)
        for title, target in [("⚙  Diagnostics",3),("◈  AI Analysis",8),("▥  Live Data",4),("✓  Guided Tests",6),("▤  Reports",9),("✧  Teach AI",10)]:
            button=QPushButton(title); button.setObjectName("topNav"); button.clicked.connect(lambda _=False, index=target:self.nav.setCurrentRow(index)); header_buttons.addWidget(button)
        header_scroll=QScrollArea(); header_scroll.setWidgetResizable(True); header_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); header_scroll.setFixedHeight(82); header_scroll.setWidget(header_nav); header.addWidget(header_scroll,3)
        settings=QPushButton("⚙"); settings.setAccessibleName("Settings"); settings.clicked.connect(self._open_settings); header.addWidget(settings); shell.addLayout(header)
        root=QHBoxLayout(); shell.addLayout(root,1)
        nav=QListWidget(); nav.setObjectName("sideNav"); nav.setFixedWidth(195); entries=[("◉  Dashboard",DashboardPage), ("▣  Vehicles",VehiclesPage), ("🔌  VCI / Devices",DevicesPage), ("⚙  Diagnostic",DiagnosticPage), ("◌  Live Data",LiveDataPage), ("⌘  ECU Network",NetworkPage), ("✓  Tests",TestsPage), ("⚠  DTC", DTCPage), ("◈  AI Analysis", HypothesesPage), ("▤  Reports", ReportsPage), ("✧  Teach AI", TeachPage)]
        self.nav=nav
        for text,_cls in entries: nav.addItem(text)
        root.addWidget(nav)
        content=QStackedWidget(); root.addWidget(content,1)
        for _text, cls in entries:
            page=cls(self); self.pages.append(page); scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.NoFrame); scroll.setWidget(page); content.addWidget(scroll)
        nav.currentRowChanged.connect(content.setCurrentIndex)
        nav.currentRowChanged.connect(lambda index: self.pages[4].request_refresh() if index == 4 else None)
        nav.currentRowChanged.connect(lambda index: self.pages[9].load() if index == 9 and self.online else None)
        nav.setCurrentRow(0)
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
    def run_worker(self, fn: Callable[[], Any], done: Callable[[Any], None]) -> None:
        if self._closing:
            return
        worker = Worker(fn)
        self._workers.append(worker)
        # Suppress late GUI mutations and modal error dialogs once closing.
        worker.finished_ok.connect(
            lambda result: done(result) if not self._closing else None
        )
        worker.failed.connect(
            lambda message: self.show_error(message) if not self._closing else None
        )
        # Use a QObject receiver on the GUI thread, not a closure that removes
        # the final strong reference while QThread is still finishing.
        worker.finished.connect(self._on_worker_finished)
        worker.start()

    @Slot()
    def _on_worker_finished(self) -> None:
        worker = self.sender()
        if worker in self._workers:
            # Qt emits finished immediately before native thread teardown.
            # Synchronize only at this already-finished boundary to avoid
            # QThread: Destroyed while thread is still running.
            worker.wait()
            self._workers.remove(worker)
            worker.deleteLater()
        _trace_shutdown(f"worker.finished: remaining={len(self._workers)}")
        if self._closing and not self._workers:
            # Process the final finished signal before invoking closeEvent again.
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event) -> None:
        _trace_shutdown(f"closeEvent: active_workers={len(self._workers)}")
        if self._workers:
            if not self._closing:
                self._closing = True
                for page in self.pages:
                    timer = getattr(page, "timer", None)
                    if isinstance(timer, QTimer):
                        timer.stop()
                for worker in self._workers:
                    worker.requestInterruption()
                self.statusBar().showMessage(
                    self.tr_text("Finishing active requests before closing...")
                )
                self.setEnabled(False)
            # Abort this close event; requests may be blocking on a bounded
            # network timeout. Do not call terminate() or wait() on the UI thread.
            event.ignore()
            return
        super().closeEvent(event)

    def show_error(self,msg:str):
        translated = self.tr_text(msg)
        QMessageBox.critical(self, self.tr_text("Error"), translated)
        self.statusBar().showMessage(translated)
    def refresh_health(self):
        def done(data): self.online=data.get("status")=="ok"; self.statusBar().showMessage(self.tr_text("Backend online" if self.online else "Backend offline")); self.refresh_pages()
        self.run_worker(self.api.health,done)
    def refresh_catalog(self):
        if self._catalog_pending or time.monotonic() - self._catalog_loaded_at < 60:
            return
        self._catalog_pending = True
        def load():
            try: return self.api.vehicle_catalog_entries()
            except Exception: return None
        def loaded(rows):
            self._catalog_pending = False
            if isinstance(rows, list):
                self._vehicle_catalog = rows
                self._catalog_loaded_at = time.monotonic()
        self.run_worker(load, loaded)

    def refresh_all(self): self.refresh_health(); self.refresh_devices(); self.refresh_catalog(); self.refresh_pages()
    def refresh_pages(self):
        for p in self.pages:
            try: p.refresh()
            except Exception: pass
        self._apply_language()
    def add_vehicle(self):
        dialog = VehicleDialog(self)
        try:
            if dialog.exec() != QDialog.Accepted:
                return
            vehicle = dialog.vehicle()
        finally:
            getattr(dialog, "deleteLater", lambda: None)()
        self.vehicles = [v for v in self.vehicles if not (v.make == vehicle.make and v.model == vehicle.model and v.year == vehicle.year and v.engine == vehicle.engine)]
        self.vehicles.append(vehicle)
        self.store.save(self.vehicles)
        self.active_vehicle = vehicle
        self.pages[1].refresh()
        self.new_session()

    def edit_selected_vehicle(self):
        item = self.pages[1].list.currentItem()
        if item is None:
            self.show_error("Select a vehicle first.")
            return
        index = int(item.data(Qt.UserRole))
        original = self.vehicles[index]
        active = self.active_vehicle is original or self.active_vehicle == original
        if active and self.session and not self.online:
            self.show_error("Reconnect the backend before editing the active session vehicle.")
            return
        dialog = VehicleDialog(self)
        dialog.set_vehicle(original)
        try:
            if dialog.exec() != QDialog.Accepted:
                return
            vehicle = dialog.vehicle()
        finally:
            dialog.deleteLater()
        def save():
            position = next((i for i, item in enumerate(self.vehicles) if item is original), None)
            if position is not None:
                self.vehicles[position] = vehicle
                self.store.save(self.vehicles)
            if self.active_vehicle is original or self.active_vehicle == original:
                self.active_vehicle = vehicle
            self.refresh_pages()
        if active and self.session:
            sid, language = self.session.session_id, self.language
            def work():
                self.api.update_vehicle(sid, vehicle.to_json())
                return {"session": self.api.analyze(sid, language=language), "decision": self.api.decision_plan(sid, language=language)}
            def done(data):
                # Save the edited local profile even if another session was opened.
                save()
                if self.session and self.session.session_id == sid:
                    self.session = Session(sid, str(data["session"].get("state", "")), vehicle)
                    self.session_json = data["session"]
                    self.decision = data["decision"]
                    self.refresh_pages()
            self.run_worker(work, done)
        else:
            save()

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
        self.statusBar().showMessage(self.tr_text(f"Vehicle deleted: {label}"))
    def refresh_devices(self):
        self.run_worker(self.api.list_devices, lambda data: self._devices_done(data.get("devices", [])))

    def _devices_done(self, devices):
        self.devices=devices; self.refresh_pages(); self.statusBar().showMessage(self.tr_text(f"VCI devices: {len(devices)}"))

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
        self.refresh_pages(); self.statusBar().showMessage(self.tr_text(message))

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
        self.session=Session(str(data.get("session_id")),str(data.get("state","CREATED")),self.active_vehicle); self.session_json=data; self.decision={}; self.telemetry={}; self.network={}; self.active_network={}; self.nav.setCurrentRow(3); self.refresh_pages(); self.statusBar().showMessage(self.tr_text("Diagnostic session created"))
    def analyze_input(self):
        if not self.session: self.new_session(); return
        text=self.pages[3].symptom.toPlainText().strip(); dtc=self.pages[3].dtc.text().strip()
        if not text and not dtc: self.show_error("Enter a symptom, observation or DTC."); return
        def work():
            if text: self.api.ingest_evidence(self.session.session_id,text)
            if dtc: self.api.add_dtc(self.session.session_id,dtc)
            return self.api.analyze(self.session.session_id, language=self.language)
        self.run_worker(work,self._analysis_done)
    def _analysis_done(self,data): self.session_json=data; self.session=Session(str(data.get("session_id")),str(data.get("state","")),self.active_vehicle); self.run_worker(lambda:self.api.decision_plan(self.session.session_id, language=self.language),self._decision_done)
    def _decision_done(self,data): self.decision=data; self.nav.setCurrentRow(3); self.refresh_pages(); self.statusBar().showMessage(self.tr_text("Diagnostic reasoning updated"))
    def start_simulator(self):
        if not self.session: self.new_session(); return
        self.run_worker(lambda:self.api.start_simulator(self.session.session_id),lambda _d:self._sim_changed("Simulator acquisition started"))
    def stop_simulator(self):
        if not self.session: return
        self.run_worker(lambda:self.api.stop_acquisition(self.session.session_id),lambda _d:self._sim_changed("Acquisition stopped"))
    def _sim_changed(self,msg): self.statusBar().showMessage(self.tr_text(msg)); self.refresh_telemetry()
    def refresh_telemetry(self):
        if not self.session or getattr(self, "_telemetry_refresh_in_flight", False):
            return

        session_id = self.session.session_id
        self._telemetry_refresh_in_flight = True

        def work():
            try:
                return {
                    "summary": self.api.telemetry_summary(session_id),
                    "records": self.api.acquisition_records(session_id),
                }
            except Exception as exc:
                return {"_error": str(exc)}

        def done(data):
            self._telemetry_refresh_in_flight = False
            if data.get("_error"):
                self.statusBar().showMessage(self.tr_text(f"Live-data refresh failed: {data['_error']}"))
                return
            # A request for a previous session must not overwrite the current session's UI.
            if not self.session or self.session.session_id != session_id:
                return
            self.telemetry = data["summary"]
            self.pages[4]._records_data = LiveDataPage._records_data_from(data.get("records", {}))
            self.pages[0].refresh()
            self.refresh_pages()

        self.run_worker(work, done)
    def analyze_telemetry(self):
        if not self.session: return
        self.run_worker(lambda:self.api.analyze_telemetry(self.session.session_id),lambda data:self._telemetry_done(data))
    def _telemetry_done(self,data): self.telemetry=data; self.refresh_pages(); self.statusBar().showMessage(self.tr_text("Telemetry analysis completed"))
    def ai_analyze_live_data(self):
        if not self.session:
            self.show_error("Create a diagnostic session first."); return
        self.statusBar().showMessage(self.tr_text("AI is analyzing live vehicle data..."))
        sid, language = self.session.session_id, self.language
        def done(data):
            if self.session and self.session.session_id == sid and self.language == language:
                self._live_ai_done(data)
        self.run_worker(lambda:self.api.ai_analyze_live_data(sid, language=language), done)

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
        self.statusBar().showMessage(self.tr_text("Live-data AI analysis completed"))
    def refresh_network(self):
        if not self.session: return
        self.run_worker(lambda:self.api.network_map(self.session.session_id),lambda data:self._network_done(data))
    def _network_done(self,data): self.network=data; self.refresh_pages(); self.statusBar().showMessage(self.tr_text("Network map refreshed"))
    def active_probe(self):
        if not self.session: return
        ids=[str(x.get("id") or x.get("ecu_id")) for x in self.network.get("ecus",[]) if x.get("id") or x.get("ecu_id")]
        self.run_worker(lambda:self.api.active_probe(self.session.session_id,ids or None),lambda data:self._active_done(data))
    def _active_done(self,data): self.active_network=data; self.refresh_pages(); self.statusBar().showMessage(self.tr_text("Active read-only ECU probe completed"))
    def _refresh_response_language(self):
        if not self.session or not self.online:
            return
        sid, language = self.session.session_id, self.language
        self.pages[4].ai_box.clear()
        def work():
            return {"session": self.api.get_session(sid, language=language), "decision": self.api.decision_plan(sid, language=language)}
        def done(data):
            if self.session and self.session.session_id == sid and self.language == language:
                self.session_json = data["session"]
                self.decision = data["decision"]
                self.refresh_pages()
        self.run_worker(work, done)

    def record_selected_test(self):
        if not self.session: self.show_error("No active session."); return
        page = self.pages[6]
        item = page.list.currentItem()
        if not item: self.show_error("Select a diagnostic test first."); return
        sid, language = self.session.session_id, self.language
        tid = str(item.data(Qt.UserRole))
        result = str(page.result.currentData() or page.result.currentText())
        notes = page.notes.text().strip()
        def work():
            # The result endpoint already recalculates probabilities and recommendations.
            session = self.api.record_test_result(sid, tid, result, notes=notes, language=language)
            return {"session": session, "decision": self.api.decision_plan(sid, language=language)}
        def done(data):
            if not self.session or self.session.session_id != sid:
                return
            self.session_json = data["session"]
            self.session = Session(sid, str(self.session_json.get("state", "")), self.active_vehicle)
            self.decision = data["decision"]
            page.notes.clear()
            page.result.setCurrentIndex(page.result.findData("INCOMPLETE"))
            self.refresh_pages()
            self.statusBar().showMessage(self.tr_text("Diagnostic reasoning updated"))
            if self.language != language:
                self._refresh_response_language()
        self.run_worker(work, done)


def _resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parents[2]
    return base / relative


def _set_windows_taskbar_icon(hwnd: int, icon: QIcon) -> None:
    """Set native Windows window icons without allowing icon failures to crash startup."""
    if sys.platform != "win32" or icon.isNull():
        return

    import ctypes
    from ctypes import wintypes

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class RGBQUAD(ctypes.Structure):
        _fields_ = [
            ("rgbBlue", ctypes.c_ubyte), ("rgbGreen", ctypes.c_ubyte),
            ("rgbRed", ctypes.c_ubyte), ("rgbReserved", ctypes.c_ubyte),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", RGBQUAD * 1)]

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD),
            ("yHotspot", wintypes.DWORD), ("hbmMask", wintypes.HBITMAP),
            ("hbmColor", wintypes.HBITMAP),
        ]

    color_bitmap = mask_bitmap = native_icon = None
    gdi32, user32 = ctypes.windll.gdi32, ctypes.windll.user32
    try:
        image = icon.pixmap(64, 64).toImage().convertToFormat(QImage.Format.Format_ARGB32)
        width, height = image.width(), image.height()
        if width <= 0 or height <= 0:
            return

        # Windows expects a top-down 32-bit DIB in BGRA byte order.
        info = BITMAPINFO()
        info.bmiHeader = BITMAPINFOHEADER(
            ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0,
            image.sizeInBytes(), 0, 0, 0, 0
        )
        gdi32.CreateDIBSection.restype = wintypes.HBITMAP
        gdi32.CreateDIBSection.argtypes = [
            wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
            ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD
        ]
        gdi32.CreateBitmap.restype = wintypes.HBITMAP
        gdi32.CreateBitmap.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p
        ]
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        user32.CreateIconIndirect.restype = wintypes.HICON
        user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
        user32.SendMessageW.argtypes = [
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        ]
        user32.DestroyIcon.argtypes = [wintypes.HICON]

        bits = ctypes.c_void_p()
        color_bitmap = gdi32.CreateDIBSection(
            None, ctypes.byref(info), 0, ctypes.byref(bits), None, 0
        )
        if not color_bitmap or not bits.value:
            return
        pixel_bytes = bytes(image.bits())[:image.sizeInBytes()]
        ctypes.memmove(bits.value, pixel_bytes, len(pixel_bytes))
        mask_bitmap = gdi32.CreateBitmap(width, height, 1, 1, None)
        if not mask_bitmap:
            return

        icon_info = ICONINFO(True, 0, 0, mask_bitmap, color_bitmap)
        native_icon = user32.CreateIconIndirect(ctypes.byref(icon_info))
        if not native_icon:
            return

        # Keep the handle alive while Windows may still display the icon.
        _WINDOWS_TASKBAR_ICONS.append(native_icon)
        user32.SendMessageW(hwnd, 0x0080, 0, native_icon)  # WM_SETICON / ICON_SMALL
        user32.SendMessageW(hwnd, 0x0080, 1, native_icon)  # WM_SETICON / ICON_BIG
        native_icon = None  # Ownership retained until application shutdown.
    except Exception as exc:
        print(f"Windows taskbar icon fallback: {exc}", file=sys.stderr)
    finally:
        if native_icon:
            user32.DestroyIcon(native_icon)
        if color_bitmap:
            gdi32.DeleteObject(color_bitmap)
        if mask_bitmap:
            gdi32.DeleteObject(mask_bitmap)


def _trace_shutdown(stage: str) -> None:
    """Write durable checkpoints for frozen Windows teardown (opt-in)."""
    destination = os.environ.get("AI_CAR_SHUTDOWN_TRACE_PATH")
    if not destination:
        return
    try:
        with open(destination, "a", encoding="utf-8") as stream:
            stream.write(stage + "\n")
    except OSError:
        pass


_WINDOWS_TASKBAR_ICONS: list[int] = []


def run() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AI-CAR-SCANER.Desktop")
        except (AttributeError, OSError):
            pass

    # Runtime startup must not depend on Pillow. The tracked Desktop WEBP is
    # byte-identical to Android's launcher icon; ICO/PNG are fallbacks.
    app = QApplication([])
    app.setFont(QFont("Segoe UI", 10))
    app.setApplicationName("AI Auto Diagnostic Workstation")
    # Prefer PNG for Qt across Windows builds (WEBP requires an image plugin).
    # Both are generated from the same master; ICO is the last fallback.
    icon_candidates = (
        _resource_path("assets/AI-Car-Scanner-mobile.png"),
        _resource_path("assets/AI-Car-Scanner.webp"),
        _resource_path("assets/AI-Car-Scanner.ico"),
    )
    icon_path = next((candidate for candidate in icon_candidates if candidate.is_file()), None)
    app_icon = QIcon(str(icon_path)) if icon_path is not None else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    win = MainWindow()
    if not app_icon.isNull():
        win.setWindowIcon(app_icon)
    win._apply_language()
    # Ensure Windows creates a native top-level window and receives the same icon
    # through its QWindow handle as well as QWidget/QApplication. This helps the
    # taskbar use the app artwork instead of the python.exe process icon.
    if sys.platform == "win32":
        win.setAttribute(Qt.WA_NativeWindow, True)
    win.show()
    if not app_icon.isNull():
        win.setWindowIcon(app_icon)
        native_window = win.windowHandle()
        if native_window is not None:
            native_window.setIcon(app_icon)
        # The Qt/EXE icons work without this custom ctypes fallback. The
        # frozen Windows release defaults to Qt-managed icons until the
        # Win32 GDI fallback is independently validated; developers can opt in
        # with AI_CAR_DISABLE_NATIVE_TASKBAR_ICON=0 for comparison.
        native_icon_disabled = os.environ.get(
            "AI_CAR_DISABLE_NATIVE_TASKBAR_ICON",
            "1" if getattr(sys, "frozen", False) else "0",
        ) == "1"
        if sys.platform == "win32" and not native_icon_disabled:
            try:
                _set_windows_taskbar_icon(int(win.winId()), app_icon)
            except Exception as exc:
                print(f"Windows taskbar icon fallback: {exc}", file=sys.stderr)
    # Strictly opt-in packaged EXE smoke automation. This runs against the
    # actual frozen GUI and verifies the full Qt event loop and clean shutdown.
    # Normal desktop launches are unaffected when the env var is absent.
    smoke_delay = os.environ.get("AI_CAR_TEST_AUTOCLOSE_MS")
    if smoke_delay is not None and getattr(sys, "frozen", False):
        delay_ms = int(smoke_delay)
        if not 200 <= delay_ms <= 30000:
            raise ValueError("AI_CAR_TEST_AUTOCLOSE_MS must be 200..30000")
        _trace_shutdown("smoke: main_window_shown")
        QTimer.singleShot(delay_ms, win.close)

    app.aboutToQuit.connect(
        lambda: [
            __import__("ctypes").windll.user32.DestroyIcon(handle)
            for handle in _WINDOWS_TASKBAR_ICONS
        ] if sys.platform == "win32" else None
    )
    _trace_shutdown("ui: entering QApplication.exec")
    result = app.exec()
    _trace_shutdown(f"ui: QApplication.exec returned rc={result}, remaining_workers={len(win._workers) if hasattr(win, '_workers') else 'unknown'}")

    # Controlled experiment for packaged Windows interpreter/DLL teardown.
    # Do not force it on all users until a Windows debug run confirms exit 0.
    if (
        getattr(sys, "frozen", False)
        and sys.platform == "win32"
        and os.environ.get("AI_CAR_QT_EXPLICIT_CLEANUP", "0") == "1"
    ):
        _trace_shutdown("ui: explicit native widget cleanup start")
        # Ensure the Qt-owned windows and icon pixmaps are released before
        # PyInstaller unloads Python and the Qt platform/style plugins.
        win.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        _trace_shutdown("ui: explicit native widget cleanup done")

    _trace_shutdown("ui: returning to main.run")
    return result
