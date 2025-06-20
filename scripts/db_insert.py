import json
import requests

GRAPHQL_URL = "http://localhost:4000/graphql"  # Update if needed
AUTH_ID = "pinch-event-bot"  # Replace with correct value

def send_event(payload):
    mutation = """
    mutation CreateEvent($authId: String!, $payload: String!) {
      createEvent(authId: $authId, payload: $payload) {
        id
        name
      }
    }
    """
    variables = {
        "authId": AUTH_ID,
        "payload": json.dumps(payload)
    }
    res = requests.post(GRAPHQL_URL, json={"query": mutation, "variables": variables})
    return res.json()

def insert_all_events():
    with open("event_payloads.json", "r", encoding="utf-8") as f:
        events = json.load(f)

    for i, event in enumerate(events):
        res = send_event(event)
        print(f"[{i+1}/{len(events)}] {res}")

if __name__ == "__main__":
    insert_all_events()
