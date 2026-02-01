import requests
import sys

BASE_URL = "http://localhost:3000/api/v1"

def check_quotes():
    # Get Partner ID
    r = requests.get(f"{BASE_URL}/partners/")
    pid = None
    for p in r.json():
        if p["code"] == "BIANCHI":
            pid = p["id"]
            break
            
    if not pid:
        print("Partner BIANCHI not found.")
        sys.exit(1)
        
    print(f"Checking quotes for partner {pid}...")
    
    # 1. Check Job Status
    r_jobs = requests.get(f"{BASE_URL}/imports/?partner_id={pid}")
    if r_jobs.status_code == 200:
        jobs = r_jobs.json()
        if jobs:
            last_job = jobs[0] # Assuming sorted desc
            print(f"Last Job ID: {last_job['id']}")
            print(f"Status: {last_job['status']}")
            print(f"Rows: {last_job.get('total_rows')}")
            print(f"Success: {last_job.get('success_count')}")
            print(f"Errors: {last_job.get('error_count')}")
            if last_job.get('errors'):
                print("Last Errors:")
                # Errors can be list of dicts or list of objects
                errs = last_job['errors']
                if isinstance(errs, list):
                    for e in errs[:3]: 
                        print(e)
                else:
                    print(errs)
        else:
            print("No import jobs found.")
    
    # 2. Check Count
    r = requests.get(f"{BASE_URL}/quotes/count?partner_id={pid}")

    if r.status_code == 200:
        count = r.json()
        print(f"Total quotes: {count}")
    else:
        print(f"Error: {r.text}")
        
    # List first 5 quotes
    # List ALL quotes (repro potential 500)
    print("Listing ALL quotes (no filter)...")
    r = requests.get(f"{BASE_URL}/quotes/?limit=10")
    if r.status_code == 200:
        quotes = r.json()
        print(f"✅ Success listing all. Count: {len(quotes)}")
        for q in quotes[:3]:
            print(f"- {q.get('origin_city')} -> {q.get('dest_postal_code')}")
    else:
        print(f"❌ Failed to list all quotes! Status: {r.status_code}")
        print(r.text)

if __name__ == "__main__":
    check_quotes()
