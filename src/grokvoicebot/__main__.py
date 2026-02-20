from .db import init_db
from .services import seed_knowledge


if __name__ == "__main__":
    init_db()
    seed_knowledge()
    print("Database initialized and seeded.")
