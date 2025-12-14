from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.db.manager import DatabaseManager
from src.db.repositories import BettingSeriesRepository, PersonRepository, SeasonRepository
from src.ui.series_wizard import SeriesWizard
from src.logic.import_export import SeriesTransferManager
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QHeaderView, QFileDialog)

class SeriesManagementWidget(QWidget):
    """
    Widget to manage betting series: list, select, edit, delete.
    """
    seriesSelected = pyqtSignal(int)  # Emits series_id when a series is selected
    seriesCreated = pyqtSignal(int)   # Emits series_id when a new series is created
    seriesDeleted = pyqtSignal(int)   # Emits series_id when a series is deleted
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.series_repo = BettingSeriesRepository(db_manager)
        self.person_repo = PersonRepository(db_manager)
        self.season_repo = SeasonRepository(db_manager)
        self.selected_series_id = None
        
        self._init_ui()
        self.load_series()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Betting Series Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Create New Series button
        new_btn = QPushButton("Create New Series")
        new_btn.clicked.connect(self.create_new_series)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # Series Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Season", "Person 1", "Person 2", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("Select Series for Betting")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.select_series)
        button_layout.addWidget(self.select_btn)
        
        self.edit_btn = QPushButton("Edit Series")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_series)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Series")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_series)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.export_btn = QPushButton("Export Selected")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_series_ui)
        button_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import Series")
        self.import_btn.clicked.connect(self.import_series_ui)
        button_layout.addWidget(self.import_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("No series selected")
        self.status_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_series(self):
        """Load all series from database and populate table."""
        self.table.setRowCount(0)
        
        # Get all series (we need to add a get_all method to BettingSeriesRepository)
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, season_id, person1_id, person2_id, name,
                   default_bet_amount_regular, default_bet_amount_cfp_semi, 
                   default_bet_amount_championship
            FROM BettingSeries
            ORDER BY id DESC
        """)
        
        series_list = cursor.fetchall()
        
        for row in series_list:
            series_id = row['id']
            season_id = row['season_id']
            person1_id = row['person1_id']
            person2_id = row['person2_id']
            name = row['name']
            
            # Get season info
            season = self.season_repo.get_by_id(season_id)
            season_name = season.display_name if season else f"Season {season_id}"
            
            # Get person names
            person1 = self.person_repo.get_by_id(person1_id)
            person2 = self.person_repo.get_by_id(person2_id)
            person1_name = person1.name if person1 else f"Person {person1_id}"
            person2_name = person2.name if person2 else f"Person {person2_id}"
            
            # Status (active if selected)
            status = "Active" if series_id == self.selected_series_id else "Inactive"
            
            # Add row to table
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            
            self.table.setItem(row_position, 0, QTableWidgetItem(str(series_id)))
            self.table.setItem(row_position, 1, QTableWidgetItem(name))
            self.table.setItem(row_position, 2, QTableWidgetItem(season_name))
            self.table.setItem(row_position, 3, QTableWidgetItem(person1_name))
            self.table.setItem(row_position, 4, QTableWidgetItem(person2_name))
            
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row_position, 5, status_item)
        
        if self.table.rowCount() == 0:
            self.status_label.setText("No series found. Create one to get started!")
        else:
            self.status_label.setText(f"Loaded {self.table.rowCount()} series")
    
    def on_selection_changed(self):
        """Enable/disable buttons based on selection."""
        has_selection = len(self.table.selectedItems()) > 0
        self.select_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
    
    def get_selected_series_id(self):
        """Get the ID of the currently selected row."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            return int(self.table.item(row, 0).text())
        return None
    
    def select_series(self):
        """Mark a series as active for betting."""
        series_id = self.get_selected_series_id()
        if series_id:
            self.selected_series_id = series_id
            self.seriesSelected.emit(series_id)
            
            # Get series name safely
            current_row = self.table.currentRow()
            if current_row >= 0:
                series_name_item = self.table.item(current_row, 1)
                series_name = series_name_item.text() if series_name_item else f"Series {series_id}"
            else:
                series_name = f"Series {series_id}"
            
            self.load_series()  # Refresh to update status
            self.status_label.setText(f"Active series: {series_name}")
            self.status_label.setStyleSheet("color: green; padding: 5px;")
    
    def edit_series(self):
        """Open wizard to edit selected series."""
        series_id = self.get_selected_series_id()
        if not series_id:
            return
        
        # Get series data from database
        series = self.series_repo.get_by_id(series_id)
        if not series:
            QMessageBox.warning(self, "Error", "Could not load series data.")
            return
        
        # Launch wizard with existing data
        wizard = SeriesWizard(self.db_manager, self, edit_mode=True, series_data=series)
        wizard.seriesCreated.connect(self.on_series_edited)
        wizard.exec()
    
    def on_series_edited(self, series_id):
        """Handle series edit completion."""
        self.load_series()
        self.status_label.setText(f"Updated series (ID: {series_id})")
        self.status_label.setStyleSheet("color: green; padding: 5px;")
    
    def delete_series(self):
        """Delete the selected series after confirmation."""
        series_id = self.get_selected_series_id()
        if not series_id:
            return
        
        series_name = self.table.item(self.table.currentRow(), 1).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{series_name}'?\n\n"
            "This will also delete all picks associated with this series.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete from database
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Delete picks first (foreign key constraint)
            cursor.execute("DELETE FROM Pick WHERE betting_series_id = ?", (series_id,))
            
            # Delete series
            cursor.execute("DELETE FROM BettingSeries WHERE id = ?", (series_id,))
            conn.commit()
            
            # Clear selection if deleted series was active
            if self.selected_series_id == series_id:
                self.selected_series_id = None
                self.status_label.setText("No series selected")
                self.status_label.setStyleSheet("color: gray; padding: 5px;")
            
            self.load_series()
            self.status_label.setText(f"Deleted series: {series_name}")
            self.status_label.setStyleSheet("color: orange; padding: 5px;")
            self.seriesDeleted.emit(series_id)
    
    def create_new_series(self):
        """Launch the Series Wizard to create a new series."""
        wizard = SeriesWizard(self.db_manager, self)
        wizard.seriesCreated.connect(self.on_series_created)
        wizard.exec()
    
    def on_series_created(self, series_id):
        """Handle new series creation."""
        self.load_series()
        self.status_label.setText(f"Created new series (ID: {series_id})")
        self.status_label.setStyleSheet("color: green; padding: 5px;")
        self.seriesCreated.emit(series_id)

    def export_series_ui(self):
        """Export the selected series to a JSON file."""
        series_id = self.get_selected_series_id()
        if not series_id:
            return

        # Prompt for file save location
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Series", f"series_{series_id}.json", "JSON Files (*.json)"
        )
        
        if not filepath:
            return

        try:
            transfer_manager = SeriesTransferManager(self.db_manager)
            success = transfer_manager.export_series(series_id, filepath)
            if success:
                QMessageBox.information(self, "Success", f"Series exported successfully to {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export series: {str(e)}")

    def import_series_ui(self):
        """Import a series from a JSON file."""
        # Prompt for file open
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Series", "", "JSON Files (*.json)"
        )
        
        if not filepath:
            return

        try:
            transfer_manager = SeriesTransferManager(self.db_manager)
            new_series_id = transfer_manager.import_series(filepath)
            
            QMessageBox.information(self, "Success", f"Series imported successfully (New ID: {new_series_id})")
            
            # Refresh list and notify
            self.load_series()
            self.seriesCreated.emit(new_series_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import series: {str(e)}")
