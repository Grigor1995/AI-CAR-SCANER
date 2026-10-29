"""Retain one QApplication until all native tests in this process have finished.

Function-local ownership can collect the C++ singleton while deferred widgets
still exist and crash a later unrelated network test during garbage collection.
"""
import os
import pytest

@pytest.fixture(scope='session', autouse=True)
def desktop_application_lifetime():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    application = QApplication.instance() or QApplication([])
    yield application
    application.closeAllWindows()
    application.processEvents()

@pytest.fixture(autouse=True)
def collect_native_wrappers_on_gui_thread(desktop_application_lifetime):
    yield
    # Cyclic Qt wrappers must be reclaimed here, not by a later HTTP daemon
    # thread that happens to trigger Python's cyclic collector.
    import gc
    desktop_application_lifetime.processEvents()
    gc.collect()
    desktop_application_lifetime.processEvents()
