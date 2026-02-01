import requests
import time
import os
import sys

BASE_URL = "http://localhost:3000/api/v1"

def check_health():
    try:
        r = requests.get("http://localhost:3000/health")
        print(f"Health: {r.status_code} - {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def create_partner():
    partner_data = {
        "code": "TEST_IMPORT",
        "name": "Test Import Partner",
        "email": "test@import.com"
    }
    # Check if exists first to avoid duplicate error
    # Actually, let's just create and ignore 400 if it says duplicate
    r = requests.post(f"{BASE_URL}/partners", json=partner_data)
    if r.status_code == 200 or r.status_code == 201:
        pid = r.json()["id"]
        print(f"Partner created/found: {pid}")
        return pid
    elif r.status_code == 400 and "existe déjà" in r.text:
        # Fetch it (assuming we can list or search, but for MVP let's just list all and match code)
        print("Partner already exists, fetching ID...")
        r = requests.get(f"{BASE_URL}/partners")
        partners = r.json()
        for p in partners:
            if p["code"] == "TEST_IMPORT":
                return p["id"]
    print(f"Failed to create/get partner: {r.text}")
    sys.exit(1)

def upload_file(partner_id, file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
        
    print(f"Uploading {file_path}...")
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"partner_id": partner_id}
        r = requests.post(f"{BASE_URL}/imports/", files=files, data=data)
        
    if r.status_code != 201:
        print(f"Upload failed: {r.status_code} - {r.text}")
        sys.exit(1)
        
    job = r.json()
    print(f"Job created: {job['id']} - Status: {job['status']}")
    return job["id"]

def poll_job(job_id):
    print("Polling job status...")
    while True:
        r = requests.get(f"{BASE_URL}/imports/{job_id}")
        job = r.json()
        status = job["status"]
        print(f"Status: {status}")
        
        if status in ["COMPLETED", "FAILED"]:
            print("Job finished.")
            print(f"Total: {job['total_rows']}, Success: {job['success_count']}, Errors: {job['error_count']}")
            if job["errors"]:
                print("Errors:", job["errors"])
            return
        
        time.sleep(1)

if __name__ == "__main__":
    if not check_health():
        print("Backend not ready.")
        sys.exit(1)

    partner_id = create_partner()
    
    # Use a dummy CSV for initial test if no args
    file_path = "test_data.csv"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Create a dummy file
        with open(file_path, "w") as f:
            f.write("mode,origine,pays_origine,destination,pays_dest,poids_min,poids_max,prix,delai\n")
            f.write("ROAD,Paris,FR,Lyon,FR,0,100,50.0,24h\n")
            f.write("ROAD,Marseille,FR,Nice,FR,0,100,30.0,12h\n")

    poll_job(upload_file(partner_id, file_path))
