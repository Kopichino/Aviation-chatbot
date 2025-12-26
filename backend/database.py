# import sqlite3
# import os
# from datetime import datetime

# DB_NAME = "leads.db"

# def init_db():
#     """Creates the leads table if it doesn't exist."""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS leads (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             email TEXT,
#             phone TEXT,
#             topic_of_interest TEXT,
#             timestamp TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()
#     print("Database initialized/verified.")

# def save_lead(email, phone, topic="General Inquiry"):
#     """Saves a new lead to the database."""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
    
#     # Check if lead already exists to avoid duplicates
#     cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
#     if cursor.fetchone():
#         # Update phone if entry exists
#         cursor.execute("UPDATE leads SET phone = ?, timestamp = ? WHERE email = ?", 
#                        (phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email))
#     else:
#         # Insert new lead
#         cursor.execute("INSERT INTO leads (email, phone, topic_of_interest, timestamp) VALUES (?, ?, ?, ?)",
#                        (email, phone, topic, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
#     conn.commit()
#     conn.close()
#     print(f"Lead saved: {email} | {phone}")

# # Run initialization immediately when imported
# init_db()

#################################################################

# import sqlite3
# import os
# from datetime import datetime

# DB_NAME = "leads.db"

# def init_db():
#     """Creates the leads table with new columns."""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS leads (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             email TEXT,
#             phone TEXT,
#             school_city TEXT,  -- NEW COLUMN
#             topic_of_interest TEXT,
#             timestamp TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()
#     print("Database initialized.")

# def save_lead(email, phone, school_city=None, topic="General Inquiry"):
#     """Saves or updates a lead with all details."""
#     conn = sqlite3.connect(DB_NAME)
#     cursor = conn.cursor()
    
#     # Check if lead exists
#     cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
#     if cursor.fetchone():
#         # Update existing record
#         cursor.execute("""
#             UPDATE leads 
#             SET phone = ?, school_city = ?, timestamp = ? 
#             WHERE email = ?
#         """, (phone, school_city, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email))
#     else:
#         # Insert new record
#         cursor.execute("""
#             INSERT INTO leads (email, phone, school_city, topic_of_interest, timestamp) 
#             VALUES (?, ?, ?, ?, ?)
#         """, (email, phone, school_city, topic, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
#     conn.commit()
#     conn.close()
#     print(f"Lead saved: {email} | {phone} | {school_city}")

# # Run initialization
# init_db()

import sqlite3
import os
from datetime import datetime

DB_NAME = ".leads.db"

def init_db():
    """Creates the leads table with SEPARATE school and city columns."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            phone TEXT,
            school TEXT,      -- New Column 1
            city TEXT,        -- New Column 2
            topic_of_interest TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized with School and City columns.")

def save_lead(email, phone, school=None, city=None, topic="General Inquiry"):
    """Saves or updates a lead with all details."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if lead exists based on EMAIL
    cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
    if cursor.fetchone():
        # Update existing record
        cursor.execute("""
            UPDATE leads 
            SET phone = ?, school = ?, city = ?, timestamp = ? 
            WHERE email = ?
        """, (phone, school, city, timestamp, email))
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO leads (email, phone, school, city, topic_of_interest, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email, phone, school, city, topic, timestamp))
    
    conn.commit()
    conn.close()
    print(f"✅ DB Update: {email} | Ph: {phone} | School: {school} | City: {city}")

# Run initialization
init_db()