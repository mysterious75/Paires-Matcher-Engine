# Paires Matcher Engine

Production-level matching engine demo for the **Founding AI Engineer** role at Paires.

This is the **core product** of Paires — the two-sided matching engine that pairs founders with the right investors, plus the agent layer that turns matches into booked meetings.

## What's Inside

### Core Matching Engine (`matcher_engine.py`)
- **5-dimension weighted scoring**: sector (35%), stage (20%), geography (15%), check size (15%), description similarity (15%)
- **Industry similarity matrix** for cross-sector matching
- **Stage compatibility matrix** for stage-flexible funds
- **Feedback loop** — records meeting bookings, improves over time
- **Multi-factor ranking** with human-readable match reasons

### Agent Layer (`match_agent.py`)
- Personalized outreach for every matched founder-investor pair
- Tone adapts based on match quality (professional / professional-warm)
- Key selling points extracted per match

### Evaluation Framework
- Conversion rate tracking (meeting bookings / total matches)
- Score distribution (high/medium/low)
- Per-investor portfolio relevance scoring

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

Then open **http://localhost:8001/docs** for interactive API docs.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/founders` | GET | List 10 founder profiles |
| `/api/investors` | GET | List 10 investor profiles |
| `/api/match/founder/{id}` | POST | Find best investors for a founder |
| `/api/match/investor/{id}` | POST | Find best founders for an investor |
| `/api/match/all` | POST | Run full two-sided matching |
| `/api/outreach/generate` | POST | Generate personalized outreach |
| `/api/feedback` | POST | Record meeting bookings |
| `/api/evals` | GET | Get matching engine metrics |
| `/api/demo/run` | POST | Run full demo |

## Architecture

```
MatcherEngine
├── _score_sector()      # Industry alignment
├── _score_stage()       # Stage compatibility
├── _score_geography()   # Region matching
├── _score_check_size()  # Deal size fit
└── _score_description() # Text similarity

MatchAgent
└── generate_outreach()  # Personalized messaging
```

Built for the **Paires Founding AI Engineer** role.
