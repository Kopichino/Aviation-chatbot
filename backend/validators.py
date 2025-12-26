import phonenumbers
from email_validator import validate_email, EmailNotValidError

def check_email(email):
    """Returns True if email is valid, False otherwise."""
    try:
        # check_deliverability=True checks if the domain (e.g. gmail.com) actually exists
        validate_email(email, check_deliverability=True)
        return True
    except EmailNotValidError as e:
        print(f"❌ Invalid Email: {str(e)}")
        return False

def check_phone(phone):
    """Returns True if phone number is valid, False otherwise."""
    try:
        # 1. Parse the number (assuming generic international or default region)
        # If your users are mostly Indian, use default_region="IN"
        parsed_number = phonenumbers.parse(phone, "IN") 
        
        # 2. Check validity
        if phonenumbers.is_valid_number(parsed_number):
            return True
        else:
            print("❌ Valid format but invalid number (e.g. too short)")
            return False
            
    except phonenumbers.NumberParseException:
        print("❌ Could not parse phone number")
        return False