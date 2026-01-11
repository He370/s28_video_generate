import sqlite3
import os
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'music.db'))

def reset_usage(force=False):
    if not os.path.exists(DB_PATH):
        logging.error(f"Database not found at {DB_PATH}")
        return

    # User confirmation
    if not force:
        confirmation = input(f"WARNING: This will reset 'usage_count' to 0 for ALL tracks in {DB_PATH}.\nAre you sure you want to proceed? (yes/no): ")
        if confirmation.lower() != 'yes':
            logging.info("Operation cancelled.")
            return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracks';")
        if not cursor.fetchone():
            logging.error("Table 'tracks' does not exist in the database.")
            conn.close()
            return

        # Execute Update
        cursor.execute("UPDATE tracks SET usage_count = 0")
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully reset usage_count for {rows_affected} tracks.")
        
    except Exception as e:
        logging.error(f"Error resetting usage: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset music usage counts in the database.")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt.")
    args = parser.parse_args()
    
    reset_usage(force=args.force)
