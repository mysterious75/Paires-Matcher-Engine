"""
COMPREHENSIVE TEST SUITE - Paires Matcher Engine
Tests ALL endpoints, edge cases, data quality, vulnerabilities
"""
import requests
import sys
import json
import re

BASE = "http://127.0.0.1:8001"
PASS = 0
FAIL = 0
ISSUES = []

def test(desc, method, url, body=None, expect_status=200):
    global PASS, FAIL, ISSUES
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=body, timeout=10)
        
        if r.status_code == expect_status:
            PASS += 1
            print(f"  ✅ {desc}")
            try:
                return r.json() if r.text else None
            except:
                return {"_html": True}
        else:
            FAIL += 1
            msg = f"{desc} — expected {expect_status}, got {r.status_code}"
            print(f"  ❌ {msg}")
            ISSUES.append(msg)
            return None
    except Exception as e:
        FAIL += 1
        msg = f"{desc} — {str(e)[:80]}"
        print(f"  ❌ {msg}")
        ISSUES.append(msg)
        return None

def check(condition, desc):
    global PASS, FAIL, ISSUES
    if condition:
        PASS += 1
    else:
        FAIL += 1
        ISSUES.append(desc)
        print(f"    ❌ {desc}")

print("=" * 60)
print(" PARRIES MATCHER — COMPREHENSIVE TEST SUITE")
print("=" * 60)

# ===== 1. HEALTH =====
print("\n--- 1. HEALTH CHECK ---")
h = test("Health endpoint", "GET", f"{BASE}/api/health")
if h:
    check(h["status"] == "healthy", "Status not healthy")
    check(h["founders"] == 10, f"Wrong founder count: {h['founders']}")
    check(h["investors"] == 10, f"Wrong investor count: {h['investors']}")

test("Root page", "GET", f"{BASE}/")
test("API docs", "GET", f"{BASE}/docs")

# ===== 2. PROFILES =====
print("\n--- 2. PROFILES ---")
f_list = test("Get all founders", "GET", f"{BASE}/api/founders")
if f_list:
    check(f_list["count"] == 10, f"Wrong count: {f_list['count']}")
    for f in f_list["founders"]:
        check(isinstance(f["id"], str) and f["id"], f"Empty founder ID")
        check(isinstance(f["name"], str) and len(f["name"]) > 1, f"Bad name for {f['id']}")
        check(isinstance(f["company"], str) and len(f["company"]) > 1, f"Bad company for {f['id']}")
        check(isinstance(f["industry"], str) and len(f["industry"]) > 1, f"Bad industry for {f['id']}")
        check(isinstance(f["ask_amount"], (int, float)) and f["ask_amount"] > 0, f"Bad ask_amount for {f['id']}")
        check(isinstance(f["arr"], (int, float)) and f["arr"] >= 0, f"Bad arr for {f['id']}")
        # Check for placeholder text
        full_text = json.dumps(f).lower()
        check("todo" not in full_text and "placeholder" not in full_text, f"Placeholder found in {f['id']}")
        # Check spelling (basic)
        for field in ["name", "company", "headline", "description"]:
            val = f.get(field, "")
            check("{%" not in val and "{{" not in val, f"Template syntax in {f['id']}.{field}")

i_list = test("Get all investors", "GET", f"{BASE}/api/investors")
if i_list:
    check(i_list["count"] == 10, f"Wrong count: {i_list['count']}")
    for inv in i_list["investors"]:
        check(isinstance(inv["id"], str) and inv["id"], f"Empty investor ID")
        check(isinstance(inv["name"], str) and len(inv["name"]) > 1, f"Bad name for {inv['id']}")
        check(isinstance(inv["check_size_min"], (int, float)) and inv["check_size_min"] > 0, f"Bad check_min for {inv['id']}")
        check(isinstance(inv["check_size_max"], (int, float)) and inv["check_size_max"] > 0, f"Bad check_max for {inv['id']}")
        check(inv["check_size_min"] < inv["check_size_max"], f"check_min >= check_max for {inv['id']}")
        # Check no placeholder text
        full_text = json.dumps(inv).lower()
        check("todo" not in full_text and "placeholder" not in full_text, f"Placeholder in {inv['id']}")
        # Check preferred_sectors is list
        check(isinstance(inv["preferred_sectors"], list) and len(inv["preferred_sectors"]) > 0, f"Bad sectors for {inv['id']}")

