from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QTabWidget, QStatusBar, QMenuBar, QPushButton, 
                             QHBoxLayout)
from PyQt6.QtCore import Qt
from src.ui.dashboard_widget import DashboardWidget
from src.ui.settings_widget import SettingsWidget
from src.ui.series_wizard import SeriesWizard
from src.ui.series_management_widget import SeriesManagementWidget
from src.db.manager import DatabaseManager

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("BowlBets v2.0")
        self.resize(1300, 800)
        
        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 1. Dashboard Tab
        self.dashboard_tab = DashboardWidget(self.db_manager)
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # 2. Series Management Tab
        self.series_tab = SeriesManagementWidget(self.db_manager)
        self.series_tab.seriesSelected.connect(self.on_series_selected)
        self.series_tab.seriesCreated.connect(self._on_series_created)
        self.series_tab.seriesDeleted.connect(lambda _: self.dashboard_tab.refresh_sidebar())
        self.tabs.addTab(self.series_tab, "Series Management")
        
        # 3. Settings Tab
        self.settings_tab = SettingsWidget(self.db_manager)
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        
        self._create_menu_bar()

    def _launch_series_wizard(self):
        wizard = SeriesWizard(self.db_manager, self)
        wizard.seriesCreated.connect(self._on_series_created)
        wizard.exec()
        
    def _on_series_created(self, series_id):
        self.statusBar().showMessage(f"Series ID {series_id} created successfully!", 5000)
        # Refresh series tab if needed
        if hasattr(self.series_tab, 'load_series'):
            self.series_tab.load_series()
        
        # Refresh Dashboard Sidebar
        if hasattr(self.dashboard_tab, 'refresh_sidebar'):
            self.dashboard_tab.refresh_sidebar()
    
    def on_series_selected(self, series_id):
        """Handle series selection from Series Management tab."""
        self.statusBar().showMessage(f"Active series: ID {series_id}", 5000)
        # Update dashboard with active series
        if hasattr(self.dashboard_tab, 'set_active_series'):
            self.dashboard_tab.set_active_series(series_id)
        
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("E&xit", self.close)
        
        # View Menu
        view_menu = menu_bar.addMenu("&View")
        
        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
