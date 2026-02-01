
import sys
import os
import json
from datetime import date, datetime

# Ensure backend root is in python path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.services.matching_service import MatchingService
from app.schemas.matching import QuoteSearchRequest
from app.models.partner_quote import TransportMode

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def check_match():
    settings = get_settings()
    engine = create_engine(str(settings.database_url))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        request = QuoteSearchRequest(
            origin_country="FR",
            origin_postal_code="06",
            dest_country="FR",
            dest_postal_code="13",
            weight=400.0,
            transport_mode=TransportMode.ROAD,
            shipping_date=date(2026, 1, 29)
        )
        
        results = MatchingService.search_quotes(session, request)
        
        # Serialize to JSON to mimic API response
        output = []
        for q in results:
            # Basic dict representation
            q_dict = {
                "id": q.id,
                "partner_id": q.partner_id,
                "partner_name": q.partner.name if q.partner else "Unknown",
                "cost": float(q.cost),
                "weight_min": q.weight_min,
                "weight_max": q.weight_max,
                "origin_postal_code": q.origin_postal_code,
                "origin_city": q.origin_city,
                "dest_postal_code": q.dest_postal_code,
                "dest_city": q.dest_city,
                "pricing_type": q.pricing_type
            }
            output.append(q_dict)
            
        print(json.dumps(output, default=json_serial, indent=4))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_match()