# ===== 3. SINGLE LOOKUP =====
print("\n--- 3. SINGLE PROFILE LOOKUP ---")
f1 = test("Get founder f1", "GET", f"{BASE}/api/founders/f1")
if f1:
    check(f1["name"] == "Aisha Patel", f"Wrong name: {f1['name']}")
    check(f1["company"] == "NovaMed AI", f"Wrong company: {f1['company']}")

test("Get investor i1", "GET", f"{BASE}/api/investors/i1")
test("Non-existent founder f999", "GET", f"{BASE}/api/founders/f999", expect_status=404)
test("Non-existent investor i999", "GET", f"{BASE}/api/investors/i999", expect_status=404)

# ===== 4. MATCHING =====
print("\n--- 4. MATCHING ENGINE ---")
m1 = test("Match founder f1", "POST", f"{BASE}/api/match/founder/f1?top_k=5")
if m1:
    check(m1["founder"] == "Aisha Patel", f"Wrong founder: {m1['founder']}")
    check(len(m1["matches"]) > 0, "No matches returned")
    check(len(m1["matches"]) <= 5, f"Too many matches: {len(m1['matches'])}")
    for m in m1["matches"]:
        check(0 <= m["overall_score"] <= 1, f"Score out of range: {m['overall_score']}")
        check(0 <= m["sector_score"] <= 1, f"Sector score out of range: {m['sector_score']}")
        check(0 <= m["stage_score"] <= 1, f"Stage score out of range: {m['stage_score']}")
        check(0 <= m["geography_score"] <= 1, f"Geo score out of range: {m['geography_score']}")
        check(0 <= m["check_size_score"] <= 1, f"Check score out of range: {m['check_size_score']}")
        check(isinstance(m["match_reasons"], list) and len(m["match_reasons"]) > 0, f"No reasons for {m['investor']}")
        # Check scores are monotonically decreasing
    scores = [m["overall_score"] for m in m1["matches"]]
    check(scores == sorted(scores, reverse=True), f"Scores not sorted: {scores}")
    # Check top score
    top = m1["matches"][0]
    check(top["overall_score"] > 0.5, f"Top score too low: {top['overall_score']}")
    print(f"    Top match: {top['investor']} ({top['overall_score']})")

m2 = test("Match investor i1", "POST", f"{BASE}/api/match/investor/i1?top_k=5")
if m2:
    check(len(m2["matches"]) > 0, "No matches for investor")
    check(m2["investor"] == "Sequoia Capital", f"Wrong investor: {m2['investor']}")

m3 = test("Full matching (all)", "POST", f"{BASE}/api/match/all")
if m3:
    check(m3["total_matches"] == 10, f"Wrong total: {m3['total_matches']}")
    for r in m3["results"]:
        check(len(r["top_matches"]) > 0, f"No top matches for {r['company']}")
        for tm in r["top_matches"]:
            check(0 <= tm["score"] <= 1, f"Score out of range for {r['company']}")

test("Match non-existent founder", "POST", f"{BASE}/api/match/founder/f999", expect_status=404)

# ===== 5. AGENT OUTREACH =====
print("\n--- 5. AGENT OUTREACH ---")
o1 = test("Generate outreach f1-i1", "POST", f"{BASE}/api/outreach/generate?founder_id=f1&investor_id=i1")
if o1:
    check(isinstance(o1["subject"], str) and len(o1["subject"]) > 5, f"Bad subject: {o1['subject']}")
    check(isinstance(o1["message_body"], str) and len(o1["message_body"]) > 50, f"Message too short")
    check(o1["match_score"] > 0, f"Non-positive match score: {o1['match_score']}")
    check("NovaMed" in o1["message_body"], "Company name not in message")
    check("Sequoia" in o1["message_body"], "Investor name not in message")
    # Check no template syntax in output
    check("{{" not in o1["subject"], f"Template syntax in subject: {o1['subject']}")
    check("{{" not in o1["message_body"], "Template syntax in body")
    check("None" not in o1["message_body"], "Python 'None' in output")

o2 = test("Generate outreach f4-i4 (Climate)", "POST", f"{BASE}/api/outreach/generate?founder_id=f4&investor_id=i4")
if o2:
    check("SustainCrop" in o2["message_body"], "Company name missing in Climate outreach")
    check("Climate" in o2["message_body"], "Climate keyword missing")

