# import os
# import boto3
# from botocore.exceptions import ClientError
# from datetime import datetime
# # from dotenv import load_dotenv

# # --- IMPORT VALIDATORS ---
# from backend.validators import check_email, check_phone 

# # load_dotenv()

# # --- CONFIGURATION ---
# TABLE_NAME = "MH_Aviation_Leads" # Make sure this matches AWS Console exactly
# REGION = os.getenv("AWS_DEFAULT_REGION", "sp-south-1")

# try:
#     dynamodb = boto3.resource("dynamodb", region_name=REGION)
#     table = dynamodb.Table(TABLE_NAME)
# except Exception as e:
#     print(f"❌ DynamoDB Init Error: {e}")

# # --- FUNCTION 1: SAVE LEAD ---
# def save_lead_dynamo(email, phone=None, name=None, school=None, city=None, chat_history=None):
#     """Saves or updates user details and appends chat history."""
    
#     # 1. VALIDATE EMAIL (First Priority)
#     # If email is fake, we stop immediately.
#     if not check_email(email):
#         print(f"🚫 Save blocked: Invalid Email '{email}'")
#         return False

#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     key = {'email': email}

#     # 2. Build Update Expression
#     update_expression = "SET last_updated = :t, created_at = if_not_exists(created_at, :t)"
#     expression_values = {':t': now}
#     expression_names = {} 

#     # 3. VALIDATE & ADD PHONE
#     if phone:
#         # Check validity first
#         if not check_phone(phone):
#             print(f"🚫 Save blocked: Invalid Phone '{phone}'")
#             return False # Reject the lead
        
#         # If valid, ADD it to the database update
#         update_expression += ", phone = :p"
#         expression_values[':p'] = phone

#     # 4. ADD OTHER FIELDS
#     if name:
#         update_expression += ", #nm = :n" 
#         expression_names['#nm'] = "name"
#         expression_values[':n'] = name
#     if school:
#         update_expression += ", school = :s"
#         expression_values[':s'] = school
#     if city:
#         update_expression += ", city = :c"
#         expression_values[':c'] = city
    
#     # 5. HANDLE CHAT HISTORY
#     if chat_history:
#         try:
#             response = table.get_item(Key=key)
#             existing_item = response.get('Item', {})
#             existing_history = existing_item.get('chat_history', [])
            
#             updated_history = existing_history + chat_history
            
#             update_expression += ", chat_history = :ch"
#             expression_values[':ch'] = updated_history
            
#         except ClientError as e:
#             print(f"Error fetching for chat append: {e}")

#     # 6. EXECUTE UPDATE
#     try:
#         update_args = {
#             'Key': key,
#             'UpdateExpression': update_expression,
#             'ExpressionAttributeValues': expression_values,
#             'ReturnValues': "UPDATED_NEW"
#         }
#         if expression_names:
#             update_args['ExpressionAttributeNames'] = expression_names

#         table.update_item(**update_args)
#         print(f"✅ DynamoDB Update for {email}")
#         return True

#     except ClientError as e:
#         print(f"❌ DynamoDB Write Error: {e.response['Error']['Message']}")
#         return False
#     except Exception as e:
#         print(f"⚠️ General DB Error: {e}")
#         return False

# # --- FUNCTION 2: GET ALL LEADS ---
# def get_all_leads():
#     """Fetches all items from the table for the Admin Dashboard."""
#     try:
#         response = table.scan()
#         items = response.get('Items', [])
#         # Sort by last_updated (Newest first)
#         items.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
#         return items
#     except Exception as e:
#         print(f"Error fetching leads: {e}")
#         return []


# ----------------------------------------------------------------------------------------------------
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

# --- CONFIGURATION ---
TABLE_NAME = "MH_Aviation_Leads" 
REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")

try:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
except Exception as e:
    print(f"❌ DynamoDB Init Error: {e}")

# --- HELPER 1: GET USER STATS ---
def get_user_stats(email):
    """Fetches counts and handles Decimal -> Int conversion safely."""
    if not email: return {"is_registered": False, "guest_count": 0, "post_reg_count": 0}
    try:
        response = table.get_item(Key={'email': email})
        item = response.get('Item', {})
        return {
            "is_registered": item.get("is_registered", False),
            "guest_count": int(item.get("guest_count", 0)), 
            "post_reg_count": int(item.get("post_reg_count", 0)) 
        }
    except Exception as e:
        print(f"⚠️ Stats Error: {e}")
        return {"is_registered": False, "guest_count": 0, "post_reg_count": 0}

# --- HELPER 2: INCREMENT COUNTER ---
def increment_counter(email, is_registered):
    """Increments the appropriate counter."""
    if not email: return
    field_name = "post_reg_count" if is_registered else "guest_count"
    try:
        table.update_item(
            Key={'email': email},
            UpdateExpression=f"ADD {field_name} :inc",
            ExpressionAttributeValues={':inc': 1}
        )
    except Exception as e:
        print(f"⚠️ Counter Error: {e}")

# --- HELPER 3: SAVE LEAD (ROBUST VERSION) ---
def save_lead_dynamo(email, phone=None, name=None, school=None, city=None, mark_registered=False):
    """Saves user details with robust error handling."""
    if not email: return False
    
    print(f"💾 Saving Details for {email}: Name={name}, Phone={phone}") 

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    key = {'email': email}

    # Base Update: Timestamp
    update_expr = "SET last_updated = :t, created_at = if_not_exists(created_at, :t)"
    expr_values = {':t': now}
    expr_names = {}

    # Conditionally add fields
    if phone:
        update_expr += ", phone = :p"
        expr_values[':p'] = phone
    if name:
        update_expr += ", #nm = :n"  # Use #nm alias for reserved word 'name'
        expr_names['#nm'] = "name"
        expr_values[':n'] = name
    if school:
        update_expr += ", school = :s"
        expr_values[':s'] = school
    if city:
        update_expr += ", city = :c"
        expr_values[':c'] = city
    
    if mark_registered:
        update_expr += ", is_registered = :r, post_reg_count = if_not_exists(post_reg_count, :zero)"
        expr_values[':r'] = True
        expr_values[':zero'] = 0

    try:
        args = {
            'Key': key,
            'UpdateExpression': update_expr,
            'ExpressionAttributeValues': expr_values,
            'ReturnValues': "UPDATED_NEW"
        }
        if expr_names:
            args['ExpressionAttributeNames'] = expr_names
            
        table.update_item(**args)
        print("✅ DynamoDB Update Success")
        return True
    except Exception as e:
        print(f"❌ DB Save Error: {e}")
        return False

# --- HELPER 4: GET ALL LEADS (REQUIRED FOR ADMIN) ---
def get_all_leads():
    """Scans table to return all leads for the dashboard."""
    try:
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"❌ Admin Scan Error: {e}")
        return []

# --- HELPER 5: APPEND CHAT HISTORY ---
def append_chat_history(email, role, message):
    """Appends a message to the chat history list."""
    if not email or not message: return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {
        "role": role, 
        "content": str(message), 
        "timestamp": timestamp
    }
    
    try:
        table.update_item(
            Key={'email': email},
            UpdateExpression="SET chat_history = list_append(if_not_exists(chat_history, :empty_list), :new_msg)",
            ExpressionAttributeValues={
                ':new_msg': [new_entry],
                ':empty_list': []
            }
        )
    except Exception as e:
        pass