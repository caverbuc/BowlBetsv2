import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.manager import DatabaseManager

def main():
    print("Initializing database...")
    db = DatabaseManager("test_bowlbets.db")
    try:
        db.initialize_schema()
        print("Schema initialized successfully.")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verify table existence
        tables = ["Person", "Season", "Team", "BowlGame", "BettingSeries", "Odds", "Pick"]
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"Table '{table}' exists.")
            else:
                print(f"ERROR: Table '{table}' missing!")
                
    except Exception as e:
        print(f"Database initialization failed: {e}")
    finally:
        db.close()
        # Cleanup
        if os.path.exists("test_bowlbets.db"):
            os.remove("test_bowlbets.db")
            print("Cleanup: Removed test DB.")

if __name__ == "__main__":
    main()
