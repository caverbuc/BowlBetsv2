import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.db.manager import DatabaseManager
from src.logic.import_export import SeriesTransferManager
from src.db.repositories import (
    BettingSeriesRepository, PersonRepository, PickRepository, 
    BowlGameRepository, SeasonRepository, TeamRepository
)

def verify_import_export():
    db_path = "bowlbets.db"
    db_manager = DatabaseManager(db_path)
    
    print("--- Setting up Test Data ---")
    season_repo = SeasonRepository(db_manager)
    series_repo = BettingSeriesRepository(db_manager)
    person_repo = PersonRepository(db_manager)
    pick_repo = PickRepository(db_manager)
    game_repo = BowlGameRepository(db_manager)
    
    # 1. Ensure Season Exists
    season = season_repo.get_by_year(2025)
    if not season:
        print("Creating Season 2024...")
        season = season_repo.create(2025, "Test Season")
    
    # 2. Create Test Series
    print("Creating Test Series...")
    p1 = person_repo.find_by_name("TestExport1") or person_repo.create("TestExport1")
    p2 = person_repo.find_by_name("TestExport2") or person_repo.create("TestExport2")
    
    try:
        series = series_repo.create(season.id, p1.id, p2.id, "AutoTest Export Series")
        print(f"Created Series ID: {series.id}")
    except Exception:
        # Assuming integrity error, find it
        # Simple query or just assume it's the latest one for these ppl?
        # Actually need find method. But for script, let's just create UNIQUE persons each time to be safe?
        # Or just find existing.
        # Let's try to query manually since repo might lack find_by_participants
        conn = db_manager.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM BettingSeries WHERE season_id=? AND person1_id=? AND person2_id=?", 
                  (season.id, p1.id, p2.id))
        row = c.fetchone()
        if row:
            series = series_repo.get_by_id(row[0])
            print(f"Found existing series ID: {series.id}")
        else:
            raise
    
    # 3. Create Picks
    # Find a game
    games = game_repo.get_by_season(season.id)
    if not games:
        print("No games found! Please run main app and Sync first.")
        # Try to find ANY game
        games = game_repo.get_by_season(season_repo.get_all()[0].id)
    
    if not games:
        print("Still no games. Aborting.")
        return

    target_game = games[0] # Pick first game
    print(f"Adding pick for game: {target_game.game_name} (API ID: {target_game.api_cfd_id})")
    
    try:
        pick_repo.create(
            betting_series_id=series.id,
            person_id=p1.id,
            bowl_game_id=target_game.id,
            pick_type="Spread",
            line_at_pick=-3.5,
            bet_amount=5.0,
            picked_team_id=target_game.team1_id,
            is_originator=True
        )
    except Exception as e:
        print(f"Pick creation failed (likely exists): {e}")
    
    # 4. Export
    export_file = "test_export.json"
    print(f"Exporting to {export_file}...")
    manager = SeriesTransferManager(db_manager)
    manager.export_series(series.id, export_file)
    
    # 5. Import
    print("Importing back...")
    new_series_id = manager.import_series(export_file)
    print(f"Imported Series ID: {new_series_id}")
    
    # 6. Verify
    print("Verifying Import...")
    new_series = series_repo.get_by_id(new_series_id)
    print(f"Name: {new_series.name}")
    assert "(Imported)" in new_series.name
    
    imported_picks = pick_repo.get_picks_for_series(new_series_id)
    print(f"Imported Picks Count: {len(imported_picks)}")
    assert len(imported_picks) == 1
    
    imp_pick = imported_picks[0]
    imp_game = game_repo.get_by_id(imp_pick.bowl_game_id)
    print(f"Imported Pick Game: {imp_game.game_name} (API ID: {imp_game.api_cfd_id})")
    
    assert imp_game.api_cfd_id == target_game.api_cfd_id
    print("SUCCESS: Imported pick is linked to the correct game via API ID!")
    
    # Cleanup
    if os.path.exists(export_file):
        os.remove(export_file)
    print("Test Complete.")

if __name__ == "__main__":
    verify_import_export()
