import requests, json

base = "http://127.0.0.1:8001"
passed = 0
failed = 0

def test(desc, method, url, body=None, expect=200):
    global passed, failed
    try:
        if method == "GET":
            r = requests.get(base + url, timeout=60)
        else:
            r = requests.post(base + url, json=body, timeout=60)
        if r.status_code == expect:
            passed += 1
            print(f"  ✅ {desc}")
            return r.json() if r.text else None
        else:
            failed += 1
            print(f"  ❌ {desc} — got {r.status_code}, expected {expect}")
            return None
    except Exception as e:
        failed += 1
        print(f"  ❌ {desc} — {str(e)[:50]}")
        return None

print("=" * 60)
print(" PAIRES MATCHER v2 — FULL TEST SUITE")
print("=" * 60)

print("\n--- HEALTH ---")
h = test("Health", "GET", "/api/health")
if h:
    assert h["version"] == "2.0.0"
    assert h["embedding_model"] == "all-MiniLM-L6-v2"
    assert h["database"] == "SQLite"

print("\n--- PROFILES ---")
test("Founders", "GET", "/api/founders")
test("Investors", "GET", "/api/investors")
test("Founder f1", "GET", "/api/founders/f1")
test("Investor i1", "GET", "/api/investors/i1")

print("\n--- MATCHING WITH EMBEDDINGS ---")
m1 = test("Match founder f1", "POST", "/api/match/founder/f1?top_k=3")
if m1:
    for m in m1["matches"]:
        assert 0 <= m["overall_score"] <= 1, f"Score out of range: {m['overall_score']}"
        assert 0 <= m["embedding_score"] <= 1, f"Embedding score out of range: {m['embedding_score']}"
        print(f"    {m['investor']:30s} = {m['overall_score']} (embedding: {m['embedding_score']})")

print("\n--- OUTREACH ---")
o1 = test("Generate outreach", "POST", "/api/outreach/generate?founder_id=f1&investor_id=i6")
if o1:
    assert "{" not in o1["body"] or "investment_partner" not in o1["body"], "Template variable in body"
    print(f"    Subject: {o1['subject'][:60]}...")
    print(f"    Embedding score in details: {o1['match_details']['embedding_score']}")

print("\n--- FEEDBACK ---")
test("Feedback booked", "POST", "/api/feedback?founder_id=f1&investor_id=i1&meeting_booked=true")
test("Feedback pass", "POST", "/api/feedback?founder_id=f2&investor_id=i3&meeting_booked=false")

print("\n--- EVALS ---")
evals = test("Get evals", "GET", "/api/evals")
if evals:
    print(f"    Total matches: {evals['total_matches_generated']}")
    print(f"    With feedback: {evals['matches_with_feedback']}")
    print(f"    Conversion: {evals['conversion_rate']}")
    print(f"    Distribution: {evals['score_distribution']}")

print("\n--- DEMO ---")
demo = test("Full demo", "POST", "/api/demo/run")
if demo:
    print(f"    Matched: {demo['founders_matched']}")
    print(f"    Avg score: {demo['average_top_score']}")
    print(f"    Embedding powered: {demo['embedding_powered']}")

print("\n--- DATABASE PERSISTENCE ---")
r1 = test("Recent matches", "GET", "/api/evals/recent")
r2 = test("Recent feedback", "GET", "/api/evals/feedback")
if r1:
    print(f"    Matches in DB: {len(r1)}")
if r2:
    print(f"    Feedback in DB: {len(r2)}")

print("\n" + "=" * 60)
print(f" RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print(" ALL SYSTEMS GO! v2 with embeddings + SQLite ✅")
print("=" * 60)
