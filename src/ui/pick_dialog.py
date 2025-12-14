from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QRadioButton, QButtonGroup, QDoubleSpinBox, QPushButton,
                             QFormLayout, QGroupBox, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.db.manager import DatabaseManager
from src.db.repositories import PickRepository, BowlGameRepository, TeamRepository, OddsRepository

class PickDialog(QDialog):
    """
    Dialog for making a pick on a bowl game.
    Supports spread and over/under bets with manual spread entry.
    """
    pickMade = pyqtSignal(int)  # Emits pick_id when saved
    
    def __init__(self, db_manager: DatabaseManager, game_data, team1, team2, 
                 series_id, person_id, odds=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.game_data = game_data
        self.team1 = team1
        self.team2 = team2
        self.series_id = series_id
        self.person_id = person_id
        self.odds = odds
        
        self.pick_repo = PickRepository(db_manager)
        
        self.setWindowTitle(f"Make Pick - {game_data.game_name}")
        self.setModal(True)
        self.resize(500, 400)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Game Info Header
        header = QLabel(f"{self.team1.canonical_name} vs {self.team2.canonical_name}")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        game_status = QLabel(f"Status: {self.game_data.game_status}")
        game_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(game_status)
        
        # Pick Type Selection
        type_group = QGroupBox("Pick Type")
        type_layout = QVBoxLayout()
        
        self.type_button_group = QButtonGroup()
        self.spread_radio = QRadioButton("Spread")
        self.spread_radio.setChecked(True)
        self.spread_radio.toggled.connect(self._on_type_changed)
        self.type_button_group.addButton(self.spread_radio)
        
        self.ou_radio = QRadioButton("Over/Under")
        self.ou_radio.toggled.connect(self._on_type_changed)
        self.type_button_group.addButton(self.ou_radio)
        
        type_layout.addWidget(self.spread_radio)
        type_layout.addWidget(self.ou_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Spread Selection
        self.spread_group = QGroupBox("Spread Selection")
        spread_layout = QVBoxLayout()
        
        # Manual spread entry
        spread_form = QFormLayout()
        self.spread_input = QDoubleSpinBox()
        self.spread_input.setRange(-99.5, 99.5)
        self.spread_input.setSingleStep(0.5)
        self.spread_input.setDecimals(1)
        
        # Pre-populate with API spread if available
        if self.odds and self.odds.spread_team1 is not None:
            self.spread_input.setValue(self.odds.spread_team1)
        
        spread_form.addRow(f"{self.team1.canonical_name} Spread:", self.spread_input)
        spread_layout.addLayout(spread_form)
        
        # Team selection
        self.team_button_group = QButtonGroup()
        self.team1_radio = QRadioButton(f"{self.team1.canonical_name} ({self.spread_input.value():+})")
        self.team1_radio.setChecked(True)
        self.team_button_group.addButton(self.team1_radio, 1)
        
        self.team2_radio = QRadioButton(f"{self.team2.canonical_name} ({-self.spread_input.value():+})")
        self.team_button_group.addButton(self.team2_radio, 2)
        
        spread_layout.addWidget(self.team1_radio)
        spread_layout.addWidget(self.team2_radio)
        
        # Update labels when spread changes
        self.spread_input.valueChanged.connect(self._update_spread_labels)
        
        self.spread_group.setLayout(spread_layout)
        layout.addWidget(self.spread_group)
        
        # Over/Under Selection
        self.ou_group = QGroupBox("Over/Under Selection")
        ou_layout = QVBoxLayout()
        
        # Manual O/U entry
        ou_form = QFormLayout()
        self.ou_input = QDoubleSpinBox()
        self.ou_input.setRange(0, 200)
        self.ou_input.setSingleStep(0.5)
        self.ou_input.setDecimals(1)
        
        # Pre-populate with API O/U if available
        if self.odds and self.odds.over_under is not None:
            self.ou_input.setValue(self.odds.over_under)
        
        ou_form.addRow("Total Points:", self.ou_input)
        ou_layout.addLayout(ou_form)
        
        # Over/Under selection
        self.ou_button_group = QButtonGroup()
        self.over_radio = QRadioButton(f"Over {self.ou_input.value()}")
        self.over_radio.setChecked(True)
        self.ou_button_group.addButton(self.over_radio, 1)
        
        self.under_radio = QRadioButton(f"Under {self.ou_input.value()}")
        self.ou_button_group.addButton(self.under_radio, 2)
        
        ou_layout.addWidget(self.over_radio)
        ou_layout.addWidget(self.under_radio)
        
        # Update labels when O/U changes
        self.ou_input.valueChanged.connect(self._update_ou_labels)
        
        self.ou_group.setLayout(ou_layout)
        self.ou_group.setVisible(False)  # Hidden by default
        layout.addWidget(self.ou_group)
        
        # Bet Amount
        amount_form = QFormLayout()
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 10000)
        self.amount_input.setSingleStep(1)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$")
        
        # Set default based on game tier (if we have series data)
        # For now, default to $5
        self.amount_input.setValue(5.00)
        
        amount_form.addRow("Bet Amount:", self.amount_input)
        layout.addLayout(amount_form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Pick")
        save_btn.clicked.connect(self._save_pick)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_type_changed(self):
        """Toggle between spread and O/U groups."""
        is_spread = self.spread_radio.isChecked()
        self.spread_group.setVisible(is_spread)
        self.ou_group.setVisible(not is_spread)
    
    def _update_spread_labels(self, value):
        """Update team radio button labels when spread changes."""
        self.team1_radio.setText(f"{self.team1.canonical_name} ({value:+})")
        self.team2_radio.setText(f"{self.team2.canonical_name} ({-value:+})")
    
    def _update_ou_labels(self, value):
        """Update O/U radio button labels when total changes."""
        self.over_radio.setText(f"Over {value}")
        self.under_radio.setText(f"Under {value}")
    
    def _save_pick(self):
        """Save the pick to the database."""
        try:
            pick_type = "Spread" if self.spread_radio.isChecked() else "Over/Under"
            
            if pick_type == "Spread":
                line = self.spread_input.value()
                picked_team_id = self.team1.id if self.team_button_group.checkedId() == 1 else self.team2.id
                picked_value = None
            else:
                line = self.ou_input.value()
                picked_team_id = None
                picked_value = "Over" if self.ou_button_group.checkedId() == 1 else "Under"
            
            bet_amount = self.amount_input.value()
            
            # Create pick
            pick = self.pick_repo.create(
                betting_series_id=self.series_id,
                person_id=self.person_id,
                bowl_game_id=self.game_data.id,
                pick_type=pick_type,
                picked_team_id=picked_team_id,
                picked_value=picked_value,
                line_at_pick=line,
                bet_amount=bet_amount
            )
            
            self.pickMade.emit(pick.id)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pick: {str(e)}")
