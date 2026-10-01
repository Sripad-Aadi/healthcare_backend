import json
import sys
import time
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


# Unique suffix so the script can be run multiple times
SUFFIX = str(int(time.time()))
EMAIL_A = f"usera_{SUFFIX}@example.com"
EMAIL_B = f"userb_{SUFFIX}@example.com"

print("== 1. Authentication ==")

# Register user A
status, body = request(
    "POST",
    "/auth/register/",
    data={
        "name": "User A",
        "email": EMAIL_A,
        "password": "secret123",
        "password_confirm": "secret123",
    },
)
check("register user A returns 201", status == 201, f"got {status}: {body}")

# Duplicate email
status, body = request(
    "POST",
    "/auth/register/",
    data={
        "name": "User A Again",
        "email": EMAIL_A,
        "password": "secret123",
        "password_confirm": "secret123",
    },
)
check("duplicate email rejected (400)", status == 400, f"got {status}: {body}")

# Mismatched passwords
status, body = request(
    "POST",
    "/auth/register/",
    data={
        "name": "Bad Passwords",
        "email": f"badpass_{SUFFIX}@example.com",
        "password": "secret123",
        "password_confirm": "different456",
    },
)
check("mismatched passwords rejected (400)", status == 400, f"got {status}: {body}")

# Short password
status, body = request(
    "POST",
    "/auth/register/",
    data={
        "name": "Short Pass",
        "email": f"short_{SUFFIX}@example.com",
        "password": "short",
        "password_confirm": "short",
    },
)
check("short password rejected (400)", status == 400, f"got {status}: {body}")

# Register user B (for cross-user tests)
status, body = request(
    "POST",
    "/auth/register/",
    data={
        "name": "User B",
        "email": EMAIL_B,
        "password": "secret123",
        "password_confirm": "secret123",
    },
)
check("register user B returns 201", status == 201, f"got {status}: {body}")

# Login user A — valid
status, body = request(
    "POST", "/auth/login/", data={"email": EMAIL_A, "password": "secret123"}
)
check(
    "login user A returns 200 with tokens",
    status == 200 and "access" in body,
    f"got {status}: {body}",
)
token_a = body["access"] if status == 200 else None

# Login user B — valid
status, body = request(
    "POST", "/auth/login/", data={"email": EMAIL_B, "password": "secret123"}
)
check(
    "login user B returns 200 with tokens",
    status == 200 and "access" in body,
    f"got {status}: {body}",
)
token_b = body["access"] if status == 200 else None

# Login — wrong password
status, body = request(
    "POST", "/auth/login/", data={"email": EMAIL_A, "password": "wrongpassword"}
)
check("login wrong password rejected (401)", status == 401, f"got {status}: {body}")

# Login — nonexistent email
status, body = request(
    "POST",
    "/auth/login/",
    data={"email": f"nonexistent_{SUFFIX}@example.com", "password": "secret123"},
)
check("login nonexistent email rejected (401)", status == 401, f"got {status}: {body}")

print("== 2. Patients ==")

# Unauthenticated
status, body = request("GET", "/patients/")
check("list patients without auth (401)", status == 401, f"got {status}")

# Create patient for user A
status, body = request(
    "POST",
    "/patients/",
    token=token_a,
    data={
        "name": "Patient A1",
        "age": 30,
        "gender": "Female",
        "phone_number": "1111111111",
    },
)
check("create patient A1 returns 201", status == 201, f"got {status}: {body}")
patient_a1 = body["id"] if status == 201 else None

# Create another patient for user A
status, body = request(
    "POST",
    "/patients/",
    token=token_a,
    data={
        "name": "Patient A2",
        "age": 25,
        "gender": "Male",
        "phone_number": "2222222222",
    },
)
check("create patient A2 returns 201", status == 201, f"got {status}: {body}")
patient_a2 = body["id"] if status == 201 else None

# Create patient for user B
status, body = request(
    "POST",
    "/patients/",
    token=token_b,
    data={
        "name": "Patient B1",
        "age": 40,
        "gender": "Other",
        "phone_number": "3333333333",
    },
)
check("create patient B1 returns 201", status == 201, f"got {status}: {body}")
patient_b1 = body["id"] if status == 201 else None

# Validation — missing required fields
status, body = request("POST", "/patients/", token=token_a, data={"age": -5})
check("create patient invalid data rejected (400)", status == 400, f"got {status}: {body}")

