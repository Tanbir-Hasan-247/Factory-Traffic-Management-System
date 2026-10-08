import urllib.request
import json
import uuid

BASE_URL = "http://localhost:8000/api"
J_ID = "A"


def post(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


import time

seq = int(time.time() * 1000)

print("Testing arrival...")
evt_id = str(uuid.uuid4())
status, resp = post(
    "/sensor-events",
    {
        "event_id": evt_id,
        "junction_id": J_ID,
        "event_type": "VEHICLE_ARRIVED",
        "vehicle_id": f"v-{evt_id}",
        "vehicle_type": "EMPLOYEE_VEHICLE",
        "direction": "NORTH",
        "sequence_no": seq,
    },
)
print("Arrival:", status, resp)

print("Testing manual...")
status, resp = post(
    f"/junctions/{J_ID}/commands",
    {"command": "MANUAL_GREEN_REQUEST", "direction": "WEST"},
)
print("Manual:", status, resp)

print("Testing status...")
status, resp = get(f"/junctions/{J_ID}")
print("Status:", status, resp)
if resp.get("pending_command_id"):
    cmd_id = resp["pending_command_id"]
    print(f"Found pending command {cmd_id}, ACKing...")
    status, ack_resp = post(
        "/controller-events",
        {"junction_id": J_ID, "status": "ACK", "command_id": cmd_id},
    )
    print("ACK:", status, ack_resp)
else:
    print("No pending command to ACK.")
