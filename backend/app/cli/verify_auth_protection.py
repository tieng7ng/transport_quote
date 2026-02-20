import sys
import os
import secrets

# Add backend directory to path so we can import app modules
# Assumes script is run from project root or backend dir
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate

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
    
    # Check if exists (cleanup from previous runs implicitly handled by unique login)
    user_in = UserCreate(
        login=login,
        email=email,
        password=password,
        first_name=f"Test {prefix}",
        last_name="User",
        role=role,
        is_active=True
    )
    
    # Use AuthService to create (handles hashing etc)
    # Note: AuthService.create_user might commit, so we are good.
    try:
        user = AuthService.create_user(db, user_in)
        # Manually activate user as create_user sets it to False by default
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
    print(f"{BOLD}Starting Authentication & RBAC Verification...{RESET}\n")
    
    client = TestClient(app)
    db = SessionLocal()
    
    # 1. Setup Users
    print("Creating test users...")
    roles = {
        "ADMIN": UserRole.ADMIN,
        "COMMERCIAL": UserRole.COMMERCIAL,
        "OPERATOR": UserRole.OPERATOR,
        "VIEWER": UserRole.VIEWER
    }
    
    users = {}
    for name, role in roles.items():
        users[name] = create_test_user(db, role, name.lower())
        if not users[name]:
            print(f"{RED}Failed to create {name} user. Aborting.{RESET}")
            return
        
        # Login to get token
        token = login_user(client, users[name])
        if not token:
            print(f"{RED}Failed to login {name}. Aborting.{RESET}")
            return
        users[name]["token"] = token
        print(f"  - {name}: {users[name]['login']} (Authenticated)")
        
    print("\n--------------------------------------------------\n")
    
    success_count = 0
    fail_count = 0
    
    def assert_status(response, expected_status, test_name):
        nonlocal success_count, fail_count
        if response.status_code == expected_status:
            print(f"{GREEN}[PASS] {test_name}{RESET}")
            success_count += 1
            return True
        else:
            print(f"{RED}[FAIL] {test_name}{RESET}")
            print(f"  Expected: {expected_status}, Got: {response.status_code}")
            print(f"  Response: {response.text}")
            fail_count += 1
            return False

    # 2. Verify POST /customer-quotes protection
    print(f"{BOLD}Testing POST /customer-quotes (Creation){RESET}")
    
    quote_data = {
        "customer_name": "Test Client",
        "customer_email": "client@test.com",
        "customer_company": "Test Corp",
        "valid_until": "2026-12-31T23:59:59",
        "currency": "EUR"
    }
    
    # VIEWER should fail
    resp = client.post(
        "/api/v1/customer-quotes/", 
        json=quote_data, 
        headers={"Authorization": f"Bearer {users['VIEWER']['token']}"}
    )
    assert_status(resp, 403, "VIEWER cannot create quotes")
    
    # COMMERCIAL should succeed
    resp = client.post(
        "/api/v1/customer-quotes/", 
        json=quote_data, 
        headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
    )
    if assert_status(resp, 200, "COMMERCIAL can create quotes"):
        quote_commercial_id = resp.json()["id"]
    else:
        quote_commercial_id = None
        
    # ADMIN should succeed
    resp = client.post(
        "/api/v1/customer-quotes/", 
        json=quote_data, 
        headers={"Authorization": f"Bearer {users['ADMIN']['token']}"}
    )
    if assert_status(resp, 200, "ADMIN can create quotes"):
        quote_admin_id = resp.json()["id"]
    else:
        quote_admin_id = None
        
    print("\n--------------------------------------------------\n")
    
    # 3. Verify GET /customer-quotes Ownership Filtering
    print(f"{BOLD}Testing GET /customer-quotes (Ownership & Visibility){RESET}")
    
    # Commercial should see their own quote
    resp = client.get(
        "/api/v1/customer-quotes/",
        headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
    )
    quotes = resp.json()
    # Check if we find the commercial quote
    found_own = any(q['id'] == quote_commercial_id for q in quotes)
    # Check if we verify NO admin quote (should be invisible to commercial)
    found_other = any(q['id'] == quote_admin_id for q in quotes)
    
    if found_own and not found_other:
        print(f"{GREEN}[PASS] COMMERCIAL sees only their own quotes{RESET}")
        success_count += 1
    else:
        print(f"{RED}[FAIL] COMMERCIAL visibility check failed{RESET}")
        print(f"  Found own: {found_own}, Found admin's: {found_other}")
        fail_count += 1
        
    # ADMIN should see ALL
    resp = client.get(
        "/api/v1/customer-quotes/",
        headers={"Authorization": f"Bearer {users['ADMIN']['token']}"}
    )
    quotes = resp.json()
    if any(q['id'] == quote_commercial_id for q in quotes) and any(q['id'] == quote_admin_id for q in quotes):
        print(f"{GREEN}[PASS] ADMIN sees all quotes{RESET}")
        success_count += 1
    else:
        print(f"{RED}[FAIL] ADMIN visibility check failed (missing quotes){RESET}")
        fail_count += 1

    print("\n--------------------------------------------------\n")

    # 4. Verify DELETE /customer-quotes/{id} Ownership
    print(f"{BOLD}Testing DELETE /customer-quotes/{id} (Ownership){RESET}")
    
    # Commercial try delete Admin quote -> 403 or 404 (depending on impl, 403 pref, 404 acceptable if filtered before)
    # In current impl: get_quote checks ownership for Commercial/Operator -> 403 "Not authorized to view" or "Not found"
    # Actually delete_quote endpoint checks checks existence. 
    # Let's see code: delete_quote does NOT have ownership check inside the function body other than check if exists?
    # Wait, I added: check if target is SUPER_ADMIN... wait that's users.
    # In customer_quotes.py:
    # delete_quote: 
    #     quote = db.query(CustomerQuote)...
    #     if not quote: 404
    #     Permission check? I recall adding require_role("ADMIN", "COMMERCIAL"). 
    #     BUT does it check if COMMERCIAL owns it?
    #     I think I missed adding the specific check `if current_user.role != ADMIN and quote.created_by != current_user.id` inside delete_quote!
    
    # Let's test this vulnerability/feature.
    if quote_admin_id:
        resp = client.delete(
            f"/api/v1/customer-quotes/{quote_admin_id}",
            headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
        )
        if resp.status_code in [403, 404]:
             print(f"{GREEN}[PASS] COMMERCIAL cannot delete ADMIN quote (Status: {resp.status_code}){RESET}")
             success_count += 1
        else:
             print(f"{RED}[FAIL] COMMERCIAL deleted ADMIN quote! (Status: {resp.status_code}){RESET}")
             fail_count += 1
             
    # Commercial delete OWN quote -> 200
    if quote_commercial_id:
        resp = client.delete(
            f"/api/v1/customer-quotes/{quote_commercial_id}",
            headers={"Authorization": f"Bearer {users['COMMERCIAL']['token']}"}
        )
        assert_status(resp, 200, "COMMERCIAL can delete their own quote")

    print(f"\n{BOLD}Verification Complete.{RESET}")
    print(f"Passed: {success_count}")
    print(f"Failed: {fail_count}")

    # Cleanup (Optional)
    # db.close()

if __name__ == "__main__":
    run_verification()
