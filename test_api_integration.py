"""
Test script to verify API integration and data relationships.
This script tests:
1. Games endpoint retrieval
2. Betting lines endpoint and its relationship to games (via game_id)
3. Venues endpoint and its relationship to games (via venue_id)
4. Game media endpoint
5. All relationship mappings
"""

import sys
import json
from PyQt6.QtCore import QSettings
from src.api.cfd import CollegeFootballDataAPI

def test_api_integration():
    print("="*80)
    print("API Integration Test")
    print("="*80)

    # Get API key from settings
    settings = QSettings("BowlBets", "BowlBetsV2")
    cfd_key = settings.value("api_keys/cfd", "")

    if not cfd_key:
        print("ERROR: No CFD API key found in settings!")
        print("Please configure your API key in the application settings first.")
        return False

    api = CollegeFootballDataAPI(cfd_key)

    # Test 1: Fetch games
    print("\n" + "="*80)
    print("TEST 1: Fetching Postseason Games for 2025")
    print("="*80)
    games = api.get_postseason_games(2025)
    print(f"✓ Retrieved {len(games)} games")

    if games:
        sample_game = games[0]
        print(f"\nSample game structure (first game):")
        print(json.dumps(sample_game, indent=2))

        # Check for required fields
        required_fields = ['id', 'homeTeam', 'awayTeam', 'homeId', 'awayId']
        missing_fields = [f for f in required_fields if f not in sample_game]
        if missing_fields:
            print(f"⚠ WARNING: Missing fields in game: {missing_fields}")
        else:
            print(f"✓ All required game fields present")

    # Test 2: Fetch betting lines
    print("\n" + "="*80)
    print("TEST 2: Fetching Betting Lines for 2025 Postseason")
    print("="*80)
    lines = api.get_betting_lines(year=2025, season_type="postseason")
    print(f"✓ Retrieved {len(lines)} betting line records")

    if lines:
        sample_line = lines[0]
        print(f"\nSample betting line structure (first record):")
        print(json.dumps(sample_line, indent=2))

        # Check structure
        if 'id' in sample_line:
            print(f"✓ Betting line has 'id' field (for matching to game)")
        else:
            print(f"⚠ WARNING: Betting line missing 'id' field!")

        if 'lines' in sample_line:
            print(f"✓ Betting line has 'lines' array with {len(sample_line['lines'])} providers")
        else:
            print(f"⚠ WARNING: Betting line missing 'lines' array!")

    # Test 3: Test relationship between games and betting lines
    print("\n" + "="*80)
    print("TEST 3: Verifying Games <-> Betting Lines Relationship")
    print("="*80)

    # Create lookup
    lines_by_game_id = {line['id']: line for line in lines}

    matched_count = 0
    unmatched_games = []

    for game in games[:10]:  # Test first 10 games
        game_id = game.get('id')
        if game_id in lines_by_game_id:
            matched_count += 1
            line_data = lines_by_game_id[game_id]
            spread = line_data['lines'][0].get('spread') if line_data.get('lines') else None
            ou = line_data['lines'][0].get('overUnder') if line_data.get('lines') else None
            print(f"✓ Game {game_id} ({game.get('homeTeam')} vs {game.get('awayTeam')})")
            print(f"  Spread: {spread}, O/U: {ou}")
        else:
            unmatched_games.append(game_id)

    print(f"\nMatched {matched_count}/{min(10, len(games))} test games with betting lines")
    if unmatched_games:
        print(f"⚠ Unmatched game IDs: {unmatched_games}")

    # Test 4: Fetch venues
    print("\n" + "="*80)
    print("TEST 4: Fetching Venues")
    print("="*80)
    venues = api.get_venues()
    print(f"✓ Retrieved {len(venues)} venues")

    if venues:
        sample_venue = venues[0]
        print(f"\nSample venue structure:")
        print(json.dumps(sample_venue, indent=2))

    # Test 5: Test relationship between games and venues
    print("\n" + "="*80)
    print("TEST 5: Verifying Games <-> Venues Relationship")
    print("="*80)

    venues_by_id = {venue['id']: venue for venue in venues}

    venue_matched = 0
    venue_unmatched = []

    for game in games[:10]:  # Test first 10 games
        venue_id = game.get('venueId') or game.get('venue_id')
        if venue_id and venue_id in venues_by_id:
            venue_matched += 1
            venue_name = venues_by_id[venue_id].get('name')
            print(f"✓ Game {game.get('id')}: {game.get('homeTeam')} vs {game.get('awayTeam')}")
            print(f"  Venue: {venue_name}")
        else:
            venue_unmatched.append(game.get('id'))

    print(f"\nMatched {venue_matched}/{min(10, len(games))} test games with venue data")
    if venue_unmatched:
        print(f"⚠ Games without venue match: {venue_unmatched}")

    # Test 6: Fetch game media
    print("\n" + "="*80)
    print("TEST 6: Fetching Game Media")
    print("="*80)
    media = api.get_game_media(2025, "postseason")
    print(f"✓ Retrieved {len(media)} media records")

    if media:
        sample_media = media[0]
        print(f"\nSample media structure:")
        print(json.dumps(sample_media, indent=2))

    # Test 7: Test relationship between games and media
    print("\n" + "="*80)
    print("TEST 7: Verifying Games <-> Media Relationship")
    print("="*80)

    media_by_game_id = {m['id']: m for m in media}

    media_matched = 0
    media_unmatched = []

    for game in games[:10]:  # Test first 10 games
        game_id = game.get('id')
        if game_id in media_by_game_id:
            media_matched += 1
            media_data = media_by_game_id[game_id]
            outlet = media_data.get('outlet')
            print(f"✓ Game {game_id}: {game.get('homeTeam')} vs {game.get('awayTeam')}")
            print(f"  Media: {outlet}")
        else:
            media_unmatched.append(game_id)

    print(f"\nMatched {media_matched}/{min(10, len(games))} test games with media data")
    if media_unmatched:
        print(f"⚠ Games without media match: {media_unmatched}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Games retrieved: {len(games)}")
    print(f"✓ Betting lines retrieved: {len(lines)}")
    print(f"✓ Venues retrieved: {len(venues)}")
    print(f"✓ Media records retrieved: {len(media)}")
    print(f"\nRelationship mapping:")
    print(f"  Games -> Betting Lines: {matched_count}/{min(10, len(games))} matched (sample)")
    print(f"  Games -> Venues: {venue_matched}/{min(10, len(games))} matched (sample)")
    print(f"  Games -> Media: {media_matched}/{min(10, len(games))} matched (sample)")

    # Check for FBS filtering
    print("\n" + "="*80)
    print("TEST 8: FBS Classification Check")
    print("="*80)
    fbs_count = 0
    non_fbs_count = 0

    for game in games[:20]:
        home_class = game.get('homeClassification', '')
        away_class = game.get('awayClassification', '')
        if home_class == 'fbs' and away_class == 'fbs':
            fbs_count += 1
        else:
            non_fbs_count += 1
            print(f"  Non-FBS game: {game.get('homeTeam')} ({home_class}) vs {game.get('awayTeam')} ({away_class})")

    print(f"\nIn first 20 games:")
    print(f"  FBS games: {fbs_count}")
    print(f"  Non-FBS games: {non_fbs_count}")
    print(f"  (Sync engine will filter out non-FBS games)")

    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80)

    return True

if __name__ == "__main__":
    try:
        test_api_integration()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
