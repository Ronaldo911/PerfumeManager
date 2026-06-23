import uuid
import pandas as pd

def clean_numeric(val):
    """Clean and convert string/number to float safely"""
    try:
        if pd.isna(val) or val == "" or val is None:
            return 0.0
        return float(str(val).replace(',', '.').replace(' ', '').strip())
    except:
        return 0.0

def new_id():
    """Generate a unique ID"""
    return str(uuid.uuid4())[:8].upper()
