from PyQt6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox,
                             QFormLayout)
from PyQt6.QtCore import pyqtSignal
from src.db.manager import DatabaseManager
from src.db.repositories import SeasonRepository, PersonRepository, BettingSeriesRepository

class SeriesWizard(QWizard):
    seriesCreated = pyqtSignal(int) # Emits series ID upon finish

    def __init__(self, db_manager: DatabaseManager, parent=None, edit_mode=False, series_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.edit_mode = edit_mode
        self.series_data = series_data
        
        title = "Edit Betting Series" if edit_mode else "New Betting Series Setup"
        self.setWindowTitle(title)
        self.setWizardStyle(QWizard.WizardStyle.MacStyle)
        
        self.season_page = SeasonPage()
        self.participants_page = ParticipantsPage()
        self.rules_page = RulesPage()
        
        self.addPage(self.season_page)
        self.addPage(self.participants_page)
        self.addPage(self.rules_page)
        
        # Pre-populate if editing
        if edit_mode and series_data:
            self._populate_fields()
        
        self.accepted.connect(self._save_data)

    def _populate_fields(self):
        """Pre-populate wizard fields with existing series data."""
        # Get season year from season_id
        season_repo = SeasonRepository(self.db_manager)
        season = season_repo.get_by_id(self.series_data.season_id)
        if season:
            self.season_page.year_input.setValue(season.start_year)
        
        # Participants page  
        person_repo = PersonRepository(self.db_manager)
        person1 = person_repo.get_by_id(self.series_data.person1_id)
        person2 = person_repo.get_by_id(self.series_data.person2_id)
        
        if person1:
            self.participants_page.p1_input.setText(person1.name)
        if person2:
            self.participants_page.p2_input.setText(person2.name)
        
        # Rules page
        self.rules_page.reg_input.setValue(self.series_data.default_bet_amount_regular)
        self.rules_page.semi_input.setValue(self.series_data.default_bet_amount_cfp_semi)
        self.rules_page.champ_input.setValue(self.series_data.default_bet_amount_championship)

    def _save_data(self):
        try:
            season_repo = SeasonRepository(self.db_manager)
            person_repo = PersonRepository(self.db_manager)
            series_repo = BettingSeriesRepository(self.db_manager)
            
            # Get Season (create if doesn't exist)
            year = self.season_page.year_input.value()
            season = season_repo.get_by_year(year)
            if not season:
                season = season_repo.create(year, f"{year}-{year+1} Bowl Season")
            
            # Get or Create Persons
            p1_name = self.participants_page.p1_input.text()
            p2_name = self.participants_page.p2_input.text()
            
            # Try to find existing persons by name
            all_persons = person_repo.get_all()
            p1 = next((p for p in all_persons if p.name == p1_name), None)
            p2 = next((p for p in all_persons if p.name == p2_name), None)
            
            if not p1:
                p1 = person_repo.create(p1_name)
            if not p2:
                p2 = person_repo.create(p2_name)
            
            # Get Rules
            series_name = self.series_data.name if (self.edit_mode and self.series_data) else f"{p1.name} vs {p2.name} - {year}"
            reg_amt = self.rules_page.reg_input.value()
            semi_amt = self.rules_page.semi_input.value()
            champ_amt = self.rules_page.champ_input.value()
            
            if self.edit_mode and self.series_data:
                # Update existing series
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE BettingSeries 
                    SET season_id=?, person1_id=?, person2_id=?, name=?,
                        default_bet_amount_regular=?, default_bet_amount_cfp_semi=?, 
                        default_bet_amount_championship=?
                    WHERE id=?
                """, (season.id, p1.id, p2.id, series_name, reg_amt, semi_amt, champ_amt, self.series_data.id))
                conn.commit()
                series_id = self.series_data.id
            else:
                # Create new series
                series = series_repo.create(
                    season_id=season.id,
                    person1_id=p1.id,
                    person2_id=p2.id,
                    name=series_name,
                    reg_amt=reg_amt,
                    semi_amt=semi_amt,
                    champ_amt=champ_amt
                )
                series_id = series.id
            
            self.seriesCreated.emit(series_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create series: {str(e)}")


class SeasonPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Season Configuration")
        self.setSubTitle("Select which bowl season you're betting on.")
        
        layout = QFormLayout()
        
        self.year_input = QSpinBox()
        self.year_input.setRange(2000, 2100)
        self.year_input.setValue(2025)
        self.registerField("year", self.year_input)
        
        layout.addRow("Season Start Year:", self.year_input)
        self.setLayout(layout)

class ParticipantsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Participants")
        self.setSubTitle("Enter the names of the two people in this betting series.")
        
        layout = QFormLayout()
        
        self.p1_input = QLineEdit()
        self.registerField("p1_name*", self.p1_input) # * means mandatory
        
        self.p2_input = QLineEdit()
        self.registerField("p2_name*", self.p2_input)
        
        layout.addRow("Person 1 Name:", self.p1_input)
        layout.addRow("Person 2 Name:", self.p2_input)
        self.setLayout(layout)

class RulesPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Betting Rules")
        self.setSubTitle("Set the default bet amounts for each game tier.")
        
        layout = QFormLayout()
        
        self.reg_input = QDoubleSpinBox()
        self.reg_input.setValue(5.00)
        self.registerField("reg_amt", self.reg_input)
        
        self.semi_input = QDoubleSpinBox()
        self.semi_input.setValue(10.00)
        self.registerField("semi_amt", self.semi_input)
        
        self.champ_input = QDoubleSpinBox()
        self.champ_input.setValue(20.00)
        self.registerField("champ_amt", self.champ_input)
        
        layout.addRow("Regular Bowl Game ($):", self.reg_input)
        layout.addRow("CFP Playoff Game ($):", self.semi_input)
        layout.addRow("National Championship ($):", self.champ_input)
        self.setLayout(layout)
