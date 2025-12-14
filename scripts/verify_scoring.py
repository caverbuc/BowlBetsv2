import sys
import os
import sqlite3

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.manager import DatabaseManager
from src.db.repositories import BowlGameRepository, PickRepository
from src.logic.scoring import ScoringEngine, PickResult

def verify_scoring():
    print("--- Starting Scoring Verification ---")
    
    db_manager = DatabaseManager("bowlbets.db")
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Configuration
    SERIES_ID = 6
    PERSON_ID = 1 # Assuming person 1 exists
    
    # 1. Setup Dummy Game Data
    print("Setting up dummy game scores...")
    
    # Game 55: T1 wins big (Cover -3.5)
    # T1 Score 30, T2 Score 10. Spread -3.5. Diff 20. Win.
    cursor.execute("""
        UPDATE BowlGame 
        SET game_status = 'Final', final_score_team1 = 30, final_score_team2 = 10, team1_id=95, team2_id=96
        WHERE id = 55
    """)
    
    # Game 56: T1 loses (Fail cover -7.5)
    # T1 Score 10, T2 Score 20. Spread -7.5. Loss.
    cursor.execute("""
        UPDATE BowlGame 
        SET game_status = 'Final', final_score_team1 = 10, final_score_team2 = 20, team1_id=97, team2_id=98
        WHERE id = 56
    """)
    
    # Game 57: High Score (Over Hits)
    # Score 40-40 (80 total). Line 70.
    cursor.execute("""
        UPDATE BowlGame 
        SET game_status = 'Final', final_score_team1 = 40, final_score_team2 = 40, team1_id=99, team2_id=100
        WHERE id = 57
    """)
    
    conn.commit()
    
    # 2. Clear old picks for these games in this series
    print("Clearing old picks...")
    cursor.execute("DELETE FROM Pick WHERE betting_series_id = ?", (SERIES_ID,))
    conn.commit()
    
    # 3. Insert Test Picks
    print("Inserting test picks...")
    pick_repo = PickRepository(db_manager)
    
    OPPONENT_ID = 2 # Assuming person 2 exists
    
    # Pick 1: Game 55, Spread, Pick Team 1 (95), Line -3.5
    # Expect: Win for P1 (Originator), Loss for P2 (Mirrored)
    pick_repo.create(
        betting_series_id=SERIES_ID, person_id=PERSON_ID, bowl_game_id=55,
        pick_type="Spread", line_at_pick=-3.5, bet_amount=10.0,
        picked_team_id=95, is_originator=True
    )
    pick_repo.create(
        betting_series_id=SERIES_ID, person_id=OPPONENT_ID, bowl_game_id=55,
        pick_type="Spread", line_at_pick=3.5, bet_amount=10.0,
        picked_team_id=96, is_originator=False
    )
    
    # Pick 2: Game 56, Spread, Pick Team 1 (97), Line -7.5
    # Expect: Loss for P1 (Originator), Win for P2
    pick_repo.create(
        betting_series_id=SERIES_ID, person_id=PERSON_ID, bowl_game_id=56,
        pick_type="Spread", line_at_pick=-7.5, bet_amount=10.0,
        picked_team_id=97, is_originator=True
    )
    pick_repo.create(
        betting_series_id=SERIES_ID, person_id=OPPONENT_ID, bowl_game_id=56,
        pick_type="Spread", line_at_pick=7.5, bet_amount=10.0,
        picked_team_id=98, is_originator=False
    )
    
    # Pick 3: Game 57, Over/Under, Pick Over, Line 70.0
    # Expect: Win for P1 (Originator), Loss for P2
    pick_repo.create(
        betting_series_id=SERIES_ID, person_id=PERSON_ID, bowl_game_id=57,
        pick_type="Over/Under", line_at_pick=70.0, bet_amount=10.0,
        picked_value="Over", is_originator=True
    )
    pick_repo.create(
        betting_series_id=SERIES_ID, person_id=OPPONENT_ID, bowl_game_id=57,
        pick_type="Over/Under", line_at_pick=70.0, bet_amount=10.0,
        picked_value="Under", is_originator=False
    )

    # 4. Run Scoring Engine
    print("Running Scoring Engine...")
    game_repo = BowlGameRepository(db_manager)
    engine = ScoringEngine(pick_repo, game_repo)
    updates = engine.process_series_picks(SERIES_ID)
    print(f"Engine reported {updates} updates.")
    
    # 5. Verify Results & Financials
    print("\n--- Verifying Results & Financials ---")
    
    # Fetch picks again
    picks = pick_repo.get_picks_for_series(SERIES_ID)
    
    for pick in picks:
        if pick.person_id == PERSON_ID:
            # Person 1 Checks
            if pick.bowl_game_id == 55:
                expected = "WIN"
                expected_pl = 10.0
            elif pick.bowl_game_id == 56:
                expected = "LOSS"
                expected_pl = -10.0
            elif pick.bowl_game_id == 57:
                expected = "WIN"
                expected_pl = 10.0
            else:
                continue
                
            res_pass = pick.result == expected
            pl_pass = pick.profit_loss == expected_pl
            print(f"P1 Game {pick.bowl_game_id}: Result {pick.result} (Exp:{expected}) [{'PASS' if res_pass else 'FAIL'}]")
        
        elif pick.person_id == OPPONENT_ID:
            # Opponent Checks (Mirrored)
            if pick.bowl_game_id == 55:
                # P1 Won, so P2 Lost
                expected = "LOSS"
            elif pick.bowl_game_id == 56:
                # P1 Lost, so P2 Won
                expected = "WIN"
            elif pick.bowl_game_id == 57:
                # P1 Won, so P2 Lost
                expected = "LOSS"
            else:
                continue
                
            res_pass = pick.result == expected
            print(f"P2 Game {pick.bowl_game_id}: Result {pick.result} (Exp:{expected}) [{'PASS' if res_pass else 'FAIL'}]")

    # 6. Verify Leaderboard Stats
    print("\n--- Verifying Leaderboard Stats ---")
    stats = pick_repo.get_series_stats(SERIES_ID)
    
    # Check Person 1 (P1)
    # Picks: Game 55 (Win, $10), Game 56 (Loss, -$10), Game 57 (Win, $10)
    # Total Games: 3. Record: 2-1-0. Net: +$10.
    # Own Picks: We inserted them without `is_originator`. By default 0.
    # So Own Stats should be 0-0 (0%).
    # WAIT: The script didn't set is_originator. We should update the script to test that too.
    
    s1 = stats.get(PERSON_ID)
    if s1:
        exp_wins = 2
        exp_net = 10.0
        print(f"P1 Record: {s1['wins']}-{s1['losses']} (Exp: 2-1) [{'PASS' if s1['wins']==2 else 'FAIL'}]")
        print(f"P1 Net: ${s1['net_profit']} (Exp: $10.0) [{'PASS' if s1['net_profit']==10.0 else 'FAIL'}]")
        
        if s1['wins'] != 2 or s1['net_profit'] != 10.0:
            print("DEBUG: All picks for Person:")
            ps = pick_repo.get_picks_for_series(SERIES_ID)
            for p in ps:
                if p.person_id == PERSON_ID:
                    print(f" - Game {p.bowl_game_id}: {p.result} (${p.profit_loss})")

    else:
        print("FAIL: No stats for Person 1")

if __name__ == "__main__":
    verify_scoring()
