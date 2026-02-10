import requests
import sys

BASE_URL = "http://localhost:3000/api/v1"

def test_auth():
    print("Testing Authentication Flow...")
    
    # 1. Login
    login_data = {
        "username": "admin@transport-quote.fr",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        sys.exit(1)
        
    token_data = response.json()
    access_token = token_data.get("access_token")
    print("✅ Login successful")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Get Me
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code != 200:
        print(f"❌ Get Me failed: {response.status_code} - {response.text}")
        sys.exit(1)
    
    user = response.json()
    if user["email"] != "admin@transport-quote.fr":
        print(f"❌ Incorrect user returned: {user['email']}")
        sys.exit(1)
    print("✅ Get Me successful")
    
    # 3. Access Protected Route (Partners)
    response = requests.get(f"{BASE_URL}/partners/", headers=headers)
    if response.status_code != 200:
        print(f"❌ Access Protected Route failed: {response.status_code} - {response.text}")
        sys.exit(1)
    print("✅ Access Protected Route successful")
    
    # 4. Access Without Token
    response = requests.get(f"{BASE_URL}/partners/")
    if response.status_code != 401:
        print(f"❌ Access Without Token should be 401, got: {response.status_code}")
        sys.exit(1)
    print("✅ Access Without Token blocked as expected")
    
    print("🎉 All Auth tests passed!")

if __name__ == "__main__":
    try:
        test_auth()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Ensure backend is running on port 3000.")
