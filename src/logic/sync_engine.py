from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QThread
from typing import Dict, List
import logging
import json

from src.db.manager import DatabaseManager
from src.db.repositories import TeamRepository, BowlGameRepository, OddsRepository, SeasonRepository
from src.api.cfd import CollegeFootballDataAPI

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

            if not cfd_key:
                self.finished.emit(False, "Missing CollegeFootballData API Key.", [])
                return

            cfd_api = CollegeFootballDataAPI(cfd_key)

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

            # 2. Fetch all data in bulk
            self.progress.emit("Fetching all games, betting lines, venues, and media from CFD API...")
            games = cfd_api.get_postseason_games(current_year)
            games.extend(cfd_api.get_postseason_games(current_year + 1))
            logging.info(f"Raw games response (first 5): {json.dumps(games[:5], indent=2)}")
            
            lines = cfd_api.get_betting_lines(year=current_year, season_type="postseason")
            lines.extend(cfd_api.get_betting_lines(year=current_year + 1, season_type="postseason"))
            logging.info(f"Raw betting lines response (first 5): {json.dumps(lines[:5], indent=2)}")

            venues = cfd_api.get_venues()
            game_media = cfd_api.get_game_media(year=current_year, season_type="postseason")
            game_media.extend(cfd_api.get_game_media(year=current_year + 1, season_type="postseason"))
            logging.info(f"Raw game media response (first 5): {json.dumps(game_media[:5], indent=2)}")

            # Create lookups for efficient access
            lines_by_game_id = {game_line['id']: game_line for game_line in lines}
            venues_by_id = {venue['id']: venue for venue in venues}
            media_by_game_id = {media_item['id']: media_item for media_item in game_media}

            # 3. Process and Upsert Data
            new_odds_list = []
            mapped_count = 0

            if not games:
                self.progress.emit("No games found or API error.")
            else:
                self.progress.emit(f"Processing {len(games)} games...")
                
                for g in games:
                    logging.info(f"Processing game: ID={g.get('id')}, Name={g.get('game_name')}, Home={g.get('homeTeam')}, Away={g.get('awayTeam')}")
                    # Validate Data
                    if not g.get('homeTeam') or not g.get('awayTeam'):
                        logging.warning(f"Skipping game {g.get('id')} due to missing team info.")
                        continue
                        
                    # Filter for FBS only
                    if g.get('homeClassification') != 'fbs' or g.get('awayClassification') != 'fbs':
                        logging.info(f"Skipping non-FBS game {g.get('id')} ({g.get('homeTeam')} vs {g.get('awayTeam')})")
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

                    # Get venue name
                    venue_name = g.get('venue', 'Unknown')
                    if g.get('venueId') and g['venueId'] in venues_by_id:
                        venue_name = venues_by_id[g['venueId']].get('name', venue_name)
                    
                    # Get media outlet
                    media_outlet = None
                    if g.get('id') in media_by_game_id:
                        media_outlet = media_by_game_id[g['id']].get('outlet', None)

                    # Upsert Game
                    db_game = self.game_repo.upsert(
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
                        fs2=g.get('awayPoints'),
                        venue_name=venue_name,
                        media_outlet=media_outlet
                    )
                    logging.info(f"Upserted game {db_game.game_name} (DB ID: {db_game.id}, CFD ID: {db_game.api_cfd_id})")

                    # 4. Sync Odds using CFD API
                    if db_game.api_cfd_id in lines_by_game_id:
                        line_data = lines_by_game_id[db_game.api_cfd_id]
                        logging.info(f"Found line data for game {db_game.api_cfd_id}: {json.dumps(line_data, indent=2)}")
                        
                        # Find the first available line
                        line_record = line_data.get('lines', [])[0] if line_data.get('lines') else None
                        
                        if line_record:
                            spread_team1 = None
                            over_under = None

                            if line_record.get('spread') is not None:
                                # Spread is for the home team, and t1 is always the home team
                                spread_team1 = line_record['spread']
                            
                            logging.info(f"Extracted spread_team1: {spread_team1}")

                            if line_record.get('overUnder') is not None:
                                over_under = line_record['overUnder']
                            
                            logging.info(f"Extracted over_under: {over_under}")

                            if spread_team1 is not None or over_under is not None:
                                from src.db.models import Odds
                                new_odds_list.append(Odds(id=None, bowl_game_id=db_game.id, spread_team1=spread_team1, over_under=over_under))
                                mapped_count += 1
                                logging.info(f"Added new odds for game {db_game.game_name}: Spread={spread_team1}, O/U={over_under}")
                        else:
                            logging.info(f"No valid line record found for game {db_game.game_name} (CFD ID: {db_game.api_cfd_id}) in line_data.")
                    else:
                        logging.info(f"No line data found in lines_by_game_id for game {db_game.game_name} (CFD ID: {db_game.api_cfd_id}).")
                
                self.progress.emit(f"Processed {len(games)} games, found {mapped_count} odds.")

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
