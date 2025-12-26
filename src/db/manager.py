import sqlite3
import os
from typing import Optional

class DatabaseManager:
    def __init__(self, db_path: str = "bowlbets.db"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        if not self._connection:
            self._connection = sqlite3.connect(self.db_path)
            # Enable foreign key support
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as sqlite3.Row objects (dict-like)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def initialize_schema(self):
        """Creates the necessary tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Person Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Person (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Season Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Season (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_year INTEGER UNIQUE NOT NULL,
                display_name TEXT UNIQUE NOT NULL
            )
        """)

        # 3. Team Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Team (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT UNIQUE NOT NULL,
                short_name TEXT UNIQUE NOT NULL,
                mascot TEXT,
                api_cfd_id INTEGER UNIQUE,
                api_theodds_id TEXT UNIQUE
            )
        """)

        # 4. BowlGame Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BowlGame (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                api_cfd_id INTEGER UNIQUE NOT NULL,
                api_theodds_id TEXT UNIQUE,
                game_name TEXT NOT NULL,
                game_date DATETIME NOT NULL,
                location TEXT NOT NULL,
                team1_id INTEGER NOT NULL,
                team2_id INTEGER NOT NULL,
                cfp_tier TEXT NOT NULL,
                game_status TEXT NOT NULL DEFAULT 'Scheduled',
                final_score_team1 INTEGER,
                final_score_team2 INTEGER,
                venue_name TEXT,
                media_outlet TEXT,
                last_api_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES Season(id),
                FOREIGN KEY (team1_id) REFERENCES Team(id),
                FOREIGN KEY (team2_id) REFERENCES Team(id)
            )
        """)

        # 5. BettingSeries Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS BettingSeries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                person1_id INTEGER NOT NULL,
                person2_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                default_bet_amount_regular DECIMAL NOT NULL DEFAULT 5.00,
                default_bet_amount_cfp_semi DECIMAL NOT NULL DEFAULT 10.00,
                default_bet_amount_championship DECIMAL NOT NULL DEFAULT 20.00,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES Season(id),
                FOREIGN KEY (person1_id) REFERENCES Person(id),
                FOREIGN KEY (person2_id) REFERENCES Person(id),
                UNIQUE (season_id, person1_id, person2_id)
            )
        """)

        # 6. Odds Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bowl_game_id INTEGER NOT NULL,
                spread_team1 DECIMAL,
                over_under DECIMAL,
                retrieved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bowl_game_id) REFERENCES BowlGame(id)
            )
        """)

        # 7. Pick Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Pick (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                betting_series_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                bowl_game_id INTEGER NOT NULL,
                pick_type TEXT NOT NULL DEFAULT 'Spread',
                picked_team_id INTEGER,
                picked_value TEXT,
                line_at_pick DECIMAL NOT NULL,
                bet_amount DECIMAL NOT NULL,
                is_locked BOOLEAN NOT NULL DEFAULT 0,
                result TEXT NOT NULL DEFAULT 'Pending',
                profit_loss DECIMAL DEFAULT 0,
                is_originator BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (betting_series_id) REFERENCES BettingSeries(id),
                FOREIGN KEY (person_id) REFERENCES Person(id),
                FOREIGN KEY (bowl_game_id) REFERENCES BowlGame(id),
                FOREIGN KEY (picked_team_id) REFERENCES Team(id),
                UNIQUE (betting_series_id, person_id, bowl_game_id)
            )
        """)
        
        # Check for migrations
        self._check_and_migrate_schema(conn)

        conn.commit()

    def _check_and_migrate_schema(self, conn):
        """Perform simple schema migrations."""
        cursor = conn.cursor()
        
        # Check Pick table columns
        cursor.execute("PRAGMA table_info(Pick)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'profit_loss' not in columns:
            print("Migrating: Adding profit_loss to Pick table")
            cursor.execute("ALTER TABLE Pick ADD COLUMN profit_loss DECIMAL DEFAULT 0")
            
        if 'is_originator' not in columns:
            print("Migrating: Adding is_originator to Pick table")
            cursor.execute("ALTER TABLE Pick ADD COLUMN is_originator BOOLEAN NOT NULL DEFAULT 0")

        # Check Team table columns for logo_url
        cursor.execute("PRAGMA table_info(Team)")
        columns = [info[1] for info in cursor.fetchall()]

        if 'logo_url' not in columns:
            print("Migrating: Adding logo_url to Team table")
            cursor.execute("ALTER TABLE Team ADD COLUMN logo_url TEXT")
            
        # Check BowlGame table columns for venue_name and media_outlet
        cursor.execute("PRAGMA table_info(BowlGame)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'venue_name' not in columns:
            print("Migrating: Adding venue_name to BowlGame table")
            cursor.execute("ALTER TABLE BowlGame ADD COLUMN venue_name TEXT")
            
        if 'media_outlet' not in columns:
            print("Migrating: Adding media_outlet to BowlGame table")
            cursor.execute("ALTER TABLE BowlGame ADD COLUMN media_outlet TEXT")
