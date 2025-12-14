import requests
from typing import List, Dict, Optional

class TheOddsAPI:
    BASE_URL = "https://api.the-odds-api.com/v4"
    SPORT_KEY = "americanfootball_ncaaf"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_odds(self, regions: str = "us", markets: str = "spreads,totals") -> List[Dict]:
        """
        Fetches current odds for NCAAF.
        docs: https://the-odds-api.com/live-api/guides/v4/#get-odds
        """
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "american"
        }
        try:
            response = requests.get(
                f"{self.BASE_URL}/sports/{self.SPORT_KEY}/odds",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"TheOdds API Error: {e}")
            return []
