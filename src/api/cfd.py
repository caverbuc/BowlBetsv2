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

    def get_betting_lines(self, game_id: Optional[int] = None, year: Optional[int] = None, 
                          season_type: str = "postseason") -> List[Dict]:
        """
        Fetches betting lines for games.
        docs: https://apinext.collegefootballdata.com/api/docs/#operation/get-lines
        """
        params = {
            "seasonType": season_type
        }
        if game_id:
            params["gameId"] = game_id
        if year:
            params["year"] = year
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/lines",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"CFD API Error (get_betting_lines): {e}")
            return []

    def get_venues(self) -> List[Dict]:
        """
        Fetches a list of all venues.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/venues",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"CFD API Error (get_venues): {e}")
            return []

    def get_game_media(self, year: int, season_type: str = "postseason") -> List[Dict]:
        """
        Fetches media information for games.
        """
        params = {
            "year": year,
            "seasonType": season_type
        }
        try:
            response = requests.get(
                f"{self.BASE_URL}/games/media",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"CFD API Error (get_game_media): {e}")
            return []

