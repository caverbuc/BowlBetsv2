from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QMessageBox, QProgressBar)
from PyQt6.QtCore import QSettings, Qt
from src.db.manager import DatabaseManager
from src.logic.sync_engine import SyncManager

class SettingsWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.settings = QSettings("BowlBets", "BowlBetsV2")
        self.db_manager = db_manager
        self.sync_manager = SyncManager(db_manager)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        
        # API Keys Group
        api_group = QGroupBox("External API Keys")
        api_layout = QVBoxLayout()
        
        # CFD Key
        cfd_layout = QHBoxLayout()
        cfd_label = QLabel("CollegeFootballData API Key:")
        self.cfd_input = QLineEdit()
        self.cfd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.cfd_input.setText(self.settings.value("api_keys/cfd", ""))
        cfd_layout.addWidget(cfd_label)
        cfd_layout.addWidget(self.cfd_input)
        api_layout.addLayout(cfd_layout)
        
        # TheOdds Key
        odds_layout = QHBoxLayout()
        odds_label = QLabel("TheOddsAPI Key:")
        self.odds_input = QLineEdit()
        self.odds_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.odds_input.setText(self.settings.value("api_keys/theodds", ""))
        odds_layout.addWidget(odds_label)
        odds_layout.addWidget(self.odds_input)
        api_layout.addLayout(odds_layout)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Save Button
        save_btn = QPushButton("Save Keys")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        
        # Data Management Group
        data_group = QGroupBox("Data Synchronization")
        data_layout = QVBoxLayout()
        
        self.sync_btn = QPushButton("Sync Data Now")
        self.sync_btn.clicked.connect(self._start_sync)
        data_layout.addWidget(self.sync_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate
        data_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        data_layout.addWidget(self.status_label)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        layout.addStretch()
        self.setLayout(layout)

    def _save_settings(self):
        self.settings.setValue("api_keys/cfd", self.cfd_input.text())
        self.settings.setValue("api_keys/theodds", self.odds_input.text())
        self.settings.sync()
        QMessageBox.information(self, "Settings Saved", "API Keys have been saved successfully.")

    def _start_sync(self):
        self.sync_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting sync...")
        
        self.sync_manager.start_sync(
            on_progress=self._on_sync_progress,
            on_finished=self._on_sync_finished
        )

    def _on_sync_progress(self, msg):
        self.status_label.setText(msg)

    def _on_sync_finished(self, success, msg):
        self.sync_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(msg)
        if success:
            QMessageBox.information(self, "Sync Complete", msg)
        else:
            QMessageBox.critical(self, "Sync Failed", msg)
