import os
from pymongo import MongoClient
from datetime import datetime

# 1. Connect to Local MongoDB
# '27017' is the default port where MongoDB runs
client = MongoClient("mongodb://localhost:27017/")

# 2. Create/Select Database
db = client["mh_aviation_db"]

# 3. Create/Select Collection (Like a Table)
leads_collection = db["leads"]

def save_lead_mongo(email, phone=None, name=None, school=None, city=None, chat_history=None):
    """
    Saves user details and/or appends chat history.
    This function uses 'upsert': If user exists, update them. If not, create them.
    """
    
    # Current timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare the data we want to update
    update_data = {
        "last_updated": now
    }
    
    # Only update fields if they are provided (not None)
    if phone: update_data["phone"] = phone
    if name: update_data["name"] = name
    if school: update_data["school"] = school
    if city: update_data["city"] = city
    
    # DATABASE OPERATION
    # $set: Updates the specific fields (name, phone, etc.)
    # $setOnInsert: Sets 'created_at' only when a new document is created
    operation = {
        "$set": update_data,
        "$setOnInsert": {"created_at": now, "email": email} 
    }

    # If chat history is provided, we want to PUSH it to the list
    if chat_history:
        # $push: Appends items to an array. 
        # $each: Allows appending multiple messages at once
        operation["$push"] = {"chat_history": {"$each": chat_history}}

    # Execute
    # filter={"email": email}: Find user by email
    # upsert=True: Create if not exists
    leads_collection.update_one(
        {"email": email},
        operation,
        upsert=True
    )
    
    print(f"✅ MongoDB Update for {email}")

def get_all_leads():
    """For the Admin Panel later"""
    return list(leads_collection.find({}, {"_id": 0})) # Return all, hide internal ID