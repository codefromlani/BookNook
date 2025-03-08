import re
from email_validator import validate_email as validate_email_format, EmailNotValidError

def validate_email(email):
    try:
        validate_email_format(email)
        return True
    except EmailNotValidError:
        return False
    
def validate_password(password):
    """
    Password must be at least 8 characters long and contain:
    - At least one letter
    - At least one number
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Za-z]', password):
        return False
    
    if not re.search(r'[0-9]', password):
        return False
    
    return True