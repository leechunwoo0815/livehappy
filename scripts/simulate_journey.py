"""Simulate real user journeys against the running backend."""
import json
import subprocess
import sys
import uuid
from httpx import Client

SUF = uuid.uuid4().hex[:6]

BASE = "http://127.0.0.1:8001/api"
c = Client(base_url=BASE, timeout=10, trust_env=False)

results = {"pass": 0, "fail": 0, "issues": []}


def step(n, desc):
    print(f"[{n}] {desc}", end=" ... ")


def ok(msg="OK"):
    results["pass"] += 1
    print(msg)


def fail(msg):
    results["fail"] += 1
    results["issues"].append(msg)
    print(f"FAIL: {msg}")


def register(username, email):
    r = c.post("/auth/register", json={"username": username, "email": email, "password": "Test1234!"})
    assert r.status_code == 200, f"register failed: {r.text}"
    return r.json()["data"]["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================
print("=== GUEST JOURNEY ===")
# ============================================================

step(1, "Register guest")
guest_t = register(f"guest_{SUF}", f"guest_{SUF}@test.com")
gh = headers(guest_t)
ok()

step(2, "Search listings (public)")
r = c.get("/listings/search")
assert r.status_code == 200
ok(f"{len(r.json()['data'])} results")

step(3, "Register host")
host_t = register(f"host_{SUF}", f"host_{SUF}@test.com")
hh = headers(host_t)
ok()

step(4, "Host creates listing")
r = c.post("/listings/", json={
    "title": "E2E测试房源", "city": "北京", "price_per_night": 200, "max_guests": 3
}, headers=hh)
assert r.status_code == 201, f"create listing: {r.text}"
lid = r.json()["data"]["id"]
assert r.json()["data"]["status"] == "pending"
ok(f"listing={lid[:8]}... status=pending")

step(5, "Guest tries to book unapproved listing")
r = c.post("/bookings/", json={
    "listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 1
}, headers=gh)
assert r.status_code == 404, f"expected 404, got {r.status_code}"
ok("correctly rejected (404)")

step(6, "Register admin + approve listing")
admin_t = register(f"admin_{SUF}", f"admin_{SUF}@test.com")
subprocess.run(
    ["psql", "-d", "stayhub", "-c", f"UPDATE users SET role='admin' WHERE username='admin_{SUF}'"],
    capture_output=True, text=True,
)
ah = headers(admin_t)
r = c.post(f"/listings/{lid}/approve", json={"action": "approve"}, headers=ah)
assert r.status_code == 200, f"approve: {r.text}"
ok("approved")

step(7, "Search after approval")
r = c.get("/listings/search", params={"city": "北京"})
found = [x for x in r.json()["data"] if x["id"] == lid]
assert len(found) == 1, "listing not found in search"
ok("found in search")

step(8, "Guest creates booking")
r = c.post("/bookings/", json={
    "listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 2
}, headers=gh)
assert r.status_code == 201, f"book: {r.text}"
bid = r.json()["data"]["id"]
assert r.json()["data"]["status"] == "pending"
assert r.json()["data"]["total_price"] == 400
ok(f"booking={bid[:8]}... price=400")

step(9, "Overlap booking rejected")
r = c.post("/bookings/", json={
    "listing_id": lid, "check_in": "2026-07-02", "check_out": "2026-07-04", "guests": 1
}, headers=gh)
assert r.status_code == 409, f"expected 409, got {r.status_code}"
ok("correctly rejected (409)")

step(10, "Guest pays")
r = c.post(f"/bookings/{bid}/pay", headers=gh)
assert r.status_code == 200
assert r.json()["data"]["status"] == "paid"
assert r.json()["data"]["amount"] == 400
assert r.json()["data"]["platform_fee"] == 40
assert r.json()["data"]["host_payout"] == 360
ok(f"paid: amount=400 fee=40 payout=360")

step(11, "Double pay rejected")
r = c.post(f"/bookings/{bid}/pay", headers=gh)
assert r.status_code == 400
ok("correctly rejected (400)")

step(12, "Guest tries review before completion")
r = c.post("/reviews/", params={
    "listing_id": lid, "booking_id": bid, "rating": 5, "content": "很好"
}, headers=gh)
assert r.status_code == 400
ok("correctly rejected (booking not completed)")

step(13, "Complete booking + review")
# Manually set booking to completed
subprocess.run(
    ["psql", "-d", "stayhub", "-c", f"UPDATE bookings SET status='completed' WHERE id='{bid}'"],
    capture_output=True, text=True,
)
r = c.post("/reviews/", params={
    "listing_id": lid, "booking_id": bid, "rating": 5, "content": "非常好的房源！"
}, headers=gh)
assert r.status_code == 200, f"review: {r.text}"
ok("review created")

step(14, "Duplicate review rejected")
r = c.post("/reviews/", params={
    "listing_id": lid, "booking_id": bid, "rating": 4
}, headers=gh)
assert r.status_code == 409
ok("correctly rejected (409)")

step(15, "Guest sends message to host")
host_id = c.get("/users/me", headers=hh).json()["data"]["id"]
r = c.post("/messages/send", json={
    "receiver_id": host_id, "content": "你好，房源还在吗？"
}, headers=gh)
assert r.status_code == 201
ok("message sent")

step(16, "Host reads conversation")
r = c.get("/messages/conversations", headers=hh)
assert r.status_code == 200
assert len(r.json()["data"]) >= 1
conv_id = r.json()["data"][0]["id"]
ok(f"conversation={conv_id[:8]}...")

step(17, "Host marks as read")
r = c.post(f"/messages/conversations/{conv_id}/read", headers=hh)
assert r.status_code == 200
ok("marked read")

step(18, "Guest creates social note")
r = c.post("/social/notes", json={
    "title": "E2E旅行日记", "content": "今天入住了测试房源，非常满意！"
}, headers=gh)
assert r.status_code == 200
nid = r.json()["data"]["id"]
ok(f"note={nid[:8]}...")

step(19, "Host likes note")
r = c.post(f"/social/notes/{nid}/like", headers=hh)
assert r.status_code == 200
ok("liked")

step(20, "Host double-like rejected")
r = c.post(f"/social/notes/{nid}/like", headers=hh)
assert r.status_code == 409
ok("correctly rejected (409)")

step(21, "Host comments on note")
r = c.post(f"/social/notes/{nid}/comments", params={"content": "欢迎下次再来！"}, headers=hh)
assert r.status_code == 200
ok("commented")

step(22, "Host follows guest")
guest_id = c.get("/users/me", headers=gh).json()["data"]["id"]
r = c.post(f"/social/follow/{guest_id}", headers=hh)
assert r.status_code == 200
ok("followed")

step(23, "Double follow rejected")
r = c.post(f"/social/follow/{guest_id}", headers=hh)
assert r.status_code == 409
ok("correctly rejected (409)")

step(24, "Guest views notifications")
r = c.get("/notifications/", headers=gh)
assert r.status_code == 200
ok(f"{r.json()['data']['unread_count']} unread")

step(25, "Guest logout")
r = c.post("/auth/logout", headers=gh)
assert r.status_code == 200
ok()

# ============================================================
print("\n=== ADMIN JOURNEY ===")
# ============================================================

step(26, "Admin views stats")
r = c.get("/admin/stats", headers=ah)
assert r.status_code == 200
d = r.json()["data"]
ok(f"users={d['total_users']} listings={d['total_listings']} bookings={d['total_bookings']}")

step(27, "Admin lists users")
r = c.get("/admin/users", headers=ah)
assert r.status_code == 200
ok(f"{len(r.json()['data']['items'])} users")

step(28, "Admin views audit logs")
r = c.get("/admin/audit-logs", headers=ah)
assert r.status_code == 200
ok(f"{len(r.json()['data']['items'])} logs")

step(29, "Admin bans guest")
r = c.post(f"/admin/users/{guest_id}/ban", headers=ah)
assert r.status_code == 200
ok("banned")

step(30, "Banned guest gets 403")
r = c.get("/bookings/", headers=gh)
# After logout, token is blacklisted. Re-login.
guest_t2 = register(f"guest2_{SUF}", f"guest2_{SUF}@test.com")
guest2_id = c.get("/users/me", headers=headers(guest_t2)).json()["data"]["id"]
# Ban via API (properly syncs DB + Redis)
r_ban = c.post(f"/admin/users/{guest2_id}/ban", headers=ah)
assert r_ban.status_code == 200, f"ban failed: {r_ban.text}"
gh2 = headers(guest_t2)
r = c.get("/bookings/", headers=gh2)
assert r.status_code == 403, f"expected 403, got {r.status_code}"
ok("correctly blocked (403)")

step(31, "Admin unbans guest")
r = c.post(f"/admin/users/{guest_id}/unban", headers=ah)
assert r.status_code == 200
ok("unbanned")

step(32, "Admin changes user role")
r = c.put(f"/admin/users/{guest_id}/role", json={"role": "host"}, headers=ah)
assert r.status_code == 200
ok("role changed to host")

step(33, "Non-admin gets 403 on admin endpoints")
# Re-login as the unbanned guest (old token was blacklisted by logout)
from httpx import Client as _C
login_r = _C(base_url=BASE, timeout=10, trust_env=False).post("/auth/login", json={
    "email": f"guest_{SUF}@test.com", "password": "Test1234!"
})
assert login_r.status_code == 200, f"re-login failed: {login_r.text}"
gh3 = headers(login_r.json()["data"]["access_token"])
r = c.get("/admin/stats", headers=gh3)
assert r.status_code == 403
ok("correctly forbidden")

# ============================================================
print(f"\n=== RESULTS: {results['pass']} passed, {results['fail']} failed ===")
if results["issues"]:
    print("ISSUES:")
    for i in results["issues"]:
        print(f"  - {i}")
else:
    print("ALL SIMULATIONS PASSED")
