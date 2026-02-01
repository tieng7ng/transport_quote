import requests
import sys
import os
import time

BASE_URL = "http://localhost:3000/api/v1"
FILE_PATH = "file_import/ML BIANCHI GROUP PROTOCOLE 01.02.2023  OK FOR 2024 update fuel 1.11.24.xlsx"

def get_bianchi_partner_id():
    r = requests.get(f"{BASE_URL}/partners/")
    if r.status_code != 200:
        print(f"❌ Failed to list partners: {r.text}")
        sys.exit(1)
    
    for p in r.json():
        if p["code"] == "BIANCHI":
            return p["id"]
    
    print("❌ Partner BIANCHI not found. Run create_partner_bianchi.py first.")
    sys.exit(1)

def run_import(partner_id):
    if not os.path.exists(FILE_PATH):
        print(f"❌ File not found: {FILE_PATH}")
        sys.exit(1)
        
    print(f"📤 Uploading file for partner {partner_id}...")
    with open(FILE_PATH, "rb") as f:
        files = {"file": f}
        data = {"partner_id": partner_id}
        r = requests.post(f"{BASE_URL}/imports/", files=files, data=data)
        
    if r.status_code != 201:
        print(f"❌ Upload failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    job = r.json()
    print(f"✅ Job created: {job['id']} - Status: {job['status']}")
    
    # Poll
    print("⏳ Waiting for processing...")
    while True:
        r = requests.get(f"{BASE_URL}/imports/{job['id']}")
        job = r.json()
        print(f"Status: {job['status']}")
        
        if job["status"] in ["COMPLETED", "FAILED"]:
            print(f"\nBenchmark Result:")
            print(f"Total Rows: {job.get('total_rows')}")
            print(f"Success: {job.get('success_count')}")
            print(f"Errors: {job.get('error_count')}")
            
            if job.get('errors'):
                print("\n❌ Errors details:")
                for e in job['errors'][:5]: # Print first 5 errors
                    print(e)
            else:
                print("\n✅ Import Successful!")
            break
        
        time.sleep(1)

if __name__ == "__main__":
    pid = get_bianchi_partner_id()
    run_import(pid)
