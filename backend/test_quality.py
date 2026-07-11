"""
Deep quality check - matching accuracy, spelling, text output
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from profiles import FOUNDER_PROFILES, INVESTOR_PROFILES
from matcher_engine import MatcherEngine
from match_agent import MatchAgent
import json

engine = MatcherEngine()
agent = MatchAgent()

print("=" * 60)
print(" MATCHING QUALITY DEEP CHECK")
print("=" * 60)

issues = []
pass_count = 0

# Test every founder gets sensible top match
print("\n--- Founder → Investor Matching ---\n")
for f in FOUNDER_PROFILES:
    matches = engine.find_best_matches(f, INVESTOR_PROFILES, 3)
    top = matches[0]
    inv = next(i for i in INVESTOR_PROFILES if i["id"] == top.investor_id)
    
    # Check sector alignment
    founder_sector = f["industry"]
    investor_sectors = inv["preferred_sectors"]
    sector_match = any(founder_sector in s or s in founder_sector for s in investor_sectors)
    
    status = "PASS" if (sector_match or top.overall_score > 0.7) else "WARN"
    if status == "WARN":
        issues.append(f"Weak match: {f['company']} ({f['industry']}) → {inv['name']}")
    
    print(f"  {status} {f['company']:20s} ({f['industry']:15s}) → {inv['name']:30s} = {top.overall_score}")
    pass_count += 1
    
    # Check match reasons are meaningful
    for reason in top.match_reasons[:1]:
        if len(reason) < 20:
            issues.append(f"Short reason for {f['company']}: {reason}")
        elif "N/A" in reason or "Unknown" in reason:
            issues.append(f"Placeholder in reason for {f['company']}: {reason}")

# Sector alignment checks
print("\n--- Sector Alignment Checks ---\n")

# HealthTech
health_funders = [f for f in FOUNDER_PROFILES if f["industry"] == "HealthTech"]
health_investors = [i for i in INVESTOR_PROFILES if any("Health" in s or "Bio" in i["name"] for s in i["preferred_sectors"])]
print(f"  HealthTech founders: {[f['company'] for f in health_funders]}")
for f in health_funders:
    m = engine.find_best_matches(f, INVESTOR_PROFILES, 1)
    inv = next(i for i in INVESTOR_PROFILES if i["id"] == m[0].investor_id)
    is_health = any("Health" in s or "Bio" in inv["name"] for s in inv["preferred_sectors"])
    status = "PASS" if is_health else "WARN"
    print(f"    {status} {f['company']} → {inv['name']}")
    if not is_health:
        issues.append(f"HealthTech founder {f['company']} matched to non-health investor {inv['name']}")

# Climate
climate_funders = [f for f in FOUNDER_PROFILES if f["industry"] == "Climate Tech"]
climate_investors = [i for i in INVESTOR_PROFILES if "Climate" in i["preferred_sectors"]]
print(f"\n  Climate Tech founders: {[f['company'] for f in climate_funders]}")
for f in climate_funders:
    m = engine.find_best_matches(f, INVESTOR_PROFILES, 1)
    inv = next(i for i in INVESTOR_PROFILES if i["id"] == m[0].investor_id)
    is_climate = "Climate" in inv["preferred_sectors"]
    status = "PASS" if is_climate else "WARN"
    print(f"    {status} {f['company']} → {inv['name']}")
    if not is_climate:
        issues.append(f"Climate founder {f['company']} matched to non-climate investor {inv['name']}")

# Deep Tech
deep_funders = [f for f in FOUNDER_PROFILES if f["industry"] == "Deep Tech"]
print(f"\n  Deep Tech founders: {[f['company'] for f in deep_funders]}")
for f in deep_funders:
    m = engine.find_best_matches(f, INVESTOR_PROFILES, 1)
    inv = next(i for i in INVESTOR_PROFILES if i["id"] == m[0].investor_id)
    is_deep = "Deep Tech" in inv["preferred_sectors"] or "Defense" in inv["preferred_sectors"]
    status = "PASS" if is_deep else "WARN"
    print(f"    {status} {f['company']} → {inv['name']}")
    if not is_deep:
        issues.append(f"Deep Tech founder {f['company']} matched to non-deep-tech investor {inv['name']}")

# Outreach text quality
print("\n--- Outreach Text Quality ---\n")
import asyncio
for f in FOUNDER_PROFILES[:3]:
    m = engine.find_best_matches(f, INVESTOR_PROFILES, 1)
    inv = next(i for i in INVESTOR_PROFILES if i["id"] == m[0].investor_id)
    outreach = asyncio.run(agent.generate_outreach(f, inv, m[0].overall_score))
    
    print(f"  --- {f['company']} → {inv['name']} ---")
    print(f"  Subject: {outreach['subject']}")
    body = outreach["body"]
    print(f"  Body length: {len(body)} chars")
    
    # Check for issues
    if "{{" in body or "}}" in body:
        issues.append(f"Template syntax in outreach for {f['company']}")
    if "None" in body or "NoneType" in body:
        issues.append(f"Python None in outreach for {f['company']}")
    if body.count("{") > body.count("}"):
        issues.append(f"Unmatched braces in outreach for {f['company']}")
    if len(body) < 100:
        issues.append(f"Outreach too short for {f['company']}: {len(body)} chars")
    
    # Check company name appears
    if f["company"] not in body:
        issues.append(f"Company name {f['company']} missing from outreach")
    if inv["name"] not in body:
        issues.append(f"Investor name {inv['name']} missing from outreach")
    
    pass_count += 1
    print()

# Final summary
print("=" * 60)
if not issues:
    print(" ALL CHECKS PASSED ✅")
else:
    print(f" ISSUES FOUND: {len(issues)}")
    for i in issues:
        print(f"  ⚠️  {i}")
print(f" Checks run: {pass_count + len(issues)}")
print("=" * 60)
