"""End-to-end test for all Healthcare Backend API endpoints.

Usage:
    1. Start the server:  python manage.py runserver
    2. Run:               python scripts/test_api.py
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"

passed = 0
failed = 0


def request(method, path, token=None, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return e.code, raw


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


print("== 1. Authentication ==")
status, body = request(
    "POST",
    "/auth/register/",
    data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "secret123",
        "password_confirm": "secret123",
    },
)
check("register returns 201", status == 201, f"got {status}: {body}")

status, _ = request(
    "POST",
    "/auth/register/",
    data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "secret123",
        "password_confirm": "secret123",
    },
)
check("duplicate email rejected (400)", status == 400, f"got {status}")

status, body = request(
    "POST",
    "/auth/login/",
    data={"email": "test@example.com", "password": "secret123"},
)
check("login returns 200 with tokens", status == 200 and "access" in body, f"got {status}: {body}")
token = body["access"] if status == 200 else None

status, _ = request("POST", "/auth/login/", data={"email": "test@example.com", "password": "wrong"})
check("login with wrong password rejected (401)", status == 401, f"got {status}")

print("== 2. Patients ==")
status, _ = request("GET", "/patients/")
check("patients list requires auth (401)", status == 401, f"got {status}")

status, body = request(
    "POST",
    "/patients/",
    token=token,
    data={"name": "Jane Smith", "age": 30, "gender": "Female", "phone_number": "1234567890"},
)
check("create patient returns 201", status == 201, f"got {status}: {body}")
patient_id = body["id"] if status == 201 else None

status, body = request("POST", "/patients/", token=token, data={"name": "Invalid", "age": -5})
check("patient validation errors (400)", status == 400, f"got {status}")

status, body = request("GET", "/patients/", token=token)
check("list patients returns 200", status == 200 and len(body) >= 1, f"got {status}: {body}")

status, body = request("GET", f"/patients/{patient_id}/", token=token)
check("get patient returns 200", status == 200 and body["name"] == "Jane Smith", f"got {status}: {body}")

status, body = request(
    "PUT",
    f"/patients/{patient_id}/",
    token=token,
    data={"name": "Jane Doe", "age": 31, "gender": "Female"},
)
check("update patient returns 200", status == 200 and body["name"] == "Jane Doe", f"got {status}: {body}")

print("== 3. Doctors ==")
status, _ = request("GET", "/doctors/")
check("doctors list requires auth (401)", status == 401, f"got {status}")

status, body = request(
    "POST",
    "/doctors/",
    token=token,
    data={"name": "Dr. House", "specialization": "Diagnostics", "email": "house@example.com"},
)
check("create doctor returns 201", status == 201, f"got {status}: {body}")
doctor_id = body["id"] if status == 201 else None

status, body = request("GET", "/doctors/", token=token)
check("list doctors returns 200", status == 200 and len(body) >= 1, f"got {status}: {body}")

status, body = request("GET", f"/doctors/{doctor_id}/", token=token)
check("get doctor returns 200", status == 200 and body["name"] == "Dr. House", f"got {status}: {body}")

status, body = request(
    "PUT",
    f"/doctors/{doctor_id}/",
    token=token,
    data={"name": "Dr. House", "specialization": "Nephrology", "email": "house@example.com"},
)
check("update doctor returns 200", status == 200 and body["specialization"] == "Nephrology", f"got {status}: {body}")

print("== 4. Mappings ==")
status, _ = request("GET", "/mappings/")
check("mappings list requires auth (401)", status == 401, f"got {status}")

status, body = request(
    "POST", "/mappings/", token=token, data={"patient_id": patient_id, "doctor_id": doctor_id}
)
check("create mapping returns 201", status == 201, f"got {status}: {body}")
mapping_id = body["id"] if status == 201 else None

status, _ = request(
    "POST", "/mappings/", token=token, data={"patient_id": patient_id, "doctor_id": doctor_id}
)
check("duplicate mapping rejected (400)", status == 400, f"got {status}")

status, _ = request("POST", "/mappings/", token=token, data={"patient_id": 9999, "doctor_id": doctor_id})
check("mapping with missing patient rejected (400)", status == 400, f"got {status}")

status, body = request("GET", "/mappings/", token=token)
check("list mappings returns 200", status == 200 and len(body) >= 1, f"got {status}: {body}")

status, body = request("GET", f"/mappings/{patient_id}/", token=token)
check("get doctors for patient returns 200", status == 200 and len(body) >= 1, f"got {status}: {body}")

status, _ = request("DELETE", f"/mappings/{mapping_id}/", token=token)
check("delete mapping returns 204", status == 204, f"got {status}")

status, _ = request("DELETE", f"/mappings/{mapping_id}/", token=token)
check("deleting missing mapping returns 404", status == 404, f"got {status}")

print("== 5. Cleanup ==")
status, _ = request("DELETE", f"/patients/{patient_id}/", token=token)
check("delete patient returns 204", status == 204, f"got {status}")

status, _ = request("DELETE", f"/doctors/{doctor_id}/", token=token)
check("delete doctor returns 204", status == 204, f"got {status}")

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
