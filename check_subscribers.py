import sqlite3
import os

def check_subscribers():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subscribers.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get all subscribers
    c.execute('SELECT email, signup_date FROM subscribers ORDER BY signup_date DESC')
    subscribers = c.fetchall()
    
    print("\nSubscribers:")
    print("-" * 50)
    for email, date in subscribers:
        print(f"Email: {email}")
        print(f"Signup Date: {date}")
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    check_subscribers() 