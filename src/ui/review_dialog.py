from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QComboBox, QHeaderView, QMessageBox, QAbstractItemView,
                             QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from datetime import datetime

class PicksReviewDialog(QDialog):
    """
    Dialog to review and check history of picks.
    Allows manually overriding results if needed.
    """
    def __init__(self, db_manager, series_id, person_repo, game_repo, team_repo, pick_repo, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Picks History")
        self.resize(800, 600)
        
        self.db_manager = db_manager
        self.series_id = series_id
        self.person_repo = person_repo
        self.game_repo = game_repo
        self.team_repo = team_repo
        self.pick_repo = pick_repo
        
        # Load references
        self.persons = {p.id: p.name for p in self.person_repo.get_all()}
        self.teams = {t.id: t.canonical_name for t in self.team_repo.get_all()}
        self.games = {g.id: g for g in self.game_repo.get_all()} # Might be heavy if many games, but okay for now
        
        self._init_ui()
        self.load_data()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter Status:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Finalized (Win/Loss/Push)", "Pending"])
        self.filter_combo.currentTextChanged.connect(self.load_data)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Game", "Person", "Pick", "Line", "Bet", "Result", "P/L", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def load_data(self):
        filter_mode = self.filter_combo.currentText()
        picks = self.pick_repo.get_picks_for_series(self.series_id)
        
        # Apply Filter
        filtered_picks = []
        for p in picks:
            is_final = p.result in ['WIN', 'LOSS', 'PUSH']
            
            if filter_mode == "All":
                filtered_picks.append(p)
            elif filter_mode == "Pending" and not is_final:
                filtered_picks.append(p)
            elif "Finalized" in filter_mode and is_final:
                filtered_picks.append(p)
                
        self.table.setRowCount(len(filtered_picks))
        
        for i, pick in enumerate(filtered_picks):
            game = self.games.get(pick.bowl_game_id)
            game_name = game.game_name if game else f"Game {pick.bowl_game_id}"
            
            person_name = self.persons.get(pick.person_id, "Unknown")
            
            # Format Pick Display
            if pick.pick_type == "Spread":
                team_name = self.teams.get(pick.picked_team_id, "Unknown")
                pick_str = f"{team_name} (Spread)"
            else:
                pick_str = f"{pick.picked_value} (O/U)"
                
            line_str = f"{pick.line_at_pick}"
            if pick.line_at_pick > 0:
                line_str = f"+{pick.line_at_pick}"
                
            bet_str = f"${pick.bet_amount:.2f}"
            result_str = pick.result
            
            pl_val = pick.profit_loss if pick.profit_loss else 0.0
            pl_str = f"${pl_val:.2f}"
            if pl_val > 0:
                pl_str = f"+{pl_str}"
            
            # Set Items
            self.table.setItem(i, 0, QTableWidgetItem(game_name))
            self.table.setItem(i, 1, QTableWidgetItem(person_name))
            self.table.setItem(i, 2, QTableWidgetItem(pick_str))
            self.table.setItem(i, 3, QTableWidgetItem(line_str))
            self.table.setItem(i, 4, QTableWidgetItem(bet_str))
            
            res_item = QTableWidgetItem(result_str)
            if result_str == 'WIN':
                res_item.setForeground(QColor("green"))
                res_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            elif result_str == 'LOSS':
                res_item.setForeground(QColor("red"))
            elif result_str == 'PUSH':
                res_item.setForeground(QColor("gray"))
            self.table.setItem(i, 5, res_item)
            
            pl_item = QTableWidgetItem(pl_str)
            if pl_val > 0:
                pl_item.setForeground(QColor("green"))
            elif pl_val < 0:
                pl_item.setForeground(QColor("red"))
            self.table.setItem(i, 6, pl_item)
            
            # Action Button
            btn = QPushButton("✎ Edit")
            btn.clicked.connect(lambda checked, pid=pick.id, cur_res=result_str: self.edit_pick(pid, cur_res))
            self.table.setCellWidget(i, 7, btn)
            
    def edit_pick(self, pick_id, current_result):
        """Manually override a pick result."""
        items = ["WIN", "LOSS", "PUSH", "Pending"]
        try:
            curr_idx = items.index(current_result)
        except ValueError:
            curr_idx = 0
            
        result, ok = QInputDialog.getItem(self, "Override Result", 
                                          "Select new result:", items, curr_idx, False)
        
        if ok and result:
            # We also need to update Profit/Loss based on the result.
            # Fetch pick to get bet amount
            pick = self.pick_repo.get_by_id(pick_id)
            if not pick:
                return
            
            new_pl = 0.0
            if result == 'WIN':
                new_pl = pick.bet_amount
            elif result == 'LOSS':
                new_pl = -pick.bet_amount
            elif result == 'PUSH':
                new_pl = 0.0
            elif result == 'Pending':
                new_pl = 0.0
                
            confirm = QMessageBox.question(self, "Confirm Override", 
                                           f"Set result to {result} and P/L to ${new_pl:.2f}?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.pick_repo.update_financials(pick_id, result, new_pl)
                self.load_data() # Refresh Table
