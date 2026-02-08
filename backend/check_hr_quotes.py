from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM partner_quotes WHERE dest_country = 'HR'"))
    count = result.scalar()
    print(f"Quotes for HR: {count}")
