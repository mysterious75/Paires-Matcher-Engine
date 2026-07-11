# Paires Matcher Engine v2

![Paires Matcher Engine Dashboard](screenshot.png)

Production-level matching engine demo for the **Founding AI Engineer** role at Paires.

This is the **core product** of Paires — the two-sided matching engine that pairs founders with the right investors, plus the agent layer that turns matches into booked meetings.

## What's Inside

### Core Matching Engine (`matcher_engine.py`)
- **Real embeddings** using `sentence-transformers` (all-MiniLM-L6-v2)
- **5-dimension weighted scoring**: sector (25%), stage (15%), geography (10%), check size (10%), **embedding similarity (40%)**
- **Feedback loop** — tracks meeting bookings, improves over time
- **Multi-factor ranking** with human-readable match reasons

### Database Layer (`database.py`)
- **SQLite persistence** for all data
- Matches, feedback, outreach logs stored permanently
- Production-ready schema with foreign keys

### Embedding Engine (`embeddings.py`)
- **Sentence-transformers** (all-MiniLM-L6-v2) for real semantic similarity
- Cosine similarity scoring between founder and investor profiles
- Batch embedding support

### Agent Layer (`match_agent.py`)
- Personalized outreach for every matched founder-investor pair
- Tone adapts based on match quality
- Key selling points extracted per match

### Evaluation Framework
- Conversion rate tracking (meeting bookings / total matches)
- Score distribution (high/medium/low)
- Recent matches and feedback history

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

Open **http://localhost:8001/docs** for interactive API docs.

## Architecture

```
MatcherEngine
├── embeddings.py      # Real vector embeddings (sentence-transformers)
├── database.py        # SQLite persistence
├── _score_sector()    # Industry alignment
├── _score_stage()     # Stage compatibility
├── _score_geography() # Region matching
├── _score_check_size()# Deal size fit
└── score_match()      # Semantic similarity (40% weight)

MatchAgent
└── generate_outreach() # Personalized messaging
```

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check (shows v2.0.0, embedding model, DB status) |
| `/api/founders` | GET | List 10 founder profiles |
| `/api/investors` | GET | List 10 investor profiles |
| `/api/match/founder/{id}` | POST | Find best investors with embedding scores |
| `/api/match/all` | POST | Run full two-sided matching |
| `/api/outreach/generate` | POST | Generate personalized outreach |
| `/api/feedback` | POST | Record meeting bookings |
| `/api/evals` | GET | Get matching engine metrics |
| `/api/evals/recent` | GET | Recent matches from database |
| `/api/evals/feedback` | GET | Recent feedback from database |
| `/api/demo/run` | POST | Run full demo |

## v2 vs v1

| Feature | v1 | v2 |
|---------|----|----|
| Scoring | Keyword matching | **Real embeddings (40% weight)** |
| Storage | In-memory | **SQLite database** |
| Persistence | None | **Full match/feedback/outreach logging** |
| Model | N/A | **sentence-transformers all-MiniLM-L6-v2** |

Built for the **Paires Founding AI Engineer** role.
