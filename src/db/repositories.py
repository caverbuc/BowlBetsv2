from typing import Optional
from src.db.manager import DatabaseManager
from src.db.models import Person, Season, Team, BowlGame, BettingSeries, Odds, Pick

class BaseRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

class PersonRepository(BaseRepository):
    def create(self, name: str) -> Person:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Person (name) VALUES (?)", (name,))
            conn.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError:
            raise ValueError(f"Person with name '{name}' already exists.")

    
    def find_by_name(self, name: str) -> Optional[Person]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Person WHERE name = ?", (name,))
        row = cursor.fetchone()
        return Person(**dict(row)) if row else None
        
    def get_by_id(self, person_id: int) -> Optional[Person]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Person WHERE id = ?", (person_id,))
        row = cursor.fetchone()
        if row:
            return Person(**dict(row))
        return None

    def get_all(self) -> list[Person]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Person ORDER BY name")
        return [Person(**dict(row)) for row in cursor.fetchall()]

class SeasonRepository(BaseRepository):
    def create(self, start_year: int, display_name: str) -> Season:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Season (start_year, display_name) VALUES (?, ?)", 
                           (start_year, display_name))
            conn.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError:
            raise ValueError(f"Season '{start_year}' already exists.")

    def get_by_id(self, season_id: int) -> Optional[Season]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Season WHERE id = ?", (season_id,))
        row = cursor.fetchone()
        return Season(**dict(row)) if row else None
    
    def get_by_year(self, start_year: int) -> Optional[Season]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Season WHERE start_year = ?", (start_year,))
        row = cursor.fetchone()
        return Season(**dict(row)) if row else None

    def get_all(self) -> list[Season]:
        """Get all seasons."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Season ORDER BY start_year DESC")
        return [Season(**dict(row)) for row in cursor.fetchall()]

class TeamRepository(BaseRepository):
    def create(self, canonical_name: str, short_name: str, mascot: str = None) -> Team:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Team (canonical_name, short_name, mascot) VALUES (?, ?, ?)",
            (canonical_name, short_name, mascot)
        )
        conn.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, team_id: int) -> Optional[Team]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Team WHERE id = ?", (team_id,))
        row = cursor.fetchone()
        return Team(**dict(row)) if row else None

    def update_logo(self, team_id: int, logo_url: str):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Team SET logo_url = ? WHERE id = ?", (logo_url, team_id))
        conn.commit()

    def find_by_name(self, name: str) -> Optional[Team]:
         cursor = self.db.get_connection().cursor()
         cursor.execute("SELECT * FROM Team WHERE canonical_name = ? OR short_name = ?", (name, name))
         row = cursor.fetchone()
         return Team(**dict(row)) if row else None

    def upsert_from_api(self, cfd_id: int, name: str, mascot: str = None) -> Team:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Try to match by CFD ID first (most reliable)
        cursor.execute("SELECT * FROM Team WHERE api_cfd_id = ?", (cfd_id,))
        row = cursor.fetchone()
        
        if row:
            # Update if needed (e.g. name change? maybe not worth it, but let's keep it fresh)
            cursor.execute("UPDATE Team SET canonical_name=?, mascot=? WHERE api_cfd_id=?", (name, mascot, cfd_id))
            conn.commit()
            return Team(**dict(row))
            
        # If no ID match, try Name match (to link manually created teams? maybe risky)
        # For now, let's assume if it has no CFD ID, it's a new team or we trust CFD ID.
        # Actually, if we have a team with same name but no CFD ID, we should update it.
        cursor.execute("SELECT * FROM Team WHERE canonical_name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("UPDATE Team SET api_cfd_id=?, mascot=? WHERE id=?", (cfd_id, mascot, row['id']))
            conn.commit()
            return self.get_by_id(row['id'])
            
        # Create new
        cursor.execute(
            "INSERT INTO Team (canonical_name, short_name, mascot, api_cfd_id) VALUES (?, ?, ?, ?)",
            (name, name, mascot, cfd_id)
        )
        conn.commit()
        return self.get_by_id(cursor.lastrowid)
    def get_all(self) -> list[Team]:
        """Get all teams."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Team ORDER BY canonical_name")
        return [Team(**dict(row)) for row in cursor.fetchall()]

