import sys
import os
import secrets
import logging

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.models.user import UserRole
from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService
from app.schemas.customer_quote import CustomerQuoteCreate, CustomerQuoteItemCreate

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_test_user(db: Session, role: UserRole, prefix: str) -> dict:
    login = f"test_{prefix}_{secrets.token_hex(4)}"
    password = "TestPassword123!"
    email = f"{login}@toto.fr"
    
    user_in = UserCreate(
        login=login,
        email=email,
        password=password,
        first_name=f"Test {prefix}",
        last_name="User",
        role=role,
        is_active=True
    )
    
    try:
        user = AuthService.create_user(db, user_in)
        user.is_active = True
        user.must_change_password = False
        db.commit()
        db.refresh(user)
        return {"login": login, "password": password, "id": str(user.id), "token": None}
    except Exception as e:
        print(f"Error creating user {login}: {e}")
        return None

def login_user(client: TestClient, user_data: dict) -> str:
    response = client.post("/api/v1/auth/login", data={
        "username": user_data["login"],
        "password": user_data["password"]
    })
    if response.status_code != 200:
        print(f"Login failed for {user_data['login']}: {response.text}")
        return None
    return response.json()["access_token"]

def run_verification():
    print(f"{BOLD}Starting Role Alignment Verification...{RESET}\n")
    
    client = TestClient(app)
    db = SessionLocal()
    
    # 1. Setup Users
    print("Creating test users...")
    roles = {
        "SUPER_ADMIN": UserRole.SUPER_ADMIN,
        "ADMIN": UserRole.ADMIN,
        "COMMERCIAL": UserRole.COMMERCIAL,
        "COMMERCIAL_2": UserRole.COMMERCIAL,
        "VIEWER": UserRole.VIEWER
    }
    
    users = {}
    for name, role in roles.items():
        users[name] = create_test_user(db, role, name.lower())
        if not users[name]:
            print(f"{RED}Failed to create {name} user. Aborting.{RESET}")
            return
        
        token = login_user(client, users[name])
        if not token:
            print(f"{RED}Failed to login {name}. Aborting.{RESET}")
            return
        users[name]["token"] = token
        print(f"  - {name}: {users[name]['login']} (Authenticated)")
        
    print("\n--------------------------------------------------\n")
    
    success_count = 0
    fail_count = 0
    
    def assert_status(response, expected_status, test_name, allowed_statuses=None):
        nonlocal success_count, fail_count
        statuses = allowed_statuses if allowed_statuses else [expected_status]
        
        if response.status_code in statuses:
            print(f"{GREEN}[PASS] {test_name} (Got: {response.status_code}){RESET}")
            success_count += 1
            return True
        else:
            print(f"{RED}[FAIL] {test_name}{RESET}")
            print(f"  Expected: {statuses}, Got: {response.status_code}")
            # print(f"  Response: {response.text}")
            fail_count += 1
            return False

    # 2. Verify DELETE /partners/{id} Restriction
    print(f"{BOLD}Testing DELETE /partners/xxx (Restriction){RESET}")
    
    # ADMIN should fail (only SUPER_ADMIN allowed)
    resp = client.delete(
        "/api/v1/partners/some-id",
        headers={"Authorization": f"Bearer {users['ADMIN']['token']}"}
    )
    assert_status(resp, 403, "ADMIN cannot delete partners")
    
    # SUPER_ADMIN should pass (404 because ID doesn't exist, but valid authorized request)
    resp = client.delete(
        "/api/v1/partners/some-id",
        headers={"Authorization": f"Bearer {users['SUPER_ADMIN']['token']}"}
    )
    assert_status(resp, 404, "SUPER_ADMIN can delete partners", allowed_statuses=[204, 404])

    print("\n--------------------------------------------------\n")

    # 3. Verify POST /imports Restriction
    print(f"{BOLD}Testing POST /imports (Restriction){RESET}")
    
    # ADMIN should fail
    # We need a dummy file for the request to be valid format-wise
    files = {'file': ('test.csv', b'test', 'text/csv')}
    data = {'partner_id': 'some-id'}
    
    resp = client.post(
        "/api/v1/imports/",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {users['ADMIN']['token']}"}
    )
    assert_status(resp, 403, "ADMIN cannot upload imports")
    
    # SUPER_ADMIN should pass (404 partner not found, or 400 invalid file, but authorized)
    resp = client.post(
        "/api/v1/imports/",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {users['SUPER_ADMIN']['token']}"}
    )
    # 404 because partner_id doesn't exist, which means auth passed
    assert_status(resp, 404, "SUPER_ADMIN can upload imports", allowed_statuses=[404, 400, 201])

    print("\n--------------------------------------------------\n")

    # 4. Verify Customer Quote Item Deletion
    print(f"{BOLD}Testing DELETE /customer-quotes/items (Commercial){RESET}")
    
    # Create Quote for COMMERCIAL
    quote_data = {
        "customer_name": "Test Client",
        "customer_email": "client@test.com",
        "customer_company": "Test Corp",
        "valid_until": "2026-12-31T23:59:59",
        "currency": "EUR"
    }
    resp = client.post(
        "/api/v1/customer-quotes/", 
        json=quote_data, 
        headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
    )
    quote_id = resp.json()["id"]
    
    # Add fee item
    item_data = {
        "item_type": "FEE",
        "description": "Test Item",
        "sell_price": 100.0,
        "cost_price": 0.0,
        "margin_amount": 100.0,
        "margin_percent": 100.0
    }
    resp = client.post(
        f"/api/v1/customer-quotes/{quote_id}/fees",
        json=item_data,
        headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
    )
    item_id = resp.json()["id"]
    
    # Try delete with OTHER Commercial -> Should Fail (Ownership)
    resp = client.delete(
        f"/api/v1/customer-quotes/{quote_id}/items/{item_id}",
        headers={"Authorization": f"Bearer {users['COMMERCIAL_2']['token']}"}
    )
    assert_status(resp, 403, "COMMERCIAL 2 cannot delete COMMERCIAL 1's item")
    
    # Try delete with OWNER Commercial -> Should Pass
    resp = client.delete(
        f"/api/v1/customer-quotes/{quote_id}/items/{item_id}",
        headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
    )
    assert_status(resp, 200, "COMMERCIAL can delete their own item")

    print("\n--------------------------------------------------\n")

    # 5. Verify Public Access to Partners
    print(f"{BOLD}Testing GET /partners (Public/Viewer){RESET}")
    
    resp = client.get(
        "/api/v1/partners/",
        headers={"Authorization": f"Bearer {users['VIEWER']['token']}"}
    )
    assert_status(resp, 200, "VIEWER can see partners")

    print(f"\n{BOLD}Role Verification Complete.{RESET}")
    print(f"Passed: {success_count}")
    print(f"Failed: {fail_count}")

    db.close()

if __name__ == "__main__":
    run_verification()
