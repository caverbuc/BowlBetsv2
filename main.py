import sys
import logging
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.db.manager import DatabaseManager

def main():
    # Set up logging
    logging.basicConfig(
        filename='bowlbets.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'  # Overwrite log file on each run
    )
    logging.info("Application starting...")

    # Initialize Application
    app = QApplication(sys.argv)
    
    # Initialize Database
    db_manager = DatabaseManager()
    try:
        db_manager.initialize_schema()
        logging.info("Database schema initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        print(f"Error initializing database: {e}")
        sys.exit(1)
        
    # Create and Show Main Window
    window = MainWindow(db_manager)
    window.show()
    
    # Execute App
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