# List — user A sees only own patients
status, body = request("GET", "/patients/", token=token_a)
patient_ids_a = [p["id"] for p in body] if status == 200 else []
check(
    "user A list contains only own patients",
    status == 200
    and patient_a1 in patient_ids_a
    and patient_a2 in patient_ids_a
    and patient_b1 not in patient_ids_a,
    f"got {status}: {body}",
)

# List — user B sees only own patients
status, body = request("GET", "/patients/", token=token_b)
patient_ids_b = [p["id"] for p in body] if status == 200 else []
check(
    "user B list contains only own patients",
    status == 200 and patient_b1 in patient_ids_b and len(patient_ids_b) == 1,
    f"got {status}: {body}",
)

# Get own patient
status, body = request("GET", f"/patients/{patient_a1}/", token=token_a)
check("get own patient returns 200", status == 200, f"got {status}: {body}")

# Get nonexistent patient
status, body = request("GET", "/patients/99999/", token=token_a)
check("get nonexistent patient returns 404", status == 404, f"got {status}: {body}")

# Cross-user get — B tries to access A's patient
status, body = request("GET", f"/patients/{patient_a1}/", token=token_b)
check("cross-user get patient returns 404", status == 404, f"got {status}: {body}")

# Update own patient
status, body = request(
    "PUT",
    f"/patients/{patient_a1}/",
    token=token_a,
    data={"name": "Patient A1 Updated", "age": 31, "gender": "Female"},
)
check(
    "update own patient returns 200",
    status == 200 and body["name"] == "Patient A1 Updated",
    f"got {status}: {body}",
)

# Update nonexistent patient
status, body = request(
    "PUT",
    "/patients/99999/",
    token=token_a,
    data={"name": "Ghost", "age": 1, "gender": "Other"},
)
check("update nonexistent patient returns 404", status == 404, f"got {status}: {body}")

# Cross-user update — B tries to update A's patient
status, body = request(
    "PUT",
    f"/patients/{patient_a1}/",
    token=token_b,
    data={"name": "Hijacked", "age": 99, "gender": "Male"},
)
check("cross-user update patient returns 404", status == 404, f"got {status}: {body}")

print("== 3. Doctors ==")

# Unauthenticated
status, body = request("GET", "/doctors/")
check("list doctors without auth (401)", status == 401, f"got {status}")

# Create doctor
status, body = request(
    "POST",
    "/doctors/",
    token=token_a,
    data={
        "name": "Dr. Smith",
        "specialization": "Cardiology",
        "email": f"smith_{SUFFIX}@example.com",
    },
)
check("create doctor returns 201", status == 201, f"got {status}: {body}")
doctor_1 = body["id"] if status == 201 else None

# Create another doctor
status, body = request(
    "POST",
    "/doctors/",
    token=token_a,
    data={
        "name": "Dr. Jones",
        "specialization": "Neurology",
        "email": f"jones_{SUFFIX}@example.com",
    },
)
check("create doctor 2 returns 201", status == 201, f"got {status}: {body}")
doctor_2 = body["id"] if status == 201 else None

# List doctors
status, body = request("GET", "/doctors/", token=token_a)
check("list doctors returns 200", status == 200 and len(body) >= 2, f"got {status}")

# Get doctor
status, body = request("GET", f"/doctors/{doctor_1}/", token=token_a)
check("get doctor returns 200", status == 200, f"got {status}: {body}")

# Get nonexistent doctor
status, body = request("GET", "/doctors/99999/", token=token_a)
check("get nonexistent doctor returns 404", status == 404, f"got {status}: {body}")

# Update doctor
status, body = request(
    "PUT",
    f"/doctors/{doctor_1}/",
    token=token_a,
    data={
        "name": "Dr. Smith",
        "specialization": "Cardiology",
        "email": f"smith_{SUFFIX}@example.com",
        "years_of_experience": 15,
    },
)
check(
    "update doctor returns 200",
    status == 200 and body["years_of_experience"] == 15,
    f"got {status}: {body}",
)

# Update nonexistent doctor
status, body = request(
    "PUT",
    "/doctors/99999/",
    token=token_a,
    data={"name": "Ghost", "specialization": "None", "email": "ghost@example.com"},
)
check("update nonexistent doctor returns 404", status == 404, f"got {status}: {body}")

print("== 4. Mappings ==")

# Unauthenticated
status, body = request("GET", "/mappings/")
check("list mappings without auth (401)", status == 401, f"got {status}")

# Create mapping — user A assigns doctor to own patient
status, body = request(
    "POST",
    "/mappings/",
    token=token_a,
    data={"patient_id": patient_a1, "doctor_id": doctor_1},
)
check("create mapping returns 201", status == 201, f"got {status}: {body}")
mapping_1 = body["id"] if status == 201 else None

