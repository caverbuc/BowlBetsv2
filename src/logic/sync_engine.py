from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QThread
from typing import Dict, List
import logging

from src.db.manager import DatabaseManager
from src.db.repositories import TeamRepository, BowlGameRepository, OddsRepository, SeasonRepository
from src.api.cfd import CollegeFootballDataAPI
from src.api.odds import TheOddsAPI

class SyncWorker(QObject):
    """
    Worker class to run sync in a separate thread.
    """
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, list) # success, message, new_odds

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.settings = QSettings("BowlBets", "BowlBetsV2")
        # Repos initialized in run() to use thread-local DB connection

    def run(self):
        # Create thread-local DB manager and connection
        db_manager = DatabaseManager(self.db_path)
        
        self.team_repo = TeamRepository(db_manager)
        self.game_repo = BowlGameRepository(db_manager)
        self.odds_repo = OddsRepository(db_manager)
        self.season_repo = SeasonRepository(db_manager)

        try:
            self.progress.emit("Initializing API Clients...")
            cfd_key = self.settings.value("api_keys/cfd", "")
            odds_key = self.settings.value("api_keys/theodds", "")

            if not cfd_key:
                self.finished.emit(False, "Missing CollegeFootballData API Key.")
                return

            cfd_api = CollegeFootballDataAPI(cfd_key)
            odds_api = TheOddsAPI(odds_key) if odds_key else None

            # 0. Sync All Teams to get logos
            self.progress.emit("Fetching all teams from CFD...")
            all_teams_data = cfd_api.get_teams()
            teams_by_id = {team['id']: team for team in all_teams_data}

            # 1. Get Current Season
            # Using 2025 for the current active season (Dec 2025)
            # In a real app we'd get this from settings or current date
            current_year = 2025
            season = self.season_repo.get_by_year(current_year)
            if not season:
                season = self.season_repo.create(current_year, f"{current_year}-{current_year+1} Bowl Season")

            # 2. Sync Games from CFD
            self.progress.emit("Fetching Bowl Games from CFD...")
            games = cfd_api.get_postseason_games(current_year)
            
            if not games:
                self.progress.emit("No games found or API error.")
            else:
                self.progress.emit(f"Processing {len(games)} games...")
                for g in games:
                    # CFD Game Structure assumption:
                    # { 'id': 123, 'season': 2024, 'home_team': '...', 'home_id': 1, 'away_team': '...', 'away_id': 2, 'start_date': '...', 'venue': '...', ... }
                    
                    
                    # Validate Data
                    if not g.get('homeTeam') or not g.get('awayTeam'):
                        print(f"Skipping game {g.get('id')} due to missing team info.")
                        continue
                        
                    # Filter for FBS only
                    if g.get('homeClassification') != 'fbs' or g.get('awayClassification') != 'fbs':
                        print(f"Skipping non-FBS game {g.get('id')} ({g.get('homeTeam')} vs {g.get('awayTeam')})")
                        continue

                    # Upsert Teams
                    t1 = self.team_repo.upsert_from_api(g.get('homeId'), g.get('homeTeam'), g.get('homeConference'))
                    t2 = self.team_repo.upsert_from_api(g.get('awayId'), g.get('awayTeam'), g.get('awayConference'))
                    
                    # Update Logos
                    if t1 and t1.api_cfd_id in teams_by_id:
                        team_data = teams_by_id[t1.api_cfd_id]
                        if team_data.get('logos'):
                            self.team_repo.update_logo(t1.id, team_data['logos'][0])

                    if t2 and t2.api_cfd_id in teams_by_id:
                        team_data = teams_by_id[t2.api_cfd_id]
                        if team_data.get('logos'):
                            self.team_repo.update_logo(t2.id, team_data['logos'][0])

                    # Determine Tier (Simplified logic)
                    tier = "Regular"
                    notes = g.get('notes', '').lower() if g.get('notes') else ''
                    name_lower = g.get('game_name', '').lower() if g.get('game_name') else ''

                    if 'championship' in notes or 'championship' in name_lower:
                        tier = "Championship"
                    elif 'semifinal' in notes or 'semi-final' in notes or 'semifinal' in name_lower or 'semi-final' in name_lower:
                        tier = "CFP Semifinal"
                    elif 'quarterfinal' in notes or 'quarter-final' in notes or 'quarterfinal' in name_lower or 'quarter-final' in name_lower:
                        tier = "CFP Quarterfinal"
                    elif 'first round' in notes or 'first round' in name_lower:
                        tier = "CFP First Round"
                    elif 'playoff' in notes or 'playoff' in name_lower:
                        tier = "CFP"

                    
                    # Upsert Game
                    self.game_repo.upsert(
                        season_id=season.id,
                        api_cfd_id=g['id'],
                        game_name=notes if notes else f"{t1.short_name} vs {t2.short_name}",
                        game_date=g.get('startDate'),
                        location=g.get('venue', 'Unknown'),
                        team1_id=t1.id,
                        team2_id=t2.id,
                        cfp_tier=tier,
                        status="Completed" if g.get('completed') else "Scheduled",
                        fs1=g.get('homePoints'),
                        fs2=g.get('awayPoints')
                    )

            # 3. Sync Odds
            new_odds_list = []
            if odds_api:
                self.progress.emit("Fetching Odds from TheOddsAPI...")
                odds_events = odds_api.get_odds()
                
                mapped_count = 0
                for event in odds_events:
                    # Match event to game
                    # Event has 'home_team', 'away_team'
                    home_name = event.get('home_team')
                    away_name = event.get('away_team')
                    
                    # Find game in DB
                    # Naive match: Check matching team names in current season games
                    db_games = self.game_repo.get_by_season(season.id)
                    
                    matched_game = None
                    for dbg in db_games:
                        # Need to load team names for the game
                        t1 = self.team_repo.get_by_id(dbg.team1_id)
                        t2 = self.team_repo.get_by_id(dbg.team2_id)
                        
                        # Check loose match (containment)
                        # e.g. "Army" in "Army Black Knights" or vice versa
                        # Normalize a bit (lower case)
                        
                        def match_names(n1, n2):
                            if not n1 or not n2: return False
                            n1 = n1.lower()
                            n2 = n2.lower()
                            return n1 in n2 or n2 in n1

                        # We need to match BOTH teams to confirm game
                        # Matches could be (T1=Home, T2=Away) OR (T1=Away, T2=Home)
                        
                        match_home = match_names(t1.canonical_name, home_name)
                        match_away = match_names(t2.canonical_name, away_name)
                        
                        if match_home and match_away:
                            matched_game = dbg
                            break
                            
                        # Try swapped
                        match_home_swapped = match_names(t2.canonical_name, home_name)
                        match_away_swapped = match_names(t1.canonical_name, away_name)
                        
                        if match_home_swapped and match_away_swapped:
                            matched_game = dbg
                            break
                    
                    if matched_game:
                        # Parse Odds
                        # Structure: event['bookmakers'][0]['markets'][0]['outcomes']...
                        # Using first available bookmaker (typically DraftKings, FanDuel, etc.)
                        bookmakers = event.get('bookmakers', [])
                        if bookmakers:
                            bookmaker_name = bookmakers[0].get('title', 'Unknown')
                            markets = bookmakers[0].get('markets', [])
                            spreads = next((m for m in markets if m['key'] == 'spreads'), None)
                            totals = next((m for m in markets if m['key'] == 'totals'), None)
                            
                            sp_val = None
                            ou_val = None
                            
                            if spreads:
                                # outcomes: [{'name': 'TeamA', 'price': 1.9, 'point': -3.5}, ...]
                                # We need spread relative to Team1
                                # Find outcome for Team1 using fuzzy matching
                                t1_obj = self.team_repo.get_by_id(matched_game.team1_id)
                                
                                def match_names(n1, n2):
                                    if not n1 or not n2: return False
                                    n1 = n1.lower()
                                    n2 = n2.lower()
                                    return n1 in n2 or n2 in n1
                                
                                for out in spreads['outcomes']:
                                    # Fuzzy match outcome name to team name
                                    if match_names(t1_obj.canonical_name, out['name']):
                                        sp_val = out['point']
                                        break
                            
                            if totals:
                                # outcomes: [{'name': 'Over', 'point': 45.5}, ...]
                                if totals['outcomes']:
                                    ou_val = totals['outcomes'][0]['point']
                            
                            if sp_val is not None or ou_val is not None:
                                # Instead of updating the DB, add to the list
                                from src.db.models import Odds
                                new_odds_list.append(Odds(id=None, bowl_game_id=matched_game.id, spread_team1=sp_val, over_under=ou_val))
                                mapped_count += 1

                self.progress.emit(f"Odds synced from {bookmaker_name if bookmakers else 'API'}. Matched {mapped_count} games.")
            else:
                self.progress.emit("No Odds API Key provided. Skipping odds.")

            self.finished.emit(True, "Sync Completed Successfully.", new_odds_list)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, f"Sync Failed: {str(e)}", [])

class SyncManager:
    """
    Manager to handle the thread lifecycle.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.thread = None
        self.worker = None

    def start_sync(self, on_progress, on_finished):
        self.thread = QThread()
        self.worker = SyncWorker(self.db_manager.db_path)
        self.worker.moveToThread(self.thread)
        
        self.worker.progress.connect(on_progress)
        self.worker.finished.connect(on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.started.connect(self.worker.run)
        self.thread.start()