class BettingSeriesRepository(BaseRepository):
    def create(self, season_id: int, person1_id: int, person2_id: int, name: str, 
               reg_amt: float=5.0, semi_amt: float=10.0, champ_amt: float=20.0) -> BettingSeries:
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO BettingSeries 
            (season_id, person1_id, person2_id, name, 
             default_bet_amount_regular, default_bet_amount_cfp_semi, default_bet_amount_championship)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (season_id, person1_id, person2_id, name, reg_amt, semi_amt, champ_amt))
        conn.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, series_id: int) -> Optional[BettingSeries]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM BettingSeries WHERE id = ?", (series_id,))
        row = cursor.fetchone()
        return BettingSeries(**dict(row)) if row else None

    def get_all(self) -> list[BettingSeries]:
        """Get all betting series."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM BettingSeries ORDER BY created_at DESC")
        return [BettingSeries(**dict(row)) for row in cursor.fetchall()]

    def get_by_season(self, season_id: int) -> list[BettingSeries]:
        """Get all betting series for a specific season."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM BettingSeries WHERE season_id = ?", (season_id,))
        return [BettingSeries(**dict(row)) for row in cursor.fetchall()]

class BowlGameRepository(BaseRepository):
    def upsert(self, season_id: int, api_cfd_id: int, game_name: str, game_date: str, 
               location: str, team1_id: int, team2_id: int, cfp_tier: str, 
               status: str, fs1: Optional[int], fs2: Optional[int],
               venue_name: Optional[str] = None, media_outlet: Optional[str] = None) -> BowlGame:
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM BowlGame WHERE api_cfd_id = ?", (api_cfd_id,))
        row = cursor.fetchone()
        
        if row:
            # Update
            cursor.execute("""
                UPDATE BowlGame SET 
                game_name=?, game_date=?, location=?, team1_id=?, team2_id=?, 
                cfp_tier=?, game_status=?, final_score_team1=?, final_score_team2=?, 
                venue_name=?, media_outlet=?, last_api_update=CURRENT_TIMESTAMP
                WHERE api_cfd_id=?
            """, (game_name, game_date, location, team1_id, team2_id, cfp_tier, status, fs1, fs2, 
                  venue_name, media_outlet, api_cfd_id))
            game_id = row['id']
        else:
            # Insert
            cursor.execute("""
                INSERT INTO BowlGame (season_id, api_cfd_id, game_name, game_date, location, 
                                    team1_id, team2_id, cfp_tier, game_status, 
                                    final_score_team1, final_score_team2, venue_name, media_outlet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (season_id, api_cfd_id, game_name, game_date, location, 
                  team1_id, team2_id, cfp_tier, status, fs1, fs2, venue_name, media_outlet))
            game_id = cursor.lastrowid
            
        conn.commit()
        return self.get_by_id(game_id)

    def get_by_id(self, game_id: int) -> Optional[BowlGame]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM BowlGame WHERE id = ?", (game_id,))
        row = cursor.fetchone()
        return BowlGame(**dict(row)) if row else None

    def get_by_season(self, season_id: int) -> list[BowlGame]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM BowlGame WHERE season_id = ? ORDER BY game_date", (season_id,))
        return [BowlGame(**dict(row)) for row in cursor.fetchall()]

    def get_all(self) -> list[BowlGame]:
        """Get all bowl games."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM BowlGame ORDER BY game_date")
        return [BowlGame(**dict(row)) for row in cursor.fetchall()]

