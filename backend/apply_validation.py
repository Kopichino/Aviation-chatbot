from pymongo import MongoClient

# 1. Connect
client = MongoClient("mongodb://localhost:27017/")
db = client["mh_aviation_db"]

# 2. Define the Validation Rules
validation_schema = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["email"], # Email is the primary key, so it's strictly required
        "properties": {
            "email": {
                "bsonType": "string",
                "pattern": "^.+@.+\\..+$",  # Regex for email (contains @ and .)
                "description": "must be a valid email address and is required"
            },
            "phone": {
                "bsonType": "string",
                "pattern": "^\\d{10,15}$", # Regex: 10 to 15 digits
                "description": "must be a string of 10-15 digits"
            },
            "name": {
                "bsonType": "string",
                "description": "must be a string"
            },
            "school": {
                "bsonType": "string",
                "description": "must be a string"
            },
            "city": {
                "bsonType": "string",
                "description": "must be a string"
            }
        }
    }
}

# 3. Apply the Rules (Try 'create' first, if fails, use 'collMod')
try:
    # Try to create collection with validation (if it doesn't exist)
    db.create_collection("leads", validator=validation_schema)
    print("✅ Collection 'leads' created with validation rules!")
except Exception as e:
    # If collection already exists, modify it to add validation
    if "already exists" in str(e):
        try:
            db.command("collMod", "leads", validator=validation_schema)
            print("✅ Validation rules applied to existing 'leads' collection!")
        except Exception as mod_error:
            print(f"❌ Failed to modify collection: {mod_error}")
    else:
        print(f"❌ Error: {e}")

# 4. (Optional) Check existing bad data
# This part doesn't fix old data, but future inserts will now be checked.