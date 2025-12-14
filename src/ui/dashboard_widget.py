from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QGridLayout, QPushButton, QMessageBox,
                             QInputDialog, QTreeWidget, QTreeWidgetItem, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QCursor
from datetime import datetime, timezone, timedelta
import dateutil.parser

from src.db.manager import DatabaseManager
from src.db.repositories import (BowlGameRepository, TeamRepository, OddsRepository, 
                                 SeasonRepository, PickRepository, BettingSeriesRepository, PersonRepository)
from src.logic.sync_engine import SyncManager
from src.logic.scoring import ScoringEngine
from src.ui.leaderboard_widget import LeaderboardWidget
from src.ui.review_dialog import PicksReviewDialog

class ClickableLabel(QLabel):
    """QLabel that emits clicked signal when clicked."""
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(self.styleSheet() + " QLabel:hover { background-color: #f0f0f0; }")
    
    def mouseReleaseEvent(self, event):
        """Use mouseReleaseEvent instead of mousePressEvent for better reliability."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class GameCard(QFrame):
    """
    Widget to display a single bowl game with per-game picker and quick-pick functionality.
    """
    teamClicked = pyqtSignal(int, int, int)  # (game_id, team_id, picker_id)
    pickerToggled = pyqtSignal(int)  # game_id
    spreadEditRequested = pyqtSignal(int)  # game_id
    ouClicked = pyqtSignal(int, str, int)  # (game_id, "Over"/"Under", picker_id)
    betAmountChanged = pyqtSignal(int, float) # game_id, new_amount
    
    def __init__(self, game_data, team1, team2, odds=None, picker_id=None, picker_name=None,
                 picks_dict=None, person_names=None, db_manager=None, bet_amount=0.0, show_bet_amount=True):
        super().__init__()
        self.game_data = game_data
        self.team1 = team1
        self.team2 = team2
        self.odds = odds
        self.picker_id = picker_id
        self.picker_name = picker_name
        self.picks_dict = picks_dict or {}
        self.person_names = person_names or {}
        self.db_manager = db_manager
        self.bet_amount = bet_amount
        self.show_bet_amount = show_bet_amount
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Tighter spacing
        
        # Header: Game Name & Date
        header_layout = QHBoxLayout()
        
        clean_name = self._format_game_name(self.game_data.game_name)
        game_name = QLabel(clean_name)

        game_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(game_name)
        
        # Bet Amount (Editable)
        if self.show_bet_amount:
            bet_str = f"${self.bet_amount:.2f}"
            bet_amount_lbl = ClickableLabel(bet_str)
            bet_amount_lbl.setToolTip("Click to edit bet amount")
            bet_amount_lbl.setStyleSheet("color: green; font-weight: bold; font-size: 12px; margin-left: 10px; border: 1px dotted #ccc; padding: 2px;")
            bet_amount_lbl.clicked.connect(self._on_edit_bet_amount)
            header_layout.addWidget(bet_amount_lbl)
        
        header_layout.addStretch()
        
        # Date Formatting
        date_str = self.game_data.game_date
        display_date = date_str
        
        try:
            dt_utc = dateutil.parser.isoparse(date_str)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
            
            central_offset = timezone(timedelta(hours=-6))
            dt_central = dt_utc.astimezone(central_offset)
            display_date = dt_central.strftime("%A %B %d, %Y %I:%M%p")
            
            if display_date.split()[3].startswith('0'):
                parts = display_date.split()
                parts[3] = parts[3][1:]
                display_date = " ".join(parts)
        except Exception:
            pass
        
        date_lbl = QLabel(display_date)
        date_lbl.setStyleSheet("color: gray; font-size: 10px;")
        
        header_layout.addWidget(game_name)
        header_layout.addStretch()
        header_layout.addWidget(date_lbl)
        layout.addLayout(header_layout)
        
        # Picker and Status on same line
        picker_status_layout = QHBoxLayout()
        
        # Picker indicator (clickable)
        if self.picker_name:
            picker_label = ClickableLabel(f"Picker: {self.picker_name}")
            picker_label.setStyleSheet("""
                QLabel { 
                    font-weight: bold; 
                    color: blue; 
                    padding: 2px 4px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
            """)
            picker_label.clicked.connect(lambda: self.pickerToggled.emit(self.game_data.id))
            picker_status_layout.addWidget(picker_label)


        
        picker_status_layout.addStretch()
        
        # Add Edit Spread Button
        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(20, 20)
        edit_btn.setToolTip("Edit Spread")
        edit_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #888;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
            QPushButton:hover {
                color: blue;
                background-color: #eee;
                border-radius: 3px;
            }
        """)
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.clicked.connect(lambda: self.spreadEditRequested.emit(self.game_data.id))
        picker_status_layout.addWidget(edit_btn)
        
        # Status
        status_text = self.game_data.game_status
        status_lbl = QLabel(status_text)
        status_style = "font-size: 10px; font-weight: bold; padding: 2px 4px; border-radius: 3px;"
        
        is_final = status_text == "Final" or status_text == "Completed"
        
        if is_final:
            status_style += " background-color: #d4edda; color: #155724;"
        elif "Q" in status_text or status_text == "In Progress":
             status_style += " background-color: #fff3cd; color: #856404;"
        else:
             status_style += " background-color: #e2e3e5; color: #383d41;"
             
        status_lbl.setStyleSheet(status_style)
        picker_status_layout.addWidget(status_lbl)
        
        layout.addLayout(picker_status_layout)
        
        # Teams - Compact format
        teams_layout = QHBoxLayout()
        teams_layout.setSpacing(10)
        
        spread_val = None
        if self.odds and self.odds.spread_team1 is not None:
            spread_val = self.odds.spread_team1
        
        # Team 1 logic
        t1_spread_str = f" ({spread_val:+})" if spread_val is not None else ""
        t1_name = (self.team1.canonical_name if self.team1 else "Unknown") + t1_spread_str
        
        t1_btn = QPushButton(t1_name)
        t1_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 6px;
                border: none;
                background: transparent;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-radius: 3px;
            }
        """)
        t1_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.picker_id:
            t1_btn.clicked.connect(lambda: self._on_team_clicked(self.team1.id))
        
        # Find who picked team1
        t1_bettor = ""
        t1_result = None
        for person_id, pick in self.picks_dict.items():
            if pick.pick_type == "Spread" and pick.picked_team_id == self.team1.id:
                t1_bettor = self.person_names.get(person_id, "")
                t1_result = pick.result
                break
        
        # Always create bettor label with fixed width for alignment (even if empty)
        t1_bettor_lbl = QLabel(t1_bettor)
        t1_style = "font-size: 10px; font-style: italic; margin-left: 8px;"
        
        if t1_result == "WIN":
             t1_style += " color: green; font-weight: bold;"
             t1_bettor_lbl.setText(f"{t1_bettor} (W)")
        elif t1_result == "LOSS":
             t1_style += " color: red;"
             t1_bettor_lbl.setText(f"{t1_bettor} (L)")
        elif t1_result == "PUSH":
             t1_style += " color: gray;"
             t1_bettor_lbl.setText(f"{t1_bettor} (P)")
        else:
             t1_style += " color: #666;"
             
        t1_bettor_lbl.setStyleSheet(t1_style)
        t1_bettor_lbl.setFixedWidth(70)  # Fixed width ensures scores always align
        
        t1_score_val = str(self.game_data.final_score_team1) if self.game_data.final_score_team1 is not None else "-"
        t1_score = QLabel(t1_score_val)
        t1_score.setStyleSheet("font-size: 12px; font-weight: bold;")
        t1_score.setFixedWidth(25)
        t1_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Highlight winner
        if is_final:
            s1 = self.game_data.final_score_team1 or 0
            s2 = self.game_data.final_score_team2 or 0
            if s1 > s2:
                t1_btn.setStyleSheet(t1_btn.styleSheet() + "QPushButton { font-weight: bold; }")
        
        # Team 2
        t2_spread_str = f" ({-spread_val:+})" if spread_val is not None else ""
        t2_name = (self.team2.canonical_name if self.team2 else "Unknown") + t2_spread_str
        
        t2_btn = QPushButton(t2_name)
        t2_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px 6px;
                border: none;
                background: transparent;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-radius: 3px;
            }
        """)
        t2_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.picker_id:
            t2_btn.clicked.connect(lambda: self._on_team_clicked(self.team2.id))
        
        # Find who picked team2
        t2_bettor = ""
        t2_result = None
        for person_id, pick in self.picks_dict.items():
            if pick.pick_type == "Spread" and pick.picked_team_id == self.team2.id:
                t2_bettor = self.person_names.get(person_id, "")
                t2_result = pick.result
                break
        
        # Always create bettor label with fixed width for alignment (even if empty)
        t2_bettor_lbl = QLabel(t2_bettor)
        t2_style = "font-size: 10px; font-style: italic; margin-left: 8px;"
        
        if t2_result == "WIN":
             t2_style += " color: green; font-weight: bold;"
             t2_bettor_lbl.setText(f"{t2_bettor} (W)")
        elif t2_result == "LOSS":
             t2_style += " color: red;"
             t2_bettor_lbl.setText(f"{t2_bettor} (L)")
        elif t2_result == "PUSH":
             t2_style += " color: gray;"
             t2_bettor_lbl.setText(f"{t2_bettor} (P)")
        else:
             t2_style += " color: #666;"
             
        t2_bettor_lbl.setStyleSheet(t2_style)
        t2_bettor_lbl.setFixedWidth(70)  # Fixed width ensures scores always align
        
        t2_score_val = str(self.game_data.final_score_team2) if self.game_data.final_score_team2 is not None else "-"
        t2_score = QLabel(t2_score_val)
        t2_score.setStyleSheet("font-size: 12px; font-weight: bold;")
        t2_score.setFixedWidth(25)
        t2_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if is_final:
            s1 = self.game_data.final_score_team1 or 0
            s2 = self.game_data.final_score_team2 or 0
            if s2 > s1:
                t2_btn.setStyleSheet(t2_btn.styleSheet() + "QPushButton { font-weight: bold; }")
        
        # Use grid layout for perfect alignment
        teams_grid = QGridLayout()
        teams_grid.setHorizontalSpacing(8)  # Space between columns
        teams_grid.setVerticalSpacing(2)    # Space between rows
        teams_grid.setColumnStretch(0, 0)   # Team name - don't stretch
        teams_grid.setColumnStretch(1, 0)   # Bettor - don't stretch
        teams_grid.setColumnStretch(2, 0)   # Score - don't stretch
        
        teams_grid.addWidget(t1_btn, 0, 0)
        teams_grid.addWidget(t1_bettor_lbl, 0, 1)
        teams_grid.addWidget(t1_score, 0, 2)
        
        teams_grid.addWidget(t2_btn, 1, 0)
        teams_grid.addWidget(t2_bettor_lbl, 1, 1)
        teams_grid.addWidget(t2_score, 1, 2)
        
        # Wrap grid in HBoxLayout to keep it on the left
        teams_container = QHBoxLayout()
        teams_container.addLayout(teams_grid)
        teams_container.addStretch()  # Push everything to the left
        
        layout.addLayout(teams_container)
        
        # Over/Under - clickable with picks shown
        if self.odds and self.odds.over_under is not None:
            ou_layout = QHBoxLayout()
            ou_lbl = QLabel(f"O/U: {self.odds.over_under}")
            ou_lbl.setStyleSheet("font-size: 11px; color: #555;")
            ou_layout.addWidget(ou_lbl)
            
            # Clickable O/U options
            over_btn = ClickableLabel("Over")
            over_btn.setStyleSheet("font-size: 11px; color: blue; margin-left: 8px; font-weight: bold;")
            over_btn.clicked.connect(lambda: self.ouClicked.emit(self.game_data.id, "Over", self.picker_id))
            
            under_btn = ClickableLabel("Under")
            under_btn.setStyleSheet("font-size: 11px; color: blue; margin-left: 4px; font-weight: bold;")
            under_btn.clicked.connect(lambda: self.ouClicked.emit(self.game_data.id, "Under", self.picker_id))
            
            if self.picker_id:
                ou_layout.addWidget(over_btn)
                ou_layout.addWidget(under_btn)
            
            # Show O/U picks - determine who picked what
            over_bettor = ""
            under_bettor = ""
            
            # Get both person names
            person1_name = self.person_names.get(list(self.person_names.keys())[0]) if self.person_names else ""
            person2_name = self.person_names.get(list(self.person_names.keys())[1]) if len(self.person_names) > 1 else ""
            
            for person_id, pick in self.picks_dict.items():
                if pick.pick_type == "Over/Under":
                    bettor_name = self.person_names.get(person_id, "")
                    result = pick.result
                    
                    # Store result for display
                    bet_text = bettor_name
                    if result == "WIN": bet_text += " (W)"
                    elif result == "LOSS": bet_text += " (L)"
                    elif result == "PUSH": bet_text += " (P)"
                    
                    if pick.picked_value == "Over":
                        over_bettor = bet_text
                        # Other person gets Under
                        under_bettor = person2_name if bettor_name == person1_name else person1_name
                    elif pick.picked_value == "Under":
                        under_bettor = bet_text
                        # Other person gets Over
                        over_bettor = person2_name if bettor_name == person1_name else person1_name
            
            if over_bettor or under_bettor:
                picks_text = f"  Over: {over_bettor}  Under: {under_bettor}"
                picks_lbl = QLabel(picks_text)
                picks_lbl.setStyleSheet("font-size: 10px; font-style: italic; color: #666;")
                ou_layout.addWidget(picks_lbl)
                
            ou_layout.addStretch()
            layout.addLayout(ou_layout)
        
        self.setLayout(layout)
    
    def _on_edit_bet_amount(self):
        """Emit signal to edit bet amount."""
        val, ok = QInputDialog.getDouble(
            self, 
            "Edit Bet Amount", 
            f"Set bet amount for {self.game_data.game_name}:",
            value=self.bet_amount,
            min=0.0,
            decimals=2
        )
        if ok:
            self.betAmountChanged.emit(self.game_data.id, val)

    def _on_picker_clicked(self):
        """Emit signal when picker is clicked."""
        print(f"Picker clicked for game {self.game_data.id}")  # Debug
        self.pickerToggled.emit(self.game_data.id)
    
    def _on_team_clicked(self, team_id):
        if self.picker_id:
            self.teamClicked.emit(self.game_data.id, team_id, self.picker_id)
    
    def _on_edit_spread(self):
        """Emit signal to edit spread."""
        self.spreadEditRequested.emit(self.game_data.id)
    
    def _show_ou_menu(self):
        """Show Over/Under selection dialog."""
        if not self.picker_id or not self.odds:
            return
        
        items = ["Over", "Under"]
        choice, ok = QInputDialog.getItem(
            self, "Over/Under Pick",
            f"Pick Over or Under {self.odds.over_under}:",
            items, 0, False
        )
        
        if ok and choice:
            self.ouClicked.emit(self.game_data.id, choice, self.picker_id)

    def _format_game_name(self, name: str) -> str:
        """Smart capitalization for game names."""
        # Start with standard title case
        name = name.title()
        
        # Replacements for common issues
        replacements = {
            "'S ": "'s ",
            "'S": "'s",  # End of string
            "Dna": "DNA",
            "Cfp": "CFP",
            "A&m": "A&M",
            "Ncaa": "NCAA",
            "Usa": "USA",
            "Vs": "vs",
            "Vs.": "vs."
        }
        
        for k, v in replacements.items():
            name = name.replace(k, v)
        
        return name


