import requests
import sys

BASE_URL = "http://localhost:3000/api/v1"

def create_bianchi_partner():
    partner_data = {
        "code": "BIANCHI",
        "name": "ML BIANCHI GROUP",
        "email": "contact@bianchi.com"
    }
    
    print(f"Creating partner {partner_data['code']}...")
    try:
        r = requests.post(f"{BASE_URL}/partners/", json=partner_data)
        
        if r.status_code == 201:
            print(f"✅ Partner created successfully: {r.json()['id']}")
            return r.json()['id']
        elif r.status_code == 400 and "existe déjà" in r.text:
            print("⚠️ Partner already exists. Fetching ID...")
            # List all and find by code
            r_list = requests.get(f"{BASE_URL}/partners/")
            for p in r_list.json():
                if p["code"] == "BIANCHI":
                    print(f"✅ Found existing partner: {p['id']}")
                    return p["id"]
        else:
            print(f"❌ Failed to create partner: {r.status_code} - {r.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_bianchi_partner()
