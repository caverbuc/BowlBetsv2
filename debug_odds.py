from PyQt6.QtCore import QSettings
from src.api.odds import TheOddsAPI
import json

def debug_odds():
    settings = QSettings("BowlBets", "BowlBetsV2")
    api_key = settings.value("api_keys/theodds", "")
    
    print(f"Stored API Key: '{api_key}'")
    
    if not api_key:
        print("ERROR: No API Key found in settings.")
        return

    api = TheOddsAPI(api_key)
    print("Fetching odds from API...")
    try:
        data = api.get_odds()
        print(f"Successfully fetched {len(data)} events.")
        if len(data) > 0:
            print("Sample Event:")
            print(json.dumps(data[0], indent=2))
        else:
            print("API returned 0 events. Is the season/sport correct?")
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    debug_odds()