# Create another mapping
status, body = request(
    "POST",
    "/mappings/",
    token=token_a,
    data={"patient_id": patient_a1, "doctor_id": doctor_2},
)
check("create mapping 2 returns 201", status == 201, f"got {status}: {body}")
mapping_2 = body["id"] if status == 201 else None

# Duplicate mapping
status, body = request(
    "POST",
    "/mappings/",
    token=token_a,
    data={"patient_id": patient_a1, "doctor_id": doctor_1},
)
check("duplicate mapping rejected (400)", status == 400, f"got {status}: {body}")

# Mapping with nonexistent patient
status, body = request(
    "POST",
    "/mappings/",
    token=token_a,
    data={"patient_id": 99999, "doctor_id": doctor_1},
)
check("mapping nonexistent patient rejected (400)", status == 400, f"got {status}: {body}")

# Mapping with nonexistent doctor
status, body = request(
    "POST",
    "/mappings/",
    token=token_a,
    data={"patient_id": patient_a1, "doctor_id": 99999},
)
check("mapping nonexistent doctor rejected (400)", status == 400, f"got {status}: {body}")

# Cross-user mapping — B tries to assign doctor to A's patient
status, body = request(
    "POST",
    "/mappings/",
    token=token_b,
    data={"patient_id": patient_a1, "doctor_id": doctor_1},
)
check("cross-user create mapping rejected (400)", status == 400, f"got {status}: {body}")

# List mappings — user A sees only own
status, body = request("GET", "/mappings/", token=token_a)
mapping_patient_ids = [m["patient"] for m in body] if status == 200 else []
check(
    "user A mappings list only own patients",
    status == 200
    and patient_a1 in mapping_patient_ids
    and patient_b1 not in mapping_patient_ids,
    f"got {status}: {body}",
)

# List mappings — user B sees only own (none yet)
status, body = request("GET", "/mappings/", token=token_b)
check(
    "user B mappings list empty (no own mappings)",
    status == 200 and len(body) == 0,
    f"got {status}: {body}",
)

# Get doctors for patient — user A
status, body = request("GET", f"/mappings/{patient_a1}/", token=token_a)
check(
    "get doctors for own patient returns 200",
    status == 200 and len(body) == 2,
    f"got {status}: {body}",
)

# Get doctors for nonexistent patient
status, body = request("GET", "/mappings/99999/", token=token_a)
check("get doctors nonexistent patient returns 404", status == 404, f"got {status}: {body}")

# Cross-user get doctors — B tries A's patient
status, body = request("GET", f"/mappings/{patient_a1}/", token=token_b)
check("cross-user get doctors returns 404", status == 404, f"got {status}: {body}")

# Delete mapping — user A
status, body = request("DELETE", f"/mappings/{mapping_1}/", token=token_a)
check("delete mapping returns 204", status == 204, f"got {status}")

# Delete nonexistent mapping
status, body = request("DELETE", "/mappings/99999/", token=token_a)
check("delete nonexistent mapping returns 404", status == 404, f"got {status}: {body}")

# Cross-user delete — B tries to delete A's mapping
status, body = request("DELETE", f"/mappings/{mapping_2}/", token=token_b)
check("cross-user delete mapping returns 404", status == 404, f"got {status}: {body}")

print("== 5. Cleanup ==")

# User A deletes own mapping
status, body = request("DELETE", f"/mappings/{mapping_2}/", token=token_a)
check("delete remaining mapping returns 204", status == 204, f"got {status}")

# User A deletes own patients
status, body = request("DELETE", f"/patients/{patient_a1}/", token=token_a)
check("delete patient A1 returns 204", status == 204, f"got {status}")

status, body = request("DELETE", f"/patients/{patient_a2}/", token=token_a)
check("delete patient A2 returns 204", status == 204, f"got {status}")

# Cross-user delete — B tries to delete A's patient
status, body = request("DELETE", f"/patients/{patient_a1}/", token=token_b)
check("cross-user delete patient returns 404", status == 404, f"got {status}: {body}")

# User B deletes own patient
status, body = request("DELETE", f"/patients/{patient_b1}/", token=token_b)
check("delete patient B1 returns 204", status == 204, f"got {status}")

# Delete doctors
status, body = request("DELETE", f"/doctors/{doctor_1}/", token=token_a)
check("delete doctor 1 returns 204", status == 204, f"got {status}")

status, body = request("DELETE", f"/doctors/{doctor_2}/", token=token_a)
check("delete doctor 2 returns 204", status == 204, f"got {status}")

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
