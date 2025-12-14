import requests
from typing import List, Dict, Optional
from datetime import datetime

class CollegeFootballDataAPI:
    BASE_URL = "https://api.collegefootballdata.com"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def get_postseason_games(self, year: int) -> List[Dict]:
        """
        Fetches postseason (bowl) games for a given season year.
        Note: API usually treats existing bowls as 'postseason' season type.
        """
        params = {
            "year": year,
            "seasonType": "postseason"
        }
        try:
            response = requests.get(
                f"{self.BASE_URL}/games", 
                headers=self.headers, 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"CFD API Error (get_games): {e}")
            return []

    def get_teams(self) -> List[Dict]:
        """
        Fetches all FBS teams to populate the database.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/teams/fbs", # Only fetch FBS teams for now
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"CFD API Error (get_teams): {e}")
            return []
