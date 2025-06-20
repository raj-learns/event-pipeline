import requests
import os
import json
from dotenv import load_dotenv

#  Create data folder if it doesn't exist
os.makedirs("data", exist_ok=True)

load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")
if not API_KEY:
    raise ValueError("API_KEY not found. Please set the SERPAPI_KEY in your .env file.")    

def fetch_events(category, city, start_index=0):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_events",
        "q": category,
        "location": city,
        "google_domain": "google.com",
        "htichips": "date:month",
        "start": start_index,
        "api_key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    filename = f"data/{category}_{start_index}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    categories = ["concerts", "comedy", "music"]
    city = "Bangalore, India"
    for cat in categories:
        for i in range(0, 40, 10):
            fetch_events(cat, city, i)
