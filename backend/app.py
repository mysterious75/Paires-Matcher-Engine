"""
Paires Matcher Demo - Founding AI Engineer Role
Core matching engine, agent layer, evals, and dashboard
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import datetime
import uuid

from matcher_engine import MatcherEngine, MatchResult
from match_agent import MatchAgent

app = FastAPI(
    title="Paires Matcher Engine — Founding AI Engineer Demo",
    description="""
    ## The Core of Paires
    
    This is the **matching engine** that pairs founders with investors:
    
    - **Embedding-style scoring**: Multi-factor weighted scoring across 5 dimensions
    - **Ranking & Feedback loops**: Track outcomes, improve match quality over time
    - **Agent layer**: Personalized outreach for every matched pair
    - **Evals**: Conversion rates, score distribution, accuracy metrics
    
    Built for the Founding AI Engineer role application.
    """,
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize
engine = MatcherEngine()
agent = MatchAgent()

from profiles import FOUNDER_PROFILES, INVESTOR_PROFILES


# ========== HEALTH ==========

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "engine": "ready",
        "founders": len(FOUNDER_PROFILES),
        "investors": len(INVESTOR_PROFILES),
        "matches_generated": len(engine.match_history)
    }


# ========== PROFILES ==========

@app.get("/api/founders")
async def get_founders():
    """Get all founder profiles"""
    return {"founders": FOUNDER_PROFILES, "count": len(FOUNDER_PROFILES)}

@app.get("/api/investors")
async def get_investors():
    """Get all investor profiles"""
    return {"investors": INVESTOR_PROFILES, "count": len(INVESTOR_PROFILES)}

@app.get("/api/founders/{founder_id}")
async def get_founder(founder_id: str):
    for f in FOUNDER_PROFILES:
        if f["id"] == founder_id:
            return f
    raise HTTPException(404, "Founder not found")

@app.get("/api/investors/{investor_id}")
async def get_investor(investor_id: str):
    for i in INVESTOR_PROFILES:
        if i["id"] == investor_id:
            return i
    raise HTTPException(404, "Investor not found")


# ========== MATCHING ==========

@app.post("/api/match/founder/{founder_id}")
async def match_founder(founder_id: str, top_k: int = Query(5, ge=1, le=10)):
    """Find best investors for a founder"""
    founder = next((f for f in FOUNDER_PROFILES if f["id"] == founder_id), None)
    if not founder:
        raise HTTPException(404, "Founder not found")
    
    matches = engine.find_best_matches(founder, INVESTOR_PROFILES, top_k)
    
    return {
        "founder": founder["name"],
        "company": founder["company"],
        "matches": [
            {
                "investor": _get_investor_name(m.investor_id),
                "investor_id": m.investor_id,
                "overall_score": m.overall_score,
                "sector_score": m.sector_score,
                "stage_score": m.stage_score,
                "geography_score": m.geography_score,
                "check_size_score": m.check_size_score,
                "description": m.description,
                "match_reasons": m.match_reasons
            }
            for m in matches
        ]
    }


@app.post("/api/match/investor/{investor_id}")
async def match_investor(investor_id: str, top_k: int = Query(5, ge=1, le=10)):
    """Find best founders for an investor"""
    investor = next((i for i in INVESTOR_PROFILES if i["id"] == investor_id), None)
    if not investor:
        raise HTTPException(404, "Investor not found")
    
    matches = engine.find_best_matches_for_investor(investor, FOUNDER_PROFILES, top_k)
    
    return {
        "investor": investor["name"],
        "matches": [
            {
                "founder": _get_founder_name(m.founder_id),
                "company": _get_founder_company(m.founder_id),
                "founder_id": m.founder_id,
                "overall_score": m.overall_score,
                "match_reasons": m.match_reasons,
                "description": m.description
            }
            for m in matches
        ]
    }


@app.post("/api/match/all")
async def match_all():
    """Run full matching - find best investors for every founder"""
    results = []
    for founder in FOUNDER_PROFILES:
        matches = engine.find_best_matches(founder, INVESTOR_PROFILES, 3)
        results.append({
            "founder_id": founder["id"],
            "founder_name": founder["name"],
            "company": founder["company"],
            "industry": founder["industry"],
            "top_matches": [
                {
                    "investor": _get_investor_name(m.investor_id),
                    "score": m.overall_score,
                    "reasons": m.match_reasons[:2]
                }
                for m in matches
            ]
        })
    
    return {
        "total_matches": len(results),
        "results": results
    }


# ========== AGENT OUTREACH ==========

@app.post("/api/outreach/generate")
async def generate_outreach(founder_id: str, investor_id: str):
    """Generate personalized outreach message for a matched pair"""
    founder = next((f for f in FOUNDER_PROFILES if f["id"] == founder_id), None)
    investor = next((i for i in INVESTOR_PROFILES if i["id"] == investor_id), None)
    
    if not founder or not investor:
        raise HTTPException(404, "Founder or Investor not found")
    
    match = engine.compute_match(founder, investor)
    outreach = await agent.generate_outreach(founder, investor, match.overall_score)
    
    return {
        "match_score": match.overall_score,
        "subject": outreach["subject"],
        "message_body": outreach["body"],
        "tone": outreach["tone"],
        "key_selling_points": outreach["key_selling_points"],
        "match_details": {
            "sector_score": match.sector_score,
            "stage_score": match.stage_score,
            "geography_score": match.geography_score,
            "check_size_score": match.check_size_score,
            "reasons": match.match_reasons
        }
    }


# ========== FEEDBACK ==========

@app.post("/api/feedback")
async def record_feedback(founder_id: str, investor_id: str, meeting_booked: bool, notes: Optional[str] = None):
    """Record feedback on a match to improve future scoring"""
    match = next((m for m in engine.match_history 
                  if m.founder_id == founder_id and m.investor_id == investor_id), None)
    
    if not match:
        # Compute on the fly
        founder = next((f for f in FOUNDER_PROFILES if f["id"] == founder_id), None)
        investor = next((i for i in INVESTOR_PROFILES if i["id"] == investor_id), None)
        if not founder or not investor:
            raise HTTPException(404, "Founder or Investor not found")
        match = engine.compute_match(founder, investor)
        engine.match_history.append(match)
    
    engine.record_feedback(match, meeting_booked, notes)
    
    return {
        "success": True,
        "recorded": True,
        "meeting_booked": meeting_booked,
        "predicted_score": match.overall_score
    }


# ========== EVALS ==========

@app.get("/api/evals")
async def get_evals():
    """Get matching engine evaluation metrics"""
    return engine.get_evals()


@app.get("/api/evals/score-distribution")
async def get_score_distribution():
    """Get distribution of match scores"""
    return engine._score_distribution()


@app.get("/api/evals/conversion")
async def get_conversion_rate():
    """Get meeting booking conversion rate"""
    total = len(engine.feedback_log)
    booked = sum(1 for f in engine.feedback_log if f["meeting_booked"])
    return {
        "total_feedback": total,
        "meetings_booked": booked,
        "conversion_rate": round(booked / total, 3) if total > 0 else 0,
        "needs_more_data": total < 5
    }


# ========== DEMO ==========

@app.post("/api/demo/run")
async def run_demo():
    """Run complete matching demo"""
    results = []
    
    for founder in FOUNDER_PROFILES:
        matches = engine.find_best_matches(founder, INVESTOR_PROFILES, 3)
        top = matches[0] if matches else None
        outreach = await agent.generate_outreach(founder, 
            next(i for i in INVESTOR_PROFILES if i["id"] == top.investor_id), top.overall_score) if top else None
        
        results.append({
            "founder": founder["name"],
            "company": founder["company"],
            "industry": founder["industry"],
            "top_match": {
                "investor": _get_investor_name(top.investor_id) if top else None,
                "score": top.overall_score if top else 0,
                "reasons": top.match_reasons if top else []
            },
            "outreach_subject": outreach["subject"] if outreach else None
        })
    
    return {
        "demo_run": True,
        "founders_matched": len(results),
        "average_top_score": round(sum(r["top_match"]["score"] for r in results) / len(results), 3),
        "matches": results
    }


# ========== ROOT ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("""
    <!DOCTYPE html><html><body style="font-family:system-ui;max-width:700px;margin:50px auto;padding:20px;background:#0a0a0a;color:white">
    <h1 style="font-size:48px;letter-spacing:-1px">Paires Matcher</h1>
    <p style="color:#888;font-size:18px">Founding AI Engineer Demo — Matching Engine</p>
    <hr style="border-color:#222">
    <h2>Endpoints</h2>
    <ul>
    <li><code>GET /api/founders</code> — 10 founder profiles</li>
    <li><code>GET /api/investors</code> — 10 investor profiles</li>
    <li><code>POST /api/match/founder/{id}</code> — Match a founder</li>
    <li><code>POST /api/match/investor/{id}</code> — Match an investor</li>
    <li><code>POST /api/match/all</code> — Run full matching</li>
    <li><code>POST /api/outreach/generate</code> — Generate outreach</li>
    <li><code>POST /api/feedback</code> — Record feedback</li>
    <li><code>GET /api/evals</code> — Get matching metrics</li>
    <li><code>POST /api/demo/run</code> — Run full demo</li>
    </ul>
    <p><a href="/docs" style="color:#60a5fa">Open API Docs →</a></p>
    <hr style="border-color:#222">
    <p style="color:#666;font-size:13px">Built for Paires — Founding AI Engineer role</p>
    </body></html>
    """)


# ========== HELPERS ==========

def _get_investor_name(investor_id: str) -> str:
    i = next((inv for inv in INVESTOR_PROFILES if inv["id"] == investor_id), None)
    return i["name"] if i else "Unknown"

def _get_founder_name(founder_id: str) -> str:
    f = next((fo for fo in FOUNDER_PROFILES if fo["id"] == founder_id), None)
    return f["name"] if f else "Unknown"

def _get_founder_company(founder_id: str) -> str:
    f = next((fo for fo in FOUNDER_PROFILES if fo["id"] == founder_id), None)
    return f["company"] if f else "Unknown"