class OddsRepository(BaseRepository):
    def update_odds(self, game_id: int, spread_team1: float, over_under: float) -> Odds:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # We store history in the Odds table, so we always INSERT a new record for history?
        # Or do we update the latest? The PRD says "Stores historical odds data".
        # But for v1 simplicity and dashboard display, we usually want the *latest*.
        # Let's Insert a new row every time we fetch meaningful change, or just update query.
        # Actually, let's keep it simple: Insert new row.
        
        cursor.execute("""
            INSERT INTO Odds (bowl_game_id, spread_team1, over_under)
            VALUES (?, ?, ?)
        """, (game_id, spread_team1, over_under))
        conn.commit()
        return Odds(id=cursor.lastrowid, bowl_game_id=game_id, spread_team1=spread_team1, over_under=over_under)

    def get_latest_for_game(self, game_id: int) -> Optional[Odds]:
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT * FROM Odds 
            WHERE bowl_game_id = ? 
            ORDER BY retrieved_at DESC 
            LIMIT 1
        """, (game_id,))
        row = cursor.fetchone()
        return Odds(**dict(row)) if row else None

class PickRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create(self, betting_series_id: int, person_id: int, bowl_game_id: int,
               pick_type: str, line_at_pick: float, bet_amount: float,
               picked_team_id: Optional[int] = None, picked_value: Optional[str] = None,
               is_originator: bool = False) -> Pick:
        """Create a new pick."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Pick 
            (betting_series_id, person_id, bowl_game_id, pick_type, 
             picked_team_id, picked_value, line_at_pick, bet_amount, is_originator)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (betting_series_id, person_id, bowl_game_id, pick_type,
              picked_team_id, picked_value, line_at_pick, bet_amount, is_originator))
        
        conn.commit()
        pick_id = cursor.lastrowid
        
        return Pick(
            id=pick_id,
            betting_series_id=betting_series_id,
            person_id=person_id,
            bowl_game_id=bowl_game_id,
            pick_type=pick_type,
            picked_team_id=picked_team_id,
            picked_value=picked_value,
            line_at_pick=line_at_pick,
            bet_amount=bet_amount,
            is_originator=is_originator
        )
    
    def get_by_id(self, pick_id: int) -> Optional[Pick]:
        """Get a pick by ID."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT * FROM Pick WHERE id = ?", (pick_id,))
        row = cursor.fetchone()
        return Pick(**dict(row)) if row else None
    
    def get_picks_for_series(self, series_id: int) -> list[Pick]:
        """Get all picks for a betting series."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT * FROM Pick 
            WHERE betting_series_id = ?
            ORDER BY created_at DESC
        """, (series_id,))
        rows = cursor.fetchall()
        return [Pick(**dict(row)) for row in rows]
    
    def get_picks_for_game(self, series_id: int, game_id: int) -> list[Pick]:
        """Get all picks for a specific game in a series."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT * FROM Pick 
            WHERE betting_series_id = ? AND bowl_game_id = ?
        """, (series_id, game_id))
        rows = cursor.fetchall()
        return [Pick(**dict(row)) for row in rows]
    
    def update_pick_line(self, pick_id: int, new_line: float):
        """Update the line for a specific pick."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Pick 
            SET line_at_pick = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (new_line, pick_id))
        conn.commit()
    
    def get_pick_for_game(self, series_id: int, person_id: int, game_id: int) -> Optional[Pick]:
        """Get a specific person's pick for a game in a series."""
        cursor = self.db.get_connection().cursor()
        cursor.execute("""
            SELECT * FROM Pick 
            WHERE betting_series_id = ? AND person_id = ? AND bowl_game_id = ?
        """, (series_id, person_id, game_id))
        row = cursor.fetchone()
        return Pick(**dict(row)) if row else None
        
    def update_financials(self, pick_id: int, result: str, profit_loss: float):
        """Update result and profit/loss of a pick."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Pick 
            SET result = ?, profit_loss = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (result, profit_loss, pick_id))
        conn.commit()

    def get_series_stats(self, series_id: int) -> dict:
        """
        Calculate stats for each person in a series.
        Returns: {person_id: {
            'wins': int, 'losses': int, 'pushes': int, 'pending': int, 
            'net_profit': float, 'total_games': int,
            'own_wins': int, 'own_losses': int, 'own_total': int
        }}
        """
        picks = self.get_picks_for_series(series_id)
        stats = {}
        
        for pick in picks:
            pid = pick.person_id
            if pid not in stats:
                stats[pid] = {
                    'wins': 0, 'losses': 0, 'pushes': 0, 'pending': 0, 
                    'net_profit': 0.0, 'total_games': 0,
                    'own_wins': 0, 'own_losses': 0, 'own_total': 0
                }
            
            s = stats[pid]
            res = pick.result
            
            if res == 'WIN':
                s['wins'] += 1
                s['total_games'] += 1
                if pick.is_originator:
                    s['own_wins'] += 1
                    s['own_total'] += 1
            elif res == 'LOSS':
                s['losses'] += 1
                s['total_games'] += 1
                if pick.is_originator:
                    s['own_losses'] += 1
                    s['own_total'] += 1
            elif res == 'PUSH':
                s['pushes'] += 1
                s['total_games'] += 1
                if pick.is_originator:
                    s['own_total'] += 1 # Count push in total for % calculation or not? Usually push excludes from %. Let's count as total but not win/loss.
            else:
                s['pending'] += 1
                if pick.is_originator:
                    pass # Don't count pending in "own total" (games played)
            
            if pick.profit_loss:
                s['net_profit'] += pick.profit_loss
                
        return stats

