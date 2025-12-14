import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.manager import DatabaseManager
from src.db.repositories import PersonRepository, SeasonRepository

def test_repos():
    print("Testing Repositories...")
    db = DatabaseManager("test_repo.db")
    db.initialize_schema()
    
    try:
        person_repo = PersonRepository(db)
        season_repo = SeasonRepository(db)
        
        # Test Person Create
        print("Creating Person 'Cutler'...")
        p1 = person_repo.create("Cutler")
        print(f"Created: {p1}")
        assert p1.name == "Cutler"
        
        # Test Person Retrieval
        p2 = person_repo.get_by_id(p1.id)
        assert p2.name == "Cutler"
        print("Person retrieval verified.")
        
        # Test Season Create
        print("Creating Season 2024...")
        s1 = season_repo.create(2024, "2024-2025 Bowl Season")
        print(f"Created: {s1}")
        assert s1.start_year == 2024
        
        print("Repository tests passed!")
        
    except Exception as e:
        print(f"Repository test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        if os.path.exists("test_repo.db"):
            os.remove("test_repo.db")

if __name__ == "__main__":
    test_repos()