class DashboardWidget(QWidget):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.game_repo = BowlGameRepository(db_manager)
        self.team_repo = TeamRepository(db_manager)
        self.odds_repo = OddsRepository(db_manager)
        self.season_repo = SeasonRepository(db_manager)
        # Initialize Engines
        self.sync_manager = SyncManager(db_manager)
        self.pick_repo = PickRepository(db_manager)
        self.scoring_engine = ScoringEngine(self.pick_repo, self.game_repo)
        self.series_repo = BettingSeriesRepository(db_manager)
        self.person_repo = PersonRepository(db_manager)
        
        self.current_season_year = 2025
        self.active_series_id = None
        self.person1_id = None
        self.person2_id = None
        self.person_names = {}
        self.game_pickers = {}  # {game_id: person_id}
        self.game_bet_overrides = {}  # {game_id: amount}
        
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        # Top-level Horiz Layout
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0,0,0,0)
        
        # Splitter to hold Sidebar + Content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT SIDEBAR: Series Tree ---
        sidebar_widget = QWidget()
        sidebar_widget.setMinimumWidth(250)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        
        sidebar_label = QLabel("Select Series")
        sidebar_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        sidebar_layout.addWidget(sidebar_label)
        
        self.series_tree = QTreeWidget()
        self.series_tree.setHeaderLabel("Season / Series")
        self.series_tree.itemClicked.connect(self._on_sidebar_item_clicked)
        sidebar_layout.addWidget(self.series_tree)
        
        splitter.addWidget(sidebar_widget)
        
        # --- RIGHT CONTENT: Dashboard ---
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        
        title = QLabel("Bowl Games Dashboard")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Leaderboard (Top)
        self.leaderboard = LeaderboardWidget()
        self.leaderboard.hide() # Hide until series is active
        main_layout.addWidget(self.leaderboard)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.games_layout = QVBoxLayout(self.scroll_content)
        self.games_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)
        
        button_layout = QHBoxLayout()
        
        sync_btn = QPushButton("Sync from APIs (Update Games & Odds)")
        sync_btn.clicked.connect(self.start_sync)
        button_layout.addWidget(sync_btn)
        
        refresh_btn = QPushButton("Refresh Display (Reload from Database)")
        refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_btn)
        
        review_btn = QPushButton("Review / Edit Picks")
        review_btn.clicked.connect(self.open_review_dialog)
        button_layout.addWidget(review_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status Bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("padding: 5px; color: gray;")
        main_layout.addWidget(self.status_bar)
        
        splitter.addWidget(content_widget)
        
        # Set Splitter Ratios (Left small, Right big)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        
        top_layout.addWidget(splitter)
        self.setLayout(top_layout)
        
        # Initialize Sidebar Data
        self.refresh_sidebar()
    
    def refresh_sidebar(self):
        self.series_tree.clear()
        
        seasons = self.season_repo.get_all()
        for season in seasons:
            series_list = self.series_repo.get_by_season(season.id)
            if not series_list:
                continue
            
            season_item = QTreeWidgetItem(self.series_tree)
            season_item.setText(0, f"{season.display_name} ({season.start_year})")
            season_item.setExpanded(True)
            
            for series in series_list:
                series_item = QTreeWidgetItem(season_item)
                series_item.setText(0, series.name)
                # Store series ID in data column 1 (hidden) or just attribute
                series_item.setData(0, Qt.ItemDataRole.UserRole, series.id)
                
                # Check if this is current active
                if self.active_series_id and series.id == self.active_series_id:
                    series_item.setSelected(True)
    
    def _on_sidebar_item_clicked(self, item, column):
        series_id = item.data(0, Qt.ItemDataRole.UserRole)
        if series_id:
            self.active_series_id = series_id
            self.load_data()
    
    def start_sync(self):
        self.status_bar.setText("Syncing from APIs...")
        self.status_bar.setStyleSheet("color: blue; padding: 5px;")
        
        def on_progress(msg):
            self.status_bar.setText(f"Syncing: {msg}")
        
        def on_finished(success, msg):
            if success:
                self.status_bar.setText("Sync successful! Data updated.")
                self.status_bar.setStyleSheet("color: green; padding: 5px;")
                self.load_data(show_status=False)
            else:
                self.status_bar.setText(f"Sync failed: {msg}")
                self.status_bar.setStyleSheet("color: red; padding: 5px;")
        
        self.sync_manager.start_sync(on_progress, on_finished)

    def load_data(self, show_status=True):
        if show_status:
            self.status_bar.setText("Refreshing display...")
            self.status_bar.setStyleSheet("color: blue; padding: 5px;")
        
        while self.games_layout.count():
            child = self.games_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        season = self.season_repo.get_by_year(self.current_season_year)
        if not season:
            self.games_layout.addWidget(QLabel("No Season Data Found."))
            return
        
        games = self.game_repo.get_by_season(season.id)
        if not games:
            self.games_layout.addWidget(QLabel("No Games Found. Try Syncing in Settings."))
            return
        
        # Only initialize pickers if not already set (e.g., first load or after series change)
        if not self.game_pickers:
            self._initialize_game_pickers(games)
        
        all_picks = {}
        if self.active_series_id:
            # Ensure we have the latest series info (Person IDs)
            series = self.series_repo.get_by_id(self.active_series_id)
            if series:
                self.person1_id = series.person1_id
                self.person2_id = series.person2_id
                
                # Update pickers context
                self.person_names[self.person1_id] = self.person_repo.get_by_id(self.person1_id).name
                self.person_names[self.person2_id] = self.person_repo.get_by_id(self.person2_id).name
            
            # Update scores for any finalized games
            self.scoring_engine.process_series_picks(self.active_series_id)
            
            # Update Leaderboard
            stats = self.pick_repo.get_series_stats(self.active_series_id)
            p1 = self.person_repo.get_by_id(self.person1_id)
            p2 = self.person_repo.get_by_id(self.person2_id)
            
            if p1 and p2:
                self.leaderboard.update_stats(p1, p2, stats)
                self.leaderboard.show()
            
            picks_list = self.pick_repo.get_picks_for_series(self.active_series_id)
            for pick in picks_list:
                key = (pick.bowl_game_id, pick.person_id)
                all_picks[key] = pick
        else:
            self.leaderboard.hide()
        
        for game in games:
            t1 = self.team_repo.get_by_id(game.team1_id)
            t2 = self.team_repo.get_by_id(game.team2_id)
            odds = self.odds_repo.get_latest_for_game(game.id)
            
            game_picks = {}
            for (gid, pid), pick in all_picks.items():
                if gid == game.id:
                    game_picks[pid] = pick
            
            picker_id = self.game_pickers.get(game.id)
            picker_name = self.person_names.get(picker_id) if picker_id else None
            
            # Determine Bet Amount
            bet_amount = 0.0
            
            # 1. Override?
            if game.id in self.game_bet_overrides:
                 bet_amount = self.game_bet_overrides[game.id]
            # 2. Existing Picks? (Take from first found)
            elif game.id in [p.bowl_game_id for p in list(all_picks.values())]:
                 # Find a pick for this game
                 for p in all_picks.values():
                     if p.bowl_game_id == game.id:
                         bet_amount = p.bet_amount
                         break
            # 3. Default based on Tier
            else:
                series = self.series_repo.get_by_id(self.active_series_id) if self.active_series_id else None
                if series:
                     # Determine using cfp_tier first, then name
                     tier_lower = (game.cfp_tier or "").lower()
                     name_lower = game.game_name.lower()
                     
                     if "championship" in tier_lower or ("championship" in name_lower and "cfp" in name_lower):
                         bet_amount = series.default_bet_amount_championship
                     elif any(x in tier_lower for x in ["semifinal", "quarterfinal", "first round", "playoff"]) or \
                          any(x in name_lower for x in ["semifinal", "quarterfinal", "first round", "playoff"]):
                         bet_amount = series.default_bet_amount_cfp_semi
                     else:
                         bet_amount = series.default_bet_amount_regular
                else:
                    bet_amount = 0.0
            
            show_bet_amount = self.active_series_id is not None
            card = GameCard(game, t1, t2, odds, picker_id, picker_name, game_picks, self.person_names, self.db_manager, bet_amount, show_bet_amount)
            card.teamClicked.connect(self.on_team_clicked)
            card.pickerToggled.connect(self.on_picker_toggled)
            card.spreadEditRequested.connect(self.on_spread_edit_requested)
            card.ouClicked.connect(self.on_ou_clicked)
            card.betAmountChanged.connect(self.on_bet_amount_changed)
            self.games_layout.addWidget(card)
        
        if show_status:
            self.status_bar.setText("Display refreshed.")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
    
    def _initialize_game_pickers(self, games):
        """Initialize picker for each game based on alternating logic."""
        if not self.active_series_id or not self.person1_id or not self.person2_id:
            return
        
        # Get all picks
        all_picks = self.pick_repo.get_picks_for_series(self.active_series_id)
        
        if not all_picks:
            # No picks yet - alternate starting with person1
            current_picker = self.person1_id
            for game in games:
                self.game_pickers[game.id] = current_picker
                # Alternate for next game
                current_picker = self.person2_id if current_picker == self.person1_id else self.person1_id
            return
        
        # Find first pick to determine starting person
        first_pick = min(all_picks, key=lambda p: p.created_at if p.created_at else "")
        first_picker = first_pick.person_id
        
        # Alternate from first picker
        current_picker = first_picker
        for game in games:
            self.game_pickers[game.id] = current_picker
            current_picker = self.person2_id if current_picker == self.person1_id else self.person1_id

    def open_review_dialog(self):
        if not self.active_series_id:
            QMessageBox.information(self, "No Active Series", "Please select a series first.")
            return
            
        dlg = PicksReviewDialog(self.db_manager, self.active_series_id, 
                                self.person_repo, self.game_repo, 
                                self.team_repo, self.pick_repo, self)
        dlg.exec()
        
        # Reload after checking reviews (stats might have changed)
        self.load_data(show_status=False)

    def on_bet_amount_changed(self, game_id, new_amount):
        """Handle bet amount change from GameCard."""
        if not self.active_series_id:
            return
            
        try:
            # 1. Update override state (for UI persistence without picks)
            self.game_bet_overrides[game_id] = new_amount
            
            # 2. Update existing picks in DB if any
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Pick
                SET bet_amount = ?
                WHERE betting_series_id = ? AND bowl_game_id = ?
            """, (new_amount, self.active_series_id, game_id))
            
            updated_count = cursor.rowcount
            conn.commit()
            
            if updated_count > 0:
                self.status_bar.setText(f"Updated bet amount to ${new_amount:.2f} for {updated_count} pick(s).")
            else:
                self.status_bar.setText(f"Set bet amount to ${new_amount:.2f} for next pick.")
                
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
            
            # Reload to refresh UI (e.g. if other logic depends on it, although local update might be enough)
            self.load_data(show_status=False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update bet amount: {str(e)}")

    def on_team_clicked(self, game_id, team_id, picker_id):
        if not self.active_series_id:
            QMessageBox.information(self, "No Active Series", "Please select an active betting series first.")
            return
        
        game = self.game_repo.get_by_id(game_id)
        odds = self.odds_repo.get_latest_for_game(game_id)
        
        if not odds or odds.spread_team1 is None:
            QMessageBox.warning(self, "No Odds", "No spread available. Click the edit button (✎) to enter manually.")
            return
        
        if team_id == game.team1_id:
            line = odds.spread_team1
        else:
            line = -odds.spread_team1
        
        series = self.series_repo.get_by_id(self.active_series_id)
        bet_amount = series.default_bet_amount_regular
        
        try:
            # Mirror Logic: Identify Opponent
            opponent_id = self.person2_id if picker_id == self.person1_id else self.person1_id
            
            # Delete ALL existing picks for BOTH people on this game
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM Pick 
                WHERE betting_series_id = ? AND bowl_game_id = ? AND person_id IN (?, ?)
            """, (self.active_series_id, game_id, picker_id, opponent_id))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"Deleted {deleted_count} existing pick(s) for game {game_id} (both parties)")
            
            # Create Pick for Picker (Initial User)
            self.pick_repo.create(
                betting_series_id=self.active_series_id,
                person_id=picker_id,
                bowl_game_id=game_id,
                pick_type="Spread",
                line_at_pick=line,
                bet_amount=bet_amount,
                picked_team_id=team_id,
                is_originator=True
            )
            
            # Create Mirror Pick for Opponent
            # Opponent gets logic:
            # If Picker chose Team 1 (spread X), Opponent gets Team 2 (spread -X)
            # Line is always relative to selected team.
            
            opponent_team_id = game.team2_id if team_id == game.team1_id else game.team1_id
            opponent_line = -line
            
            self.pick_repo.create(
                betting_series_id=self.active_series_id,
                person_id=opponent_id,
                bowl_game_id=game_id,
                pick_type="Spread",
                line_at_pick=opponent_line,
                bet_amount=bet_amount,
                picked_team_id=opponent_team_id,
                is_originator=False
            )
            
            self.status_bar.setText(f"Pick saved! {self.person_names.get(picker_id, 'User')} vs {self.person_names.get(opponent_id, 'Opponent')}.")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
            self.load_data(show_status=False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pick: {str(e)}")
    
    def on_ou_clicked(self, game_id, choice, picker_id):
        if not self.active_series_id:
            return
        
        odds = self.odds_repo.get_latest_for_game(game_id)
        if not odds or odds.over_under is None:
            QMessageBox.warning(self, "No Odds", "No O/U available.")
            return
        
        series = self.series_repo.get_by_id(self.active_series_id)
        bet_amount = series.default_bet_amount_regular
        
        try:
            # Mirror Logic: Identify Opponent
            opponent_id = self.person2_id if picker_id == self.person1_id else self.person1_id
            
            # Delete ALL existing picks for BOTH people on this game
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM Pick 
                WHERE betting_series_id = ? AND bowl_game_id = ? AND person_id IN (?, ?)
            """, (self.active_series_id, game_id, picker_id, opponent_id))
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"Deleted {deleted_count} existing pick(s) for game {game_id} (both parties)")
            
            # Create Pick for Picker
            self.pick_repo.create(
                betting_series_id=self.active_series_id,
                person_id=picker_id,
                bowl_game_id=game_id,
                pick_type="Over/Under",
                line_at_pick=odds.over_under,
                bet_amount=bet_amount,
                picked_value=choice,
                is_originator=True
            )
            
            # Create Mirror Pick for Opponent
            opponent_choice = "Under" if choice == "Over" else "Over"
            
            self.pick_repo.create(
                betting_series_id=self.active_series_id,
                person_id=opponent_id,
                bowl_game_id=game_id,
                pick_type="Over/Under",
                line_at_pick=odds.over_under,
                bet_amount=bet_amount,
                picked_value=opponent_choice,
                is_originator=False
            )
            
            self.status_bar.setText(f"Pick saved! {self.person_names.get(picker_id, 'User')} vs {self.person_names.get(opponent_id, 'Opponent')}.")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
            self.load_data(show_status=False)
            
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to save pick: {str(e)}")
    
    def on_picker_toggled(self, game_id):
        """Handle picker toggle for a specific game."""
        print(f"Dashboard received picker toggle for game {game_id}")
        
        if not self.person1_id or not self.person2_id:
            print("No person IDs set!")
            return
        
        current_picker = self.game_pickers.get(game_id, self.person1_id)
        new_picker = self.person2_id if current_picker == self.person1_id else self.person1_id
        
        print(f"Changing picker from {self.person_names.get(current_picker)} to {self.person_names.get(new_picker)}")
        
        # Update this game's picker
        self.game_pickers[game_id] = new_picker
        
        # If this is the first game, update all subsequent games
        season = self.season_repo.get_by_year(self.current_season_year)
        if season:
            games = self.game_repo.get_by_season(season.id)
            if games and games[0].id == game_id:
                print("This is game 1 - updating all games")
                current = new_picker
                for game in games:
                    self.game_pickers[game.id] = current
                    current = self.person2_id if current == self.person1_id else self.person1_id
        
        print(f"Game {game_id} picker is now: {self.person_names.get(self.game_pickers[game_id])}")
        
        # Reload display
        self.load_data(show_status=False)
    
    def on_spread_edit_requested(self, game_id):
        current_odds = self.odds_repo.get_latest_for_game(game_id)
        current_spread = current_odds.spread_team1 if current_odds else 0.0
        
        spread, ok = QInputDialog.getDouble(
            self, "Edit Spread",
            "Enter spread for Team 1 (negative means Team 1 is favored):",
            current_spread, -99.5, 99.5, 1
        )
        
        if ok:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            if current_odds:
                cursor.execute("UPDATE Odds SET spread_team1 = ? WHERE id = ?", (spread, current_odds.id))
            else:
                cursor.execute("INSERT INTO Odds (bowl_game_id, spread_team1) VALUES (?, ?)", (game_id, spread))
            
            conn.commit()
            self.status_bar.setText(f"Spread updated to {spread:+}")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
            self.load_data(show_status=False)
    
    def set_active_series(self, series_id, person_id=None):
        self.active_series_id = series_id
        
        # Clear game pickers to force reinitialization
        self.game_pickers = {}
        
        series = self.series_repo.get_by_id(series_id)
        if series:
            self.person1_id = series.person1_id
            self.person2_id = series.person2_id
            
            person1 = self.person_repo.get_by_id(self.person1_id)
            person2 = self.person_repo.get_by_id(self.person2_id)
            
            if person1:
                self.person_names[person1.id] = person1.name
            if person2:
                self.person_names[person2.id] = person2.name
        
        self.load_data(show_status=False)
