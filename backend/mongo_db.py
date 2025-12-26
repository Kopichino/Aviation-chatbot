import os
from pymongo import MongoClient
from pymongo.errors import WriteError
from datetime import datetime

# 1. Connect to Local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["mh_aviation_db"]
leads_collection = db["leads"]

# --- FUNCTION 1: SAVE LEAD (Used by Chatbot) ---
def save_lead_mongo(email, phone=None, name=None, school=None, city=None, chat_history=None):
    """Saves or updates user details and appends chat history."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare update data
    update_data = {"last_updated": now}
    if phone: update_data["phone"] = phone
    if name: update_data["name"] = name
    if school: update_data["school"] = school
    if city: update_data["city"] = city
    
    # Define database operation
    operation = {
        "$set": update_data,
        "$setOnInsert": {"created_at": now, "email": email} 
    }

    # Append chat history if provided
    if chat_history:
        operation["$push"] = {"chat_history": {"$each": chat_history}}

    try:
        leads_collection.update_one(
            {"email": email},
            operation,
            upsert=True
        )
        print(f"✅ MongoDB Update for {email}")
        return True 
    
    except WriteError as e:
        print(f"❌ DATA REJECTED by MongoDB Validation: {e}")
        return False
        
    except Exception as e:
        print(f"⚠️ General DB Error: {e}")
        return False

# --- FUNCTION 2: GET ALL LEADS (Used by Admin Panel) ---
# <--- THIS WAS MISSING --->
def get_all_leads():
    """Fetches all documents from the leads collection for the Admin Dashboard."""
    # .find() gets everything. 
    # {"_id": 0} tells Mongo NOT to send the internal ID field which causes errors in JSON.
    try:
        leads = list(leads_collection.find({}, {"_id": 0}))
        return leads
    except Exception as e:
        print(f"Error fetching leads: {e}")
        return []