from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class LeaderboardWidget(QFrame):
    """
    Displays betting series standings including:
    - Overall Record (W-L-P)
    - Overall Win %
    - Net Profit
    - Own Pick Record & Win %
    """
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: #f8f9fa; border-radius: 5px;")
        self._init_ui()

    def _init_ui(self):
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.setLayout(self.layout)
        
        # We will dynamically add widgets for each person when data is loaded
        self.p1_widget = self._create_person_widget()
        self.p2_widget = self._create_person_widget()
        
        self.layout.addWidget(self.p1_widget)
        self.layout.addStretch() # Spacer
        self.layout.addWidget(QLabel("VS"))
        self.layout.addStretch() # Spacer
        self.layout.addWidget(self.p2_widget)
        
    def _create_person_widget(self):
        w = QWidget()
        l = QVBoxLayout()
        l.setSpacing(2)
        w.setLayout(l)
        
        name = QLabel("Name")
        name.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(name)
        
        stats = QLabel("0-0-0 (0%)")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(stats)
        
        net = QLabel("$0.00")
        net.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        net.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(net)
        
        extra = QLabel("Own Picks: 0/0 (0%)")
        extra.setStyleSheet("color: gray; font-size: 10px;")
        extra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(extra)
        
        # Store refs
        w.name_lbl = name
        w.stats_lbl = stats
        w.net_lbl = net
        w.extra_lbl = extra
        return w

    def update_stats(self, person1, person2, stats):
        """
        Update the display.
        person1/2: Person objects
        stats: result of repository.get_series_stats(series_id)
        """
        self._update_person(self.p1_widget, person1, stats.get(person1.id, {}))
        self._update_person(self.p2_widget, person2, stats.get(person2.id, {}))

    def _update_person(self, widget, person, s):
        if not person:
            widget.hide()
            return
        
        widget.show()
        widget.name_lbl.setText(person.name)
        
        # Basic Stats
        wins = s.get('wins', 0)
        losses = s.get('losses', 0)
        pushes = s.get('pushes', 0)
        total = wins + losses + pushes
        
        win_pct = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        
        widget.stats_lbl.setText(f"{wins}-{losses}-{pushes}  ({win_pct:.1f}%)")
        
        # Net Profit
        net = s.get('net_profit', 0.0)
        txt = f"${abs(net):.2f}"
        if net > 0:
            txt = f"+{txt}"
            widget.net_lbl.setStyleSheet("color: green;")
        elif net < 0:
            txt = f"-{txt}"
            widget.net_lbl.setStyleSheet("color: red;")
        else:
            widget.net_lbl.setStyleSheet("color: black;")
        widget.net_lbl.setText(txt)
        
        # Own Picks Stats
        own_wins = s.get('own_wins', 0)
        own_losses = s.get('own_losses', 0)
        own_total = s.get('own_total', 0)
        
        # Own Win % calculation (typically own_wins / own_wins+own_losses ?)
        own_decided = own_wins + own_losses
        own_pct = (own_wins / own_decided * 100) if own_decided > 0 else 0.0
        
        widget.extra_lbl.setText(f"Own Picks: {own_wins}-{own_losses} ({own_pct:.1f}%)")
