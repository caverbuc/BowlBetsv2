# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BowlBets v2.0 is a PyQt6 desktop application for tracking college football bowl game bets between two people. Users create betting series, make spread and over/under picks on bowl games, and the application automatically calculates results and profit/loss based on final game scores.

## Essential Commands

### Running the Application
```bash
python main.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Code formatting
black src/

# Linting
flake8 src/
```

### Debugging Tools
```bash
# Manual verification scripts
python scripts/verify_scoring.py
python scripts/verify_import_export.py
python scripts/fix_originator.py
python debug_odds.py
```

## Core Architecture

The application follows a **layered architecture pattern**:

```
UI Layer (src/ui/)
    ↓
Business Logic Layer (src/logic/)
    ↓
Repository Layer (src/db/repositories.py)
    ↓
Database Layer (SQLite via src/db/manager.py)
```

### Application Entry Point

`main.py` initializes:
1. Logging to `bowlbets.log` (overwrites each run)
2. QApplication instance
3. DatabaseManager - creates/opens SQLite connection
4. Schema initialization (creates tables, runs migrations)
5. MainWindow with DashboardWidget
6. Qt event loop

### Database Schema

Seven tables with specific relationships:
- **Person** - Users/betters
- **Season** - Bowl seasons (e.g., 2025-2026)
- **Team** - College teams with API IDs and logo URLs
- **BowlGame** - Games with scores, status, and API metadata
- **BettingSeries** - Series between two people for a season (with default bet amounts per tier)
- **Odds** - Betting lines (spread, over/under) per game
- **Pick** - Individual bets with `line_at_pick`, `bet_amount`, `result`, `profit_loss`, `is_originator`

**Critical Unique Constraints:**
- `BettingSeries`: UNIQUE(season_id, person1_id, person2_id)
- `Pick`: UNIQUE(betting_series_id, person_id, bowl_game_id) - one pick per person per game per series
- `Team`: UNIQUE api_cfd_id, UNIQUE api_theodds_id
- `BowlGame`: UNIQUE api_cfd_id

### Repository Pattern

All database access goes through repositories in `src/db/repositories.py`:
- PersonRepository
- SeasonRepository
- TeamRepository
- BowlGameRepository
- BettingSeriesRepository
- OddsRepository
- PickRepository

Each repository provides: `create()`, `get_by_id()`, `get_all()`, `update()`, `delete()`, plus specialized query methods.

**Key specialized methods:**
- `BowlGameRepository.upsert_from_api()` - Creates or updates games using API data
- `PickRepository.get_picks_for_series()` - Returns all picks for a betting series
- `BettingSeriesRepository.update_financials()` - Recalculates series totals
- `TeamRepository.upsert_from_api()` - Inserts/updates teams by API ID

### Business Logic Layer

**ScoringEngine** (`src/logic/scoring.py`):
- `process_series_picks(series_id)` - Calculates outcomes for all picks in a series
- Only scores games with status "Final" or "Completed"
- Returns PickResult enum: WIN, LOSS, PUSH, PENDING, ERROR
- `calculate_spread_outcome()` - Spread bet logic (accounts for picked team)
- `calculate_ou_outcome()` - Over/Under logic (picked_value is "over" or "under")
- Calculates `profit_loss` using bet_amount and line_at_pick (American odds)

**SyncManager/SyncWorker** (`src/logic/sync_engine.py`):
- Runs in separate QThread to avoid blocking UI
- Fetches games, odds, venues, media from College Football Data API
- Filters for FBS teams only
- Updates/inserts bowl games and odds via `upsert_from_api()`
- Retrieves team logos via API
- Emits signals: `progress`, `finished`, `error`, `new_odds_available`

**SeriesTransferManager** (`src/logic/import_export.py`):
- **Export**: Serializes series to JSON using API IDs (not local DB IDs) for portability
- **Import**: Deserializes JSON and links to local games via API IDs
- Preserves: pick data, line_at_pick, bet_amount, is_originator flag
- Enables series sharing between different databases/machines

### UI Components

**MainWindow** (`src/ui/main_window.py`):
- Menu bar: File (Settings, Exit), Series (New, Import, Export), Help (About)
- Central widget: DashboardWidget
- Status bar for messages

**DashboardWidget** (`src/ui/dashboard_widget.py`) - **1,241 lines (largest file)**:
- Main application interface
- Displays game cards for all games in selected series
- Per-person picker widgets for each game
- Quick-pick buttons (team selection, O/U)
- Bet amount input
- Series selection dropdown
- Leaderboard integration
- Handles new/import/export series workflows

**PickDialog** (`src/ui/pick_dialog.py`):
- Modal dialog for detailed pick entry
- Pick type selection (Spread/Over-Under)
- Team/value selection
- Bet amount spinbox
- Auto-populates odds from API data
- Manual spread override capability

