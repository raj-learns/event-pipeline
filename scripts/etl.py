import os
import json
import csv
from datetime import datetime, timedelta

INPUT_FOLDER = "data"
OUTPUT_FILE = "cleaned_events.tsv"
TARGET_CITY = "bangalore"  # lowercase for match

def smart_parse_when(when_str):
    """
    Robustly extract start and end datetime from a variety of 'when' strings.
    """
    if not when_str:
        return "-", "-"

    when_str = (
        when_str.replace("a.m.", "AM")
        .replace("p.m.", "PM")
        .replace("–", "-")
        .replace("—", "-")
        .replace(" to ", " - ")
    )

    parts = [p.strip() for p in when_str.split("-")]

    def parse_datetime(raw):
        # Remove weekday (e.g., 'Sat, ')
        if "," in raw:
            raw = raw.split(",", 1)[-1].strip()

        now = datetime.now()
        year = now.year

        # If only time, skip
        if len(raw.split()) <= 2:
            return None

        candidates = [
            f"{raw} {year}",
            f"{raw.replace(',', '')} {year}",
        ]

        formats = [
            "%b %d %I:%M %p %Y",
            "%b %d %I %p %Y",
            "%b %d %Y",
            "%b %d, %I:%M %p %Y",
            "%b %d, %I %p %Y",
        ]

        for date_str in candidates:
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue

        return None


    start_dt = parse_datetime(parts[0])
    if not start_dt:
        return "-", "-"

    # Default year fix (for Python >= 3.15 warning)
    now = datetime.now()
    start_dt = start_dt.replace(year=now.year)

    # Parse end time
    if len(parts) > 1:
        end_raw = parts[1]
        end_dt = parse_datetime(end_raw)
        if end_dt:
            if end_dt.month != start_dt.month or end_dt.day != start_dt.day:
                end_dt = end_dt.replace(year=now.year)
            else:
                # If only time was parsed, match date from start
                end_dt = start_dt.replace(hour=end_dt.hour, minute=end_dt.minute)
        else:
            end_dt = start_dt + timedelta(hours=2)
    else:
        end_dt = start_dt + timedelta(hours=2)

    return start_dt.strftime("%d/%m/%Y %H:%M"), end_dt.strftime("%d/%m/%Y %H:%M")


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
                        title = e.get("title", "-")
                        description = e.get("description", "")
                        link = e.get("link", "")
                        if link:
                            description += f" | {link}"

                        start_date, end_date = smart_parse_when(e.get("date", {}).get("when", ""))
                        location = ", ".join(e.get("address", [])) if e.get("address") else "-"
                        image = e.get("image") or e.get("thumbnail", "-")
                        location_link = e.get("event_location_map", {}).get("link", "-")

                        if TARGET_CITY not in location.lower():
                            continue

                        all_events.append({
                            "title": title,
                            "description": description,
                            "start_date": start_date,
                            "end_date": end_date,
                            "link": link,
                            "image": image,
                            "category": category,
                            "location": location,
                            "location_link": location_link,
                        })

                except json.JSONDecodeError:
                    print(f" Invalid JSON: {filename}")
    return deduplicate_events(all_events)

def deduplicate_events(events):
    unique = {}
    for e in events:
        key = (e["title"], e["start_date"], e["location"])
        if key in unique:
            existing = unique[key]
            if e["category"] not in existing["category"]:
                existing["category"] += f", {e['category']}"
        else:
            e["category"] = e["category"]
            unique[key] = e
    return list(unique.values())

def write_to_tsv(events):
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "title", "description", "start_date", "end_date",
            "link", "image", "category", "location", "location_link"
        ], delimiter='\t')
        writer.writeheader()
        writer.writerows(events)



def write_to_json_payload(events):
    def to_iso(dt_str):
        try:
            return datetime.strptime(dt_str, "%d/%m/%Y %H:%M").isoformat()
        except:
            return None

    output = []
    for e in events:
        payload = {
            "name": e["title"],
            "description": e["description"],
            "startTime": to_iso(e["start_date"]),
            "endTime": to_iso(e["end_date"]),
            "location": {
                "name": e["location"].split(",")[0] if e["location"] != "-" else "Unknown Venue",
                "address": e["location"],
                "url": e["location_link"]
            },
            "coverImage": e["image"],
            "city": TARGET_CITY.title(),
            "country": "India"
        }
        output.append(payload)

    with open("event_payloads.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    events = extract_events()
    write_to_tsv(events)
    write_to_json_payload(events)
    print(f" Cleaned {len(events)} events. Saved to {OUTPUT_FILE} and event_payloads.json")
