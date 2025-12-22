# GEMINI.md

## Project Overview

This project is a desktop application named "BowlBets v2.0" for tracking college football bowl game bets between two people. It is built using Python and the PyQt6 framework for the user interface. The application allows users to create betting series, make picks on bowl games (spread and over/under), and automatically calculates the results and profit/loss based on the final game scores.

The application retrieves game data and odds from the College Football Data API and The Odds API. The data is stored in a local SQLite database.

## Key Technologies

*   **Language:** Python 3
*   **UI Framework:** PyQt6
*   **Database:** SQLite
*   **APIs:**
    *   College Football Data API (for game and team information)
    *   The Odds API (for betting odds)
*   **Libraries:**
    *   `requests`: For making HTTP requests to the APIs.
    *   `python-dotenv`: for managing environment variables.
    *   `pytest`: For unit testing.
    *   `pytest-qt`: For testing PyQt applications.
    *   `black` & `flake8`: For code formatting and linting.

## Architecture

The application follows a typical desktop application architecture:

*   **`main.py`**: The entry point of the application. It initializes the database and the main window.
*   **`src/`**: Contains the core source code.
    *   **`src/ui/`**: Contains the PyQt6 user interface components. `main_window.py` is the main window, which contains several widgets for different functionalities.
    *   **`src/db/`**: Contains the database-related code. `models.py` defines the database schema using dataclasses, and `manager.py` manages the database connection and schema initialization. `repositories.py` contains the logic for querying the database.
    *   **`src/logic/`**: Contains the business logic of the application. `scoring.py` calculates the results of the bets, and `import_export.py` handles the import and export of betting series.
    *   **`src/api/`**: Contains the code for interacting with external APIs.
*   **`tests/`**: Contains the tests for the application. `test_scoring.py` is a good example of how the application is tested.
*   **`scripts/`**: Contains various scripts for debugging and verification.

## Building and Running

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up Environment Variables:**
    The application uses API keys for The Odds API and the College Football Data API. These keys are stored in the application's settings, which are managed by `QSettings`. You will need to set the API keys in the settings UI of the application.

3.  **Run the Application:**
    ```bash
    python main.py
    ```

## Development Conventions

*   **Code Style:** The project uses `black` for code formatting and `flake8` for linting.
*   **Testing:** The project uses `pytest` and `pytest-qt` for testing. The `tests/` directory contains the tests. The `scripts/` directory also contains verification scripts that can be run manually.
*   **Database:** The database schema is defined in `src/db/models.py`. The database is managed by the `DatabaseManager` class in `src/db/manager.py`. The application uses SQLite as its database.
*   **UI:** The user interface is built with PyQt6. The UI components are located in the `src/ui/` directory.
