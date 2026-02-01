import requests
import json
from datetime import date

URL = "http://localhost:3000/api/v1/match/"

def test_payload(name, payload):
    print(f"--- Testing {name} ---")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(URL, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("Validation Error Response:")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 200:
            print("Success")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")
    print("\n")

def run_tests():
    # 1. Valid Payload (Baseline)
    base_payload = {
        "origin_country": "FR",
        "origin_postal_code": "06000",
        "dest_country": "FR",
        "dest_postal_code": "75001",
        "weight": 500,
        "shipping_date": str(date.today())
    }
    test_payload("Baseline (Valid)", base_payload)

    # 2. Empty Transport Mode (Potential Frontend Issue)
    payload_empty_mode = base_payload.copy()
    payload_empty_mode["transport_mode"] = "" 
    test_payload("Empty Transport Mode string", payload_empty_mode)

    # 3. String Weight (Potential Frontend Issue)
    payload_string_weight = base_payload.copy()
    payload_string_weight["weight"] = "500" # Should be auto-casted by Pydantic usually, but worth checking
    test_payload("String Weight", payload_string_weight)

    # 4. Missing required field
    payload_missing = base_payload.copy()
    del payload_missing["origin_country"]
    test_payload("Missing Origin Country", payload_missing)

if __name__ == "__main__":
    run_tests()
