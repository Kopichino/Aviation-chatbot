import sqlite3
import os
from datetime import datetime

DB_NAME = "leads.db"

def init_db():
    """Creates the leads table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            phone TEXT,
            topic_of_interest TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized/verified.")

def save_lead(email, phone, topic="General Inquiry"):
    """Saves a new lead to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if lead already exists to avoid duplicates
    cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
    if cursor.fetchone():
        # Update phone if entry exists
        cursor.execute("UPDATE leads SET phone = ?, timestamp = ? WHERE email = ?", 
                       (phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email))
    else:
        # Insert new lead
        cursor.execute("INSERT INTO leads (email, phone, topic_of_interest, timestamp) VALUES (?, ?, ?, ?)",
                       (email, phone, topic, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    print(f"Lead saved: {email} | {phone}")

# Run initialization immediately when imported
init_db()