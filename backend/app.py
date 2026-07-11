"""
Paires Matcher v2 - Founding AI Engineer Demo
Real embeddings + SQLite + production matching engine
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional

from matcher_engine import MatcherEngine
from match_agent import MatchAgent
from profiles import FOUNDER_PROFILES, INVESTOR_PROFILES

app = FastAPI(
    title="Paires Matcher Engine v2",
    description="Production matching engine with real embeddings and SQLite persistence",
    version="2.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

engine = MatcherEngine()
agent = MatchAgent()


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "engine": "ready",
        "embedding_model": "all-MiniLM-L6-v2",
        "database": "SQLite",
        "founders": len(FOUNDER_PROFILES),
        "investors": len(INVESTOR_PROFILES),
        "total_matches": engine.db.get_match_count(),
        "total_feedback": engine.db.get_feedback_count()
    }


@app.get("/api/founders")
async def get_founders():
    return {"founders": FOUNDER_PROFILES, "count": len(FOUNDER_PROFILES)}


@app.get("/api/investors")
async def get_investors():
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


@app.post("/api/match/founder/{founder_id}")
async def match_founder(founder_id: str, top_k: int = Query(5, ge=1, le=10)):
    founder = next((f for f in FOUNDER_PROFILES if f["id"] == founder_id), None)
    if not founder:
        raise HTTPException(404, "Founder not found")
    
    matches = engine.find_best_matches(founder, INVESTOR_PROFILES, top_k)
    
    return {
        "founder": founder["name"],
        "company": founder["company"],
        "matches": [
            {
                "investor": next((i["name"] for i in INVESTOR_PROFILES if i["id"] == m.investor_id), "Unknown"),
                "investor_id": m.investor_id,
                "overall_score": m.overall_score,
                "sector_score": m.sector_score,
                "stage_score": m.stage_score,
                "geography_score": m.geography_score,
                "check_size_score": m.check_size_score,
                "embedding_score": m.embedding_score,
                "description": m.description,
                "match_reasons": m.match_reasons
            }
            for m in matches
        ]
    }


@app.post("/api/match/investor/{investor_id}")
async def match_investor(investor_id: str, top_k: int = Query(5, ge=1, le=10)):
    investor = next((i for i in INVESTOR_PROFILES if i["id"] == investor_id), None)
    if not investor:
        raise HTTPException(404, "Investor not found")
    
    matches = engine.find_best_matches_for_investor(investor, FOUNDER_PROFILES, top_k)
    
    return {
        "investor": investor["name"],
        "matches": [
            {
                "founder": next((f["name"] for f in FOUNDER_PROFILES if f["id"] == m.founder_id), "Unknown"),
                "company": next((f["company"] for f in FOUNDER_PROFILES if f["id"] == m.founder_id), "Unknown"),
                "founder_id": m.founder_id,
                "overall_score": m.overall_score,
                "embedding_score": m.embedding_score,
                "match_reasons": m.match_reasons,
                "description": m.description
            }
            for m in matches
        ]
    }


@app.post("/api/match/all")
async def match_all():
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
                    "investor": next((i["name"] for i in INVESTOR_PROFILES if i["id"] == m.investor_id), "Unknown"),
                    "score": m.overall_score,
                    "embedding_score": m.embedding_score,
                    "reasons": m.match_reasons[:2]
                }
                for m in matches
            ]
        })
    return {"total_matches": len(results), "results": results}


@app.post("/api/outreach/generate")
async def generate_outreach(founder_id: str, investor_id: str):
    founder = next((f for f in FOUNDER_PROFILES if f["id"] == founder_id), None)
    investor = next((i for i in INVESTOR_PROFILES if i["id"] == investor_id), None)
    
    if not founder or not investor:
        raise HTTPException(404, "Founder or Investor not found")
    
    match = engine.compute_match(founder, investor)
    outreach = await agent.generate_outreach(founder, investor, match.overall_score)
    
    # Save to database
    engine.db.save_outreach(
        founder_id, investor_id,
        outreach["subject"], outreach["body"],
        outreach["tone"], match.overall_score
    )
    
    return {
        "match_score": match.overall_score,
        "embedding_score": match.embedding_score,
        "subject": outreach["subject"],
        "body": outreach["body"],
        "tone": outreach["tone"],
        "key_selling_points": outreach["key_selling_points"],
        "match_details": {
            "sector_score": match.sector_score,
            "stage_score": match.stage_score,
            "geography_score": match.geography_score,
            "check_size_score": match.check_size_score,
            "embedding_score": match.embedding_score,
            "reasons": match.match_reasons
        }
    }


@app.post("/api/feedback")
async def record_feedback(founder_id: str, investor_id: str, meeting_booked: bool, notes: Optional[str] = None):
    founder = next((f for f in FOUNDER_PROFILES if f["id"] == founder_id), None)
    investor = next((i for i in INVESTOR_PROFILES if i["id"] == investor_id), None)
    
    if not founder or not investor:
        raise HTTPException(404, "Founder or Investor not found")
    
    predicted_score = engine.compute_match(founder, investor).overall_score
    engine.record_feedback(founder_id, investor_id, meeting_booked, notes, predicted_score)
    
    return {
        "success": True,
        "meeting_booked": meeting_booked,
        "predicted_score": predicted_score
    }


@app.get("/api/evals")
async def get_evals():
    return engine.get_evals()


@app.get("/api/evals/recent")
async def get_recent_matches():
    return engine.db.get_recent_matches(20)


@app.get("/api/evals/feedback")
async def get_recent_feedback():
    return engine.db.get_recent_feedback(20)


@app.post("/api/demo/run")
async def run_demo():
    results = []
    for founder in FOUNDER_PROFILES:
        matches = engine.find_best_matches(founder, INVESTOR_PROFILES, 3)
        top = matches[0] if matches else None
        inv = next((i for i in INVESTOR_PROFILES if i["id"] == top.investor_id), None) if top else None
        outreach = await agent.generate_outreach(founder, inv, top.overall_score) if inv else None
        
        results.append({
            "founder": founder["name"],
            "company": founder["company"],
            "industry": founder["industry"],
            "top_match": {
                "investor": inv["name"] if inv else "N/A",
                "score": top.overall_score if top else 0,
                "embedding_score": top.embedding_score if top else 0,
                "reasons": top.match_reasons if top else []
            },
            "outreach_subject": outreach["subject"] if outreach else None
        })
    
    return {
        "demo_run": True,
        "founders_matched": len(results),
        "average_top_score": round(sum(r["top_match"]["score"] for r in results) / len(results), 3),
        "embedding_powered": True,
        "matches": results
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("""
    <!DOCTYPE html><html><body style="font-family:system-ui;max-width:700px;margin:50px auto;padding:20px;background:#0a0a0a;color:white">
    <h1 style="font-size:48px;letter-spacing:-1px">Paires Matcher v2</h1>
    <p style="color:#888;font-size:18px">Real Embeddings + SQLite + Production Matching Engine</p>
    <hr style="border-color:#222">
    <h2>v2 Features</h2>
    <ul>
    <li><strong>Real Embeddings:</strong> sentence-transformers all-MiniLM-L6-v2</li>
    <li><strong>SQLite Database:</strong> Persistent storage for matches, feedback, outreach</li>
    <li><strong>40% Embedding Weight:</strong> Semantic similarity as primary scoring factor</li>
    <li><strong>Feedback Loop:</strong> Tracks meeting bookings to improve over time</li>
    </ul>
    <h2>Endpoints</h2>
    <ul>
    <li><code>GET /api/founders</code> — 10 founder profiles</li>
    <li><code>GET /api/investors</code> — 10 investor profiles</li>
    <li><code>POST /api/match/founder/{id}</code> — Match a founder</li>
    <li><code>POST /api/match/all</code> — Run full matching</li>
    <li><code>POST /api/outreach/generate</code> — Generate outreach</li>
    <li><code>POST /api/feedback</code> — Record feedback</li>
    <li><code>GET /api/evals</code> — Get matching metrics</li>
    <li><code>POST /api/demo/run</code> — Run full demo</li>
    </ul>
    <p><a href="/docs" style="color:#60a5fa">Open API Docs →</a></p>
    </body></html>
    """)
