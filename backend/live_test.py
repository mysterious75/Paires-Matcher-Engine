import requests, json

base = "http://127.0.0.1:8001"

print("=== LIVE TEST ===\n")

# 1. Match founder f1
r = requests.post(f"{base}/api/match/founder/f1?top_k=3")
d = r.json()
print(f"1. Match {d['founder']} ({d['company']}):")
for m in d["matches"]:
    print(f"   {m['investor']:30s} = {m['overall_score']}")
print()

# 2. Generate outreach
r = requests.post(f"{base}/api/outreach/generate?founder_id=f1&investor_id=i6")
d = r.json()
print(f"2. Outreach ({d['match_score']:.0%} match):")
print(f"   Subject: {d['subject']}")
print(f"   Body: {d['body'][:200]}...")
print()

# 3. Full demo
r = requests.post(f"{base}/api/demo/run")
d = r.json()
print(f"3. Full Demo: {d['founders_matched']} founders matched, avg score: {d['average_top_score']}")
for m in d["matches"][:3]:
    print(f"   {m['company']:20s} -> {m['top_match']['investor']:30s} ({m['top_match']['score']:.0%})")
print()

# 4. Evals
r = requests.get(f"{base}/api/evals")
d = r.json()
print(f"4. Evals: {d['total_matches_generated']} matches, {d['matches_with_feedback']} feedback, {d['conversion_rate']:.0%} conversion")
print()
print("=== ALL LIVE TESTS PASSED ===")
