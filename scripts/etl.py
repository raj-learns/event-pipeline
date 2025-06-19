import os
import json
import csv
from datetime import datetime

INPUT_FOLDER = "data"
OUTPUT_FILE = "cleaned_events.csv"

def parse_time(text):
    try:
        dt = datetime.strptime(text, "%a, %b %d, %I:%M %p")
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return "-"

def extract_events():
    all_events = []

    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith(".json"):
            path = os.path.join(INPUT_FOLDER, filename)
            with open(path, "r") as file:
                try:
                    data = json.load(file)
                    events = data.get("events_results", [])
                    category = filename.split("_")[0]
                    for e in events:
                        event = {
                            "title": e.get("title", "-"),
                            "description": e.get("description", "-"),
                            "start_date": parse_time(e.get("date", {}).get("when", "-")),
                            "end_date": "-",  # optional
                            "link": e.get("link", "-"),
                            "image": e.get("image", "-"),
                            "category": category,
                            "location": ", ".join(e.get("address", [])) if e.get("address") else "-",
                        }
                        all_events.append(event)
                except json.JSONDecodeError:
                    print(f"Invalid JSON in file: {filename}")
    return all_events

def write_to_csv(events):
    with open("cleaned_events.tsv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "description", "start_date", "end_date",
            "link", "image", "category", "location"
        ], delimiter='\t')  # <-- Set tab as delimiter

        writer.writeheader()
        writer.writerows(events)

if __name__ == "__main__":
    events = extract_events()
    write_to_csv(events)
    print(f"✅ Cleaned {len(events)} events. Saved to {OUTPUT_FILE}")
