import argparse
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def create_admin(email: str, password: str):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User {email} already exists.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name="Admin",
            last_name="System",
            role="ADMIN",
            is_active=True,
            must_change_password=False
        )
        db.add(user)
        db.commit()
        print(f"Admin created successfully: {email}")
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create initial admin user")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    
    args = parser.parse_args()
    create_admin(args.email, args.password)
