import requests
import time
import os
import sys

BASE_URL = "http://localhost:3000/api/v1"

def create_partner():
    partner_data = {
        "code": "BESSON",
        "name": "Transport BESSON",
        "email": "contact@besson.fr"
    }
    r = requests.post(f"{BASE_URL}/partners", json=partner_data)
    if r.status_code == 200 or r.status_code == 201:
        pid = r.json()["id"]
        print(f"Partner created/found: {pid}")
        return pid
    elif r.status_code == 400 or "existe déjà" in r.text:
        # Fetch it
        print("Partner already exists, fetching ID...")
        r = requests.get(f"{BASE_URL}/partners")
        partners = r.json()
        for p in partners:
            if p["code"] == "BESSON":
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
            print(f"Total processed in file: {job['total_rows']}")
            print(f"Quotes created (Success): {job['success_count']}")
            print(f"Errors: {job['error_count']}")
            
            if job.get("errors"):
                print("Errors:", job["errors"])
            return
        
        time.sleep(2)

if __name__ == "__main__":
    partner_id = create_partner()
    file_path = "file_import/grille tarifaire2024 BESSON.xlsx"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
    poll_job(upload_file(partner_id, file_path))
