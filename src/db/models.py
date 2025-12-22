from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Person:
    id: Optional[int]
    name: str
    created_at: Optional[datetime] = None

@dataclass
class Season:
    id: Optional[int]
    start_year: int
    display_name: str

@dataclass
class Team:
    id: Optional[int]
    canonical_name: str
    short_name: str
    mascot: Optional[str]
    logo_url: Optional[str]
    api_cfd_id: Optional[int]
    api_theodds_id: Optional[str]

@dataclass
class BowlGame:
    id: Optional[int]
    season_id: int
    api_cfd_id: int
    api_theodds_id: Optional[str]
    game_name: str
    game_date: datetime
    location: str
    team1_id: int
    team2_id: int
    cfp_tier: str
    game_status: str
    final_score_team1: Optional[int]
    final_score_team2: Optional[int]
    last_api_update: Optional[datetime] = None

@dataclass
class BettingSeries:
    id: Optional[int]
    season_id: int
    person1_id: int
    person2_id: int
    name: str
    default_bet_amount_regular: float
    default_bet_amount_cfp_semi: float
    default_bet_amount_championship: float
    created_at: Optional[datetime] = None

@dataclass
class Odds:
    id: Optional[int]
    bowl_game_id: int
    spread_team1: Optional[float]
    over_under: Optional[float]
    retrieved_at: Optional[datetime] = None

@dataclass
class Pick:
    id: Optional[int]
    betting_series_id: int
    person_id: int
    bowl_game_id: int
    line_at_pick: float
    bet_amount: float
    pick_type: str = 'Spread'
    picked_team_id: Optional[int] = None
    picked_value: Optional[str] = None
    is_locked: bool = False
    result: str = 'Pending'
    profit_loss: Optional[float] = 0.0
    is_originator: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
