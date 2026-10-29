"""Shared presentation theme for all three clients and legacy screens."""
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
QGroupBox { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #12364D,stop:0.35 #0B2541,stop:1 #061626); border: 1px solid #1E6E95; border-top: 1px solid #35C8FF; border-radius: 14px; }
QGroupBox { margin-top: 15px; padding: 15px 12px 12px; font-weight: 650; }
QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 7px; color: #A9CFFF; }
QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #205477,stop:0.17 #0E355A,stop:1 #071B32); color: #EAF4FF; border: 1px solid #1973A4; border-top: 1px solid #35C8FF; border-radius: 9px; padding: 10px 15px; font-weight: 600; }
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
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0066BC,stop:1 #35C8FF); border-radius: 6px; }
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
