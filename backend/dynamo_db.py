import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from dotenv import load_dotenv

# --- IMPORT VALIDATORS ---
from backend.validators import check_email, check_phone 

load_dotenv()

# --- CONFIGURATION ---
TABLE_NAME = "MH_Aviation_Leads" # Make sure this matches AWS Console exactly
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

try:
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
except Exception as e:
    print(f"❌ DynamoDB Init Error: {e}")

# --- FUNCTION 1: SAVE LEAD ---
def save_lead_dynamo(email, phone=None, name=None, school=None, city=None, chat_history=None):
    """Saves or updates user details and appends chat history."""
    
    # 1. VALIDATE EMAIL (First Priority)
    # If email is fake, we stop immediately.
    if not check_email(email):
        print(f"🚫 Save blocked: Invalid Email '{email}'")
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    key = {'email': email}

    # 2. Build Update Expression
    update_expression = "SET last_updated = :t, created_at = if_not_exists(created_at, :t)"
    expression_values = {':t': now}
    expression_names = {} 

    # 3. VALIDATE & ADD PHONE
    if phone:
        # Check validity first
        if not check_phone(phone):
            print(f"🚫 Save blocked: Invalid Phone '{phone}'")
            return False # Reject the lead
        
        # If valid, ADD it to the database update
        update_expression += ", phone = :p"
        expression_values[':p'] = phone

    # 4. ADD OTHER FIELDS
    if name:
        update_expression += ", #nm = :n" 
        expression_names['#nm'] = "name"
        expression_values[':n'] = name
    if school:
        update_expression += ", school = :s"
        expression_values[':s'] = school
    if city:
        update_expression += ", city = :c"
        expression_values[':c'] = city
    
    # 5. HANDLE CHAT HISTORY
    if chat_history:
        try:
            response = table.get_item(Key=key)
            existing_item = response.get('Item', {})
            existing_history = existing_item.get('chat_history', [])
            
            updated_history = existing_history + chat_history
            
            update_expression += ", chat_history = :ch"
            expression_values[':ch'] = updated_history
            
        except ClientError as e:
            print(f"Error fetching for chat append: {e}")

    # 6. EXECUTE UPDATE
    try:
        update_args = {
            'Key': key,
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': "UPDATED_NEW"
        }
        if expression_names:
            update_args['ExpressionAttributeNames'] = expression_names

        table.update_item(**update_args)
        print(f"✅ DynamoDB Update for {email}")
        return True

    except ClientError as e:
        print(f"❌ DynamoDB Write Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"⚠️ General DB Error: {e}")
        return False

# --- FUNCTION 2: GET ALL LEADS ---
def get_all_leads():
    """Fetches all items from the table for the Admin Dashboard."""
    try:
        response = table.scan()
        items = response.get('Items', [])
        # Sort by last_updated (Newest first)
        items.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        return items
    except Exception as e:
        print(f"Error fetching leads: {e}")
        return []