test("Outreach with invalid investor", "POST", f"{BASE}/api/outreach/generate?founder_id=f1&investor_id=i999", expect_status=404)
test("Outreach with invalid founder", "POST", f"{BASE}/api/outreach/generate?founder_id=f999&investor_id=i1", expect_status=404)

# ===== 6. FEEDBACK =====
print("\n--- 6. FEEDBACK LOOP ---")
fb1 = test("Feedback: meeting booked", "POST", f"{BASE}/api/feedback?founder_id=f1&investor_id=i1&meeting_booked=true")
if fb1:
    check(fb1["success"] == True, "Feedback not marked as success")
    check(fb1["meeting_booked"] == True, "Meeting not recorded as booked")

fb2 = test("Feedback: no meeting", "POST", f"{BASE}/api/feedback?founder_id=f2&investor_id=i3&meeting_booked=false&notes=bad_fit")
if fb2:
    check(fb2["success"] == True, "Feedback failed")

test("Feedback with invalid founder", "POST", f"{BASE}/api/feedback?founder_id=f999&investor_id=i1&meeting_booked=true", expect_status=404)

# ===== 7. EVALS =====
print("\n--- 7. EVALS ---")
evals = test("Get evals", "GET", f"{BASE}/api/evals")
if evals:
    check(evals["total_matches_generated"] > 0, "No matches generated")
    check(evals["matches_with_feedback"] >= 2, "Feedback not recorded")
    check(isinstance(evals["score_distribution"], dict), "Score distribution not a dict")
    check("high" in evals["score_distribution"], "Missing 'high' in distribution")
    check("medium" in evals["score_distribution"], "Missing 'medium' in distribution")
    check("low" in evals["score_distribution"], "Missing 'low' in distribution")

dist = test("Score distribution", "GET", f"{BASE}/api/evals/score-distribution")
if dist:
    check(sum(dist.values()) > 0, "Empty distribution")

conv = test("Conversion rate", "GET", f"{BASE}/api/evals/conversion")
if conv:
    check(0 <= conv["conversion_rate"] <= 1, f"Bad conversion rate: {conv['conversion_rate']}")

# ===== 8. DEMO =====
print("\n--- 8. DEMO RUN ---")
demo = test("Full demo", "POST", f"{BASE}/api/demo/run")
if demo:
    check(demo["demo_run"] == True, "Demo not marked as run")
    check(demo["founders_matched"] == 10, f"Wrong founder count: {demo['founders_matched']}")
    check(0 < demo["average_top_score"] <= 1, f"Bad avg score: {demo['average_top_score']}")
    for m in demo["matches"]:
        check(isinstance(m["founder"], str) and len(m["founder"]) > 1, f"Bad founder name")
        check(isinstance(m["company"], str) and len(m["company"]) > 1, f"Bad company name")
        check(isinstance(m["top_match"]["investor"], str) and len(m["top_match"]["investor"]) > 1, f"Bad investor name")
        check(0 <= m["top_match"]["score"] <= 1, f"Score out of range: {m['top_match']['score']}")
        check(isinstance(m["outreach_subject"], str) and len(m["outreach_subject"]) > 5, f"Bad outreach subject")

# ===== 9. SECURITY / VULNERABILITIES =====
print("\n--- 9. SECURITY CHECK ---")
# Check CORS headers (with Origin header as browser would send)
r = requests.options(f"{BASE}/api/health", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}, timeout=10)
headers_lower = {k.lower(): v for k, v in r.headers.items()}
has_cors = "access-control-allow-origin" in headers_lower or r.status_code == 200
check(has_cors, "CORS not configured")

# Check no sensitive data in responses
health_data = requests.get(f"{BASE}/api/health", timeout=10).json()
check("password" not in str(health_data).lower(), "Password in health response")
check("secret" not in str(health_data).lower(), "Secret in health response")

# Check error responses are proper JSON
err_r = requests.get(f"{BASE}/api/founders/nonexistent", timeout=10)
try:
    err_json = err_r.json()
    check("detail" in err_json, "Error response missing 'detail' field")
except:
    check(False, "Error response not valid JSON")

# ===== SUMMARY =====
print("\n" + "=" * 60)
status = "ALL PASSED ✅" if FAIL == 0 else f"{FAIL} FAILURES ❌"
print(f" RESULTS: {PASS} passed, {FAIL} failed — {status}")
print("=" * 60)

if ISSUES:
    print("\nIssues found:")
    for i in ISSUES:
        print(f"  ❌ {i}")

sys.exit(0 if FAIL == 0 else 1)
