import unittest
from datetime import datetime
from src.logic.scoring import ScoringEngine, PickResult
from src.db.models import Pick, BowlGame

class TestScoringEngine(unittest.TestCase):
    
    def setUp(self):
        # Create a dummy game
        self.game = BowlGame(
            id=1, season_id=2024, api_cfd_id=1, api_theodds_id="key",
            game_name="Test Bowl", game_date=datetime.now(), location="Stadium",
            team1_id=101, team2_id=102, cfp_tier="Non-CFP",
            game_status="Final", 
            final_score_team1=24, # Team 1 Score
            final_score_team2=20, # Team 2 Score
            last_api_update=datetime.now()
        )
        
    def test_spread_favorite_covers(self):
        # Team 1 wins by 4. Spread is -3. Should Cover.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=-3.0, bet_amount=100, pick_type="Spread",
            picked_team_id=101 # Team 1
        )
        result = ScoringEngine.calculate_spread_outcome(pick, self.game)
        self.assertEqual(result, PickResult.WIN)
        
    def test_spread_favorite_fails_cover(self):
        # Team 1 wins by 4. Spread is -7. Should Lose.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=-7.0, bet_amount=100, pick_type="Spread",
            picked_team_id=101 # Team 1
        )
        result = ScoringEngine.calculate_spread_outcome(pick, self.game)
        self.assertEqual(result, PickResult.LOSS)

    def test_spread_underdog_wins_outright(self):
        # Team 2 loses by 4. Picked Team 2? Wait.
        # This test case: Underdog wins outright means they actually have higher score.
        # In this game (24-20), Team 1 won.
        # Let's test Underdog Covers (Loses game, but covers spread)
        # Team 2 (+7) vs Team 1 (-7). Score 20 vs 24.
        # Team 2 Score + 7 = 27 > 24. Win.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=7.0, bet_amount=100, pick_type="Spread",
            picked_team_id=102 # Team 2
        )
        result = ScoringEngine.calculate_spread_outcome(pick, self.game)
        self.assertEqual(result, PickResult.WIN)

    def test_spread_push(self):
        # Team 1 wins by 4. Spread is -4. Push.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=-4.0, bet_amount=100, pick_type="Spread",
            picked_team_id=101
        )
        result = ScoringEngine.calculate_spread_outcome(pick, self.game)
        self.assertEqual(result, PickResult.PUSH)
        
    def test_ou_over_hits(self):
        # Total is 24+20 = 44. Line 40. Over Wins.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=40.0, bet_amount=100, pick_type="Over/Under",
            picked_value="Over"
        )
        result = ScoringEngine.calculate_ou_outcome(pick, self.game)
        self.assertEqual(result, PickResult.WIN)

    def test_ou_under_hits(self):
        # Total is 44. Line 50. Under Wins.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=50.0, bet_amount=100, pick_type="Over/Under",
            picked_value="Under"
        )
        result = ScoringEngine.calculate_ou_outcome(pick, self.game)
        self.assertEqual(result, PickResult.WIN)
        
    def test_ou_push(self):
         # Total is 44. Line 44. Push.
        pick = Pick(
            id=1, betting_series_id=1, person_id=1, bowl_game_id=1,
            line_at_pick=44.0, bet_amount=100, pick_type="Over/Under",
            picked_value="Over"
        )
        result = ScoringEngine.calculate_ou_outcome(pick, self.game)
        self.assertEqual(result, PickResult.PUSH)

if __name__ == '__main__':
    unittest.main()
