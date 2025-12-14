import sys
import os
import sqlite3

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.manager import DatabaseManager

def fix_originators():
    print("--- Fixing Retroactive Originators ---")
    db = DatabaseManager("bowlbets.db")
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Strategy:
    # For each series/game combination:
    # Check if ANY pick has is_originator = 1.
    # If not, find the pick for Person 1 (from BettingSeries) and set it to 1.
    
    # 1. Get all series
    cursor.execute("SELECT id, person1_id, person2_id FROM BettingSeries")
    series_list = cursor.fetchall()
    
    updates = 0
    
    for series in series_list:
        sid = series['id']
        p1 = series['person1_id']
        p2 = series['person2_id']
        
        # Get all game IDs with picks in this series
        cursor.execute("SELECT DISTINCT bowl_game_id FROM Pick WHERE betting_series_id = ?", (sid,))
        games = [r['bowl_game_id'] for r in cursor.fetchall()]
        
        for gid in games:
            # Check if originator exists
            cursor.execute("SELECT count(*) as cnt FROM Pick WHERE betting_series_id=? AND bowl_game_id=? AND is_originator=1", (sid, gid))
            count = cursor.fetchone()['cnt']
            
            if count == 0:
                # No originator found. Assume Person 1 is originator.
                print(f"Series {sid}, Game {gid}: No originator. Setting Person {p1} as originator.")
                cursor.execute("""
                    UPDATE Pick 
                    SET is_originator = 1 
                    WHERE betting_series_id = ? AND bowl_game_id = ? AND person_id = ?
                """, (sid, gid, p1))
                updates += cursor.rowcount
                
    conn.commit()
    print(f"Fixed {updates} picks.")

if __name__ == "__main__":
    fix_originators()
