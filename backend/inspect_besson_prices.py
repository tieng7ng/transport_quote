
import sys
import os
import json
from decimal import Decimal

# Ensure backend root is in python path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.partner_quote import PartnerQuote

def inspect_besson():
    settings = get_settings()
    engine = create_engine(str(settings.database_url))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Fetch BESSON quotes for Dept 13 with weight_max=500
        # We look for costs around 14.46 and 21.35
        quotes = session.query(PartnerQuote).filter(
            PartnerQuote.dest_postal_code == '13',
            PartnerQuote.weight_max == 500,
            PartnerQuote.origin_postal_code == '06'
        ).all()
        
        print(f"Found {len(quotes)} quotes for BESSON (Dept 13, Max 500kg, Origin 06)")
        
        for q in quotes:
            print(f"\nID: {q.id}")
            print(f"Partner: {q.partner.name if q.partner else 'Unknown'} ({q.partner_code if hasattr(q, 'partner_code') else 'N/A'})")
            print(f"City: {q.dest_city}")
            print(f"Cost: {q.cost}")
            print(f"Delivery Time: {q.delivery_time}")
            print(f"Metadata: {q.meta_data}")
            print(f"Created At: {q.created_at}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_besson()