**SeriesWizard** (`src/ui/series_wizard.py`):
- Multi-page QWizard for series creation/editing
- Page 1: Season selection/creation
- Page 2: Participant names (person1/person2)
- Page 3: Default bet amounts (regular, CFP semi-final, championship)

**ImageCache** (`src/ui/image_cache.py`):
- Caches team logos to prevent redundant network fetches
- Uses `QPixmap` for efficient image handling

### API Integration

**CollegeFootballDataAPI** (`src/api/cfd.py`):
- `get_postseason_games(year)` - Fetches bowl games for a season
- `get_teams()` - Gets all FBS teams
- `get_betting_lines(game_id)` - Gets spread and over/under odds
- `get_venues()` - Stadium information
- `get_game_media(year)` - Broadcast details
- Requires API key stored in QSettings
- Handles authentication, timeouts, error responses

**Note**: `src/api/odds.py` was removed - The Odds API integration is no longer active.

## Data Models (Dataclasses)

All models in `src/db/models.py` use `@dataclass` with `Optional[int]` for IDs (None before insertion).

Key fields to understand:
- **Pick.is_originator**: Boolean indicating which person made the pick first (used for UI coordination)
- **Pick.line_at_pick**: Stores the odds line when pick was made (may differ from current odds)
- **BowlGame.cfp_tier**: "Regular", "Semi-Final", or "Championship" (affects default bet amounts)
- **BowlGame.game_status**: "Scheduled", "In Progress", "Final", "Completed" (only "Final"/"Completed" are scored)

## Threading Model

**UI Thread**: All PyQt6 widgets, signals, slots
**Worker Thread**: SyncWorker runs API calls in separate thread via QThread
- **Critical**: Never manipulate UI from worker thread
- Use signals/slots to communicate results back to UI thread

## Settings Storage

API keys and preferences stored via `QSettings`:
- Accessed in `src/ui/settings_widget.py`
- Keys: "api/cfd_key", "api/theodds_key"
- Platform-specific storage (macOS: ~/Library/Preferences, Windows: Registry)

## Testing Approach

Tests use `pytest` and `pytest-qt`:
- Database tests create temporary in-memory databases
- UI tests use `qtbot` fixture for widget interaction
- Scoring tests verify WIN/LOSS/PUSH logic with known game outcomes

**Note**: Several test files were deleted in recent commits. Core testing framework remains in place.

## Common Development Patterns

### Adding a New Database Column

1. Update dataclass in `src/db/models.py`
2. Add ALTER TABLE migration in `DatabaseManager.initialize_schema()` (src/db/manager.py)
3. Update repository methods if new queries needed
4. Update UI widgets if column should be displayed/edited

### Adding a New Pick Type

1. Update Pick dataclass with new pick_type value
2. Add calculation method to ScoringEngine
3. Update PickDialog UI to support new pick type
4. Update DashboardWidget quick-pick buttons if needed

### Syncing New Data from API

1. Add new API method to CollegeFootballDataAPI
2. Add repository upsert/update methods if needed
3. Call from SyncWorker.run() in sync_engine.py
4. Update progress signals for UI feedback

## File Organization

- **UI files** average 100-200 lines except DashboardWidget (1,241 lines)
- **Repository file** is ~400 lines (all 7 repositories in one file)
- **Database models** are simple dataclasses (~10-15 lines each)
- **Business logic** files are focused on single responsibility (150-220 lines each)

## Logging

Application logs to `bowlbets.log` (overwrites each run):
- Level: INFO
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Use `logging.info()`, `logging.error()`, etc. throughout the codebase

## Key Design Decisions

1. **Dataclasses over ORM**: Simple data containers, explicit SQL in repositories
2. **Repository pattern**: Separation of data access from business logic
3. **API ID preservation**: Games/teams linked by external API IDs, not just local DB IDs
4. **Import/export via API IDs**: Enables series portability across databases
5. **Single repository file**: All repositories in one file for cohesion
6. **QSettings for configuration**: Platform-native storage for API keys
7. **Threaded API calls**: SyncWorker prevents UI blocking during network operations
8. **Pick immutability**: line_at_pick preserved even when odds change
9. **is_originator flag**: Tracks who made pick first for UI coordination between users

## User Documentation

**User Guide**: `USER_GUIDE.md` contains comprehensive documentation for end users
**About Dialog**: Accessible via Help → User Guide & About menu
- Displays app information and version
- Includes full user guide with searchable content
- Basic markdown rendering for formatting

## Recent Changes (V1share branch)

- Series management moved from dedicated widget to menu-driven workflow
- Team logos integrated and cached
- Removed The Odds API integration (src/api/odds.py deleted)
- Removed series_management_widget.py (refactored into menus)
- Deleted test files (test_scoring.py, test_repos_script.py, verify_db.py)
- Playoff game bet amount handling implemented
- Odds display and acceptance improved in UI
- Added comprehensive user guide and About dialog
- Added venue and media information display on game cards
- Added over/under manual editing capability