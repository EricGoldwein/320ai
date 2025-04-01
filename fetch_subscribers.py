import sqlite3
import os
from datetime import datetime

def create_local_database():
    """Create a new local database with the same structure"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subscribers.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create the subscribers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers
        (email TEXT PRIMARY KEY,
         signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Add some test data
    test_subscribers = [
        ('test@example.com', datetime.now().isoformat()),
        ('test2@example.com', datetime.now().isoformat()),
    ]
    
    for email, date in test_subscribers:
        try:
            c.execute('INSERT OR REPLACE INTO subscribers (email, signup_date) VALUES (?, ?)',
                     (email, date))
        except sqlite3.IntegrityError:
            print(f"Subscriber {email} already exists")
    
    conn.commit()
    conn.close()
    print("Successfully created local database with test data")

if __name__ == "__main__":
    create_local_database() 