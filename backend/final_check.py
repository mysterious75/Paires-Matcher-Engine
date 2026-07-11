import requests

base = "http://127.0.0.1:8001"

tests = [
    ("GET", "/api/health", "Health"),
    ("GET", "/api/founders", "Founders"),
    ("GET", "/api/investors", "Investors"),
    ("GET", "/api/founders/f1", "Single founder"),
    ("GET", "/api/investors/i1", "Single investor"),
    ("GET", "/api/evals", "Evals"),
    ("GET", "/api/evals/conversion", "Conversion"),
    ("POST", "/api/match/founder/f1", "Match founder"),
    ("POST", "/api/match/investor/i1", "Match investor"),
    ("POST", "/api/match/all", "Match all"),
    ("POST", "/api/outreach/generate?founder_id=f1&investor_id=i1", "Outreach"),
    ("POST", "/api/feedback?founder_id=f1&investor_id=i1&meeting_booked=true", "Feedback"),
    ("POST", "/api/demo/run", "Demo"),
]

passed = 0
failed = 0
for method, url, desc in tests:
    try:
        if method == "GET":
            r = requests.get(base + url, timeout=5)
        else:
            r = requests.post(base + url, timeout=5)
        if r.status_code == 200:
            passed += 1
        else:
            failed += 1
            print(f"FAIL: {desc} returned {r.status_code}")
    except Exception as e:
        failed += 1
        print(f"FAIL: {desc} - {str(e)[:50]}")

# Check outreach has no template vars
r = requests.post(base + "/api/outreach/generate?founder_id=f1&investor_id=i6", timeout=5)
body = r.json()["body"]
if "{" in body and "investment_partner" in body:
    failed += 1
    print("FAIL: Template variable in outreach")
else:
    passed += 1

# Check all founder profiles have data
r = requests.get(base + "/api/founders", timeout=5)
for f in r.json()["founders"]:
    if not f.get("name") or not f.get("company"):
        failed += 1
        print(f"FAIL: Empty profile {f.get('id')}")
    else:
        passed += 1

print(f"\n=== FINAL: {passed} passed, {failed} failed ===")
if failed == 0:
    print("ALL SYSTEMS GO!")
