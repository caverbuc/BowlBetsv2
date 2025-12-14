import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from src.db.manager import DatabaseManager
from src.db.repositories import (
    BettingSeriesRepository, PersonRepository, PickRepository, 
    BowlGameRepository, SeasonRepository, TeamRepository
)
from src.db.models import BettingSeries, Person, Pick, BowlGame, Season

class SeriesTransferManager:
    """
    Handles exporting a BettingSeries to JSON and importing it back.
    Ensures that the imported series remains 'live' by linking to local Game records via API IDs.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.series_repo = BettingSeriesRepository(db_manager)
        self.person_repo = PersonRepository(db_manager)
        self.pick_repo = PickRepository(db_manager)
        self.game_repo = BowlGameRepository(db_manager)
        self.season_repo = SeasonRepository(db_manager)
        self.team_repo = TeamRepository(db_manager)

    def export_series(self, series_id: int, filepath: str) -> bool:
        """
        Export a series and its picks to a JSON file.
        """
        series = self.series_repo.get_by_id(series_id)
        if not series:
            raise ValueError(f"Series ID {series_id} not found.")

        # 1. Fetch related data
        season = self.season_repo.get_by_id(series.season_id)
        p1 = self.person_repo.get_by_id(series.person1_id)
        p2 = self.person_repo.get_by_id(series.person2_id)
        picks = self.pick_repo.get_picks_for_series(series_id)

        # 2. Build JSON Structure
        data = {
            "metadata": {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
            },
            "season": {
                "year": season.start_year,
                "name": season.display_name
            },
            "series": {
                "name": series.name,
                "default_bet_amount_regular": series.default_bet_amount_regular,
                "default_bet_amount_cfp_semi": series.default_bet_amount_cfp_semi,
                "default_bet_amount_championship": series.default_bet_amount_championship
            },
            "persons": [
                {"original_id": p1.id, "name": p1.name},
                {"original_id": p2.id, "name": p2.name}
            ],
            "picks": []
        }

        # 3. Serialize Picks (using Game API ID for portability)
        for pick in picks:
            game = self.game_repo.get_by_id(pick.bowl_game_id)
            if not game:
                continue # Should not happen

            pick_data = {
                "game_api_cfd_id": game.api_cfd_id,
                "game_name": game.game_name, # Fallback
                "person_original_id": pick.person_id,
                "pick_type": pick.pick_type,
                "picked_team_name": None,
                "picked_value": pick.picked_value,
                "line_at_pick": pick.line_at_pick,
                "bet_amount": pick.bet_amount,
                "is_originator": pick.is_originator,
                "timestamp": pick.updated_at.isoformat() if hasattr(pick.updated_at, 'isoformat') else str(pick.updated_at or datetime.now().isoformat())
            }

            # If strictly team pick, resolve team name/API ID
            if pick.picked_team_id:
                team = self.team_repo.get_by_id(pick.picked_team_id)
                if team:
                    pick_data["picked_team_name"] = team.canonical_name
                    pick_data["picked_team_cfd_id"] = team.api_cfd_id

            data["picks"].append(pick_data)

        # 4. Write to File
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        
        return True

    def import_series(self, filepath: str) -> int:
        """
        Import a series from JSON. Returns the new Series ID.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, 'r') as f:
            data = json.load(f)

        # 1. Resolve Season
        season_year = data["season"]["year"]
        season = self.season_repo.get_by_year(season_year)
        if not season:
            # Maybe auto-create? Or fail? Better to fail if season data missing.
            # But let's try to find any season or just create a placeholder if desperate.
            # Ideally user has synced data.
            raise ValueError(f"Season {season_year} not found in database. Please sync data first.")

        # 2. Create Persons (Names + ' (Imported)')
        # Map original_id -> new_id
        person_map = {}
        for p_data in data["persons"]:
            orig_id = p_data["original_id"]
            name = p_data["name"]
            
            # Simple conflict resolution: append (Imported)
            # Or assume if exporting to a friend, they are "Friend"
            # Let's verify if name exists. If so, create new anyway to avoid mixing data?
            # User request: "share a series".
            # If I import "Cutler vs Jim", and I am Jim, I might want to map "Jim" to ME.
            # But that's complicated UI.
            # Simple Default: Create "Name (Imported)" unique persons for this series.
            
            new_name = f"{name} (Imported)"
            # Ensure uniqueness just in case
            if self.person_repo.find_by_name(new_name):
                 new_name = f"{name} (Imported {datetime.now().strftime('%H%M%S')})"
            
            new_person = self.person_repo.create(new_name)
            person_map[orig_id] = new_person.id

        # 3. Create Series
        s_data = data["series"]
        new_series = self.series_repo.create(
            season_id=season.id,
            person1_id=person_map[data["persons"][0]["original_id"]],
            person2_id=person_map[data["persons"][1]["original_id"]],
            name=f"{s_data['name']} (Imported)",
            reg_amt=s_data["default_bet_amount_regular"],
            semi_amt=s_data["default_bet_amount_cfp_semi"],
            champ_amt=s_data["default_bet_amount_championship"]
        )

        # 4. Import Picks
        for p_data in data["picks"]:
            # Find Game
            game = None
            if p_data.get("game_api_cfd_id"):
                 # Need a repository method to find by API ID
                 # I'll add find_by_api_id to BowlGameRepo or use raw query here
                 games = self.game_repo.get_by_season(season.id)
                 for g in games:
                     if g.api_cfd_id == p_data["game_api_cfd_id"]:
                         game = g
                         break
            
            # Fallback by name
            if not game:
                # Try fuzzy name match? or exact
                games = self.game_repo.get_by_season(season.id)
                for g in games:
                    if g.game_name == p_data["game_name"]:
                         game = g
                         break
            
            if not game:
                print(f"Warning: Could not link game {p_data.get('game_name')} - skipping pick.")
                continue

            # Resolve Team (for Spread picks)
            picked_team_id = None
            if p_data.get("picked_team_name"):
                 # Try to find team locally
                 team = self.team_repo.find_by_name(p_data["picked_team_name"])
                 if team:
                     picked_team_id = team.id
            
            # Create Pick
            new_person_id = person_map.get(p_data["person_original_id"])
            if not new_person_id:
                continue

            self.pick_repo.create(
                betting_series_id=new_series.id,
                person_id=new_person_id,
                bowl_game_id=game.id,
                pick_type=p_data["pick_type"],
                line_at_pick=p_data["line_at_pick"],
                bet_amount=p_data["bet_amount"],
                picked_team_id=picked_team_id,
                picked_value=p_data["picked_value"],
                is_originator=p_data.get("is_originator", False)
            )

        return new_series.id
