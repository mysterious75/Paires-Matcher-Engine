"""
Final verification - tests all components without server
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from profiles import FOUNDER_PROFILES, INVESTOR_PROFILES
from matcher_engine import MatcherEngine
from match_agent import MatchAgent

print("=== Paires Matcher Engine - Final Verification ===\n")

# Test 1: Profiles loaded
print(f"✅ {len(FOUNDER_PROFILES)} founder profiles loaded")
print(f"✅ {len(INVESTOR_PROFILES)} investor profiles loaded\n")

# Test 2: Engine works
engine = MatcherEngine()
agent = MatchAgent()
print("✅ Engine initialized")
print("✅ Agent initialized\n")

# Test 3: Match a few pairs
test_pairs = [
    ("f1", "i1", "NovaMed AI (HealthTech) x Sequoia (AI/Health focus)"),
    ("f4", "i4", "SustainCrop (Climate) x Climate Fund"),
    ("f3", "i5", "Voxel AI (Enterprise AI) x Founders Fund"),
    ("f8", "i8", "PhotonLink (Deep Tech/Defense) x Shield Capital"),
    ("f10", "i7", "SkillSync (EdTech) x Creandum (European)"),
]

for founder_id, investor_id, desc in test_pairs:
    founder = next(f for f in FOUNDER_PROFILES if f["id"] == founder_id)
    investor = next(i for i in INVESTOR_PROFILES if i["id"] == investor_id)
    match = engine.compute_match(founder, investor)
    print(f"  {desc}")
    print(f"    Score: {match.overall_score} (sector:{match.sector_score} stage:{match.stage_score} geo:{match.geography_score} check:{match.check_size_score})")
    print(f"    Top reason: {match.match_reasons[0] if match.match_reasons else 'N/A'}\n")

# Test 4: Find best matches for all founders
print("=== Best Match for Each Founder ===\n")
for founder in FOUNDER_PROFILES:
    matches = engine.find_best_matches(founder, INVESTOR_PROFILES, 1)
    top = matches[0]
    inv = next(i for i in INVESTOR_PROFILES if i["id"] == top.investor_id)
    print(f"  {founder['company']:20s} → {inv['name']:30s} (score: {top.overall_score})")

print("\n=== ALL TESTS PASSED ✅ ===")
