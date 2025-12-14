from datetime import datetime
from src.db.repositories import PickRepository, BowlGameRepository
from src.db.models import Pick, BowlGame
from enum import Enum

class PickResult(Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    PUSH = "PUSH"
    PENDING = "PENDING"
    ERROR = "ERROR"

class ScoringEngine:
    def __init__(self, pick_repo: PickRepository, game_repo: BowlGameRepository):
        self.pick_repo = pick_repo
        self.game_repo = game_repo

    def process_series_picks(self, series_id: int) -> int:
        """
        Iterate through all picks in a series and update their status 
        if the game is final.
        Returns the number of picks updated.
        """
        picks = self.pick_repo.get_picks_for_series(series_id)
        updates_count = 0
        
        for pick in picks:
            # Skip if already finalized (unless we want to allow re-scoring?)
            # Let's allowed re-scoring for now in case logic changes or scores correct.
            # But maybe only if game is Final.
            
            game = self.game_repo.get_by_id(pick.bowl_game_id)
            if not game:
                continue
                
            # Only score matches that are Final
            # Note: Checking "Final" string might need fuzzy match if API varies, 
            # but our sync engine normalizes to "Final".
            status = game.game_status.lower()
            if status != "final" and status != "completed":
                continue
                
            # Calculate Result
            new_result = PickResult.PENDING
            
            if pick.pick_type == "Spread":
                new_result = self.calculate_spread_outcome(pick, game)
            elif pick.pick_type == "Over/Under":
                new_result = self.calculate_ou_outcome(pick, game)
            
            # Calculate Profit/Loss
            profit_loss = 0.0
            if new_result == PickResult.WIN:
                profit_loss = pick.bet_amount
            elif new_result == PickResult.LOSS:
                profit_loss = -pick.bet_amount
            elif new_result == PickResult.PUSH:
                profit_loss = 0.0
            else:
                profit_loss = 0.0 # Error or Pending

            # Update DB (Force update to ensure P/L is set even if result matches but P/L was 0)
            # Or optimization: check if result OR profit_loss differs.
            # pick.profit_loss might be None from DB model if not populated in object yet?
            # Let's perform update to be safe and ensure financial data integrity.
            
            # Use new repository method
            self.pick_repo.update_financials(pick.id, new_result.value, profit_loss)
            
            # Count logical updates (state changes)
            if new_result.value != pick.result:
                updates_count += 1
                
        return updates_count

    @staticmethod
    def calculate_spread_outcome(pick: Pick, game: BowlGame) -> 'PickResult':
        """
        Calculate if a spread bet is a WIN, LOSS, or PUSH.
        Adjusted Score = Picked Team Score + Spread
        If Adjusted Score > Opponent Score -> WIN
        If Adjusted Score < Opponent Score -> LOSS
        If Adjusted Score == Opponent Score -> PUSH
        """
        if pick.pick_type != "Spread":
            return PickResult.ERROR
        
        # Ensure game is final
        if game.final_score_team1 is None or game.final_score_team2 is None:
             # Even if status says Final, we need scores. 
             # If scores are missing, we can't score.
             return PickResult.PENDING

        if not pick.picked_team_id:
            return PickResult.ERROR
            
        # Identify scores
        if pick.picked_team_id == game.team1_id:
            picked_score = game.final_score_team1
            opponent_score = game.final_score_team2
        elif pick.picked_team_id == game.team2_id:
            picked_score = game.final_score_team2
            opponent_score = game.final_score_team1
        else:
            # Picked team not in this game? Data integrity error.
            return PickResult.ERROR

        # Apply spread
        # Note: line_at_pick is typically relative to the favorite.
        # But in our DB, we store the spread value assigned to the picked team? 
        # Let's verify how we store "line_at_pick".
        # In DashboardWidget:
        # if team_id == game.team1_id: line = odds.spread_team1
        # else: line = -odds.spread_team1
        # So `line_at_pick` IS the spread for the picked team.
        # Example: Team A is -3.5. If I pick Team A, line_at_pick is -3.5.
        # Adjusted Score = Team A Score + (-3.5)
        
        adjusted_score = picked_score + pick.line_at_pick
        
        if adjusted_score > opponent_score:
            return PickResult.WIN
        elif adjusted_score < opponent_score:
            return PickResult.LOSS
        else:
            return PickResult.PUSH

    @staticmethod
    def calculate_ou_outcome(pick: Pick, game: BowlGame) -> 'PickResult':
        """
        Calculate if an Over/Under bet is a WIN, LOSS, or PUSH.
        """
        if pick.pick_type != "Over/Under":
            return PickResult.ERROR
        
        if game.final_score_team1 is None or game.final_score_team2 is None:
            return PickResult.PENDING

        total_score = game.final_score_team1 + game.final_score_team2
        line = pick.line_at_pick
        
        if pick.picked_value == "Over":
            if total_score > line:
                return PickResult.WIN
            elif total_score < line:
                return PickResult.LOSS
            else:
                return PickResult.PUSH
        elif pick.picked_value == "Under":
            if total_score < line:
                return PickResult.WIN
            elif total_score > line:
                return PickResult.LOSS
            else:
                return PickResult.PUSH
        else:
            return PickResult.ERROR
