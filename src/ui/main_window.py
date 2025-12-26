from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QTabWidget, QStatusBar, QMenuBar, QPushButton,
                             QHBoxLayout)
from PyQt6.QtCore import Qt
from src.ui.dashboard_widget import DashboardWidget
from src.ui.settings_widget import SettingsWidget
from src.ui.series_wizard import SeriesWizard
from src.ui.about_dialog import AboutDialog
from src.db.manager import DatabaseManager

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("BowlBets v2.0")
        self.resize(1300, 800)
        
        # Central Widget
        self.dashboard_widget = DashboardWidget(self.db_manager)
        self.setCentralWidget(self.dashboard_widget)
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        
        self._create_menu_bar()

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("Settings", self._open_settings)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)
        
        # Series Menu
        series_menu = menu_bar.addMenu("&Series")
        series_menu.addAction("New Series...", self._new_series)
        series_menu.addSeparator()
        series_menu.addAction("Import Series...", self._import_series)
        series_menu.addAction("Export Series...", self._export_series)
        
        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About BowlBets", self._show_about)

    def _open_settings(self):
        # This could be a dialog or a tab in a settings window
        self.settings_dialog = SettingsWidget(self.db_manager)
        self.settings_dialog.setWindowTitle("Settings")
        self.settings_dialog.show()

    def _new_series(self):
        self.dashboard_widget.create_new_series()

    def _import_series(self):
        self.dashboard_widget.import_series()

    def _export_series(self):
        self.dashboard_widget.export_series()

    def _show_about(self):
        """Show the About dialog with user guide."""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
