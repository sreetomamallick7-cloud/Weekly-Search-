import os
import requests
from dotenv import load_dotenv

def test_serp():
    load_dotenv('.env.local')
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("❌ SERPAPI_KEY not found in .env.local")
        return

    print(f"Testing SerpApi with key: {api_key[:5]}...{api_key[-5:]}")
    
    params = {
        "engine": "google_trends",
        "q": "gold",
        "geo": "IN",
        "date": "today 1-m",
        "api_key": api_key
    }
    
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=20)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            iot = data.get("interest_over_time", {}).get("timeline_data", [])
            print(f"✅ Success! Got {len(iot)} data points for 'gold'.")
        else:
            print(f"❌ Failed: {r.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_serp()
