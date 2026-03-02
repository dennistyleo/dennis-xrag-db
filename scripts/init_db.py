#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_config import XRAGDatabase

def init_database():
    print("🚀 Initializing XRAG database structure...")
    db = XRAGDatabase('data/xrag_complete.db')
    print(f"✅ Database initialized at: {db.db_path}")
    print("\n📊 Tables created:")
    print("   - known_axioms")
    print("   - xr_variables")
    print("   - match_history")
    print("   - unknown_candidates")

if __name__ == "__main__":
    init_database()
