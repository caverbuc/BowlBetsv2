import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.db.manager import DatabaseManager

def main():
    # Initialize Application
    app = QApplication(sys.argv)
    
    # Initialize Database
    db_manager = DatabaseManager()
    try:
        db_manager.initialize_schema()
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)
        
    # Create and Show Main Window
    window = MainWindow(db_manager)
    window.show()
    
    # Execute App
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
