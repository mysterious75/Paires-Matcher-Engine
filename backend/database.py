"""
Paires Matcher - SQLite Database Layer
Persistent storage for founders, investors, matches, and feedback
"""
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "matcher.db")


class MatcherDB:
    """SQLite database for persistent matching data"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS founders (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                founder_id TEXT NOT NULL,
                investor_id TEXT NOT NULL,
                overall_score REAL NOT NULL,
                sector_score REAL,
                stage_score REAL,
                geography_score REAL,
                check_size_score REAL,
                embedding_score REAL,
                description TEXT,
                match_reasons TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (founder_id) REFERENCES founders(id),
                FOREIGN KEY (investor_id) REFERENCES investors(id)
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                founder_id TEXT NOT NULL,
                investor_id TEXT NOT NULL,
                meeting_booked BOOLEAN NOT NULL,
                notes TEXT,
                predicted_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS outreach_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                founder_id TEXT NOT NULL,
                investor_id TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                tone TEXT,
                match_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_founder(self, founder: Dict, embedding_bytes: bytes = None):
        """Save founder profile"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO founders (id, data, embedding) VALUES (?, ?, ?)",
            (founder["id"], json.dumps(founder), embedding_bytes)
        )
        conn.commit()
        conn.close()
    
    def save_investor(self, investor: Dict, embedding_bytes: bytes = None):
        """Save investor profile"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO investors (id, data, embedding) VALUES (?, ?, ?)",
            (investor["id"], json.dumps(investor), embedding_bytes)
        )
        conn.commit()
        conn.close()
    
    def get_founder(self, founder_id: str) -> Optional[Dict]:
        """Get founder by ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM founders WHERE id = ?", (founder_id,))
        row = c.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
    
    def get_investor(self, investor_id: str) -> Optional[Dict]:
        """Get investor by ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM investors WHERE id = ?", (investor_id,))
        row = c.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
    
    def get_all_founders(self) -> List[Dict]:
        """Get all founders"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM founders")
        rows = c.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    
    def get_all_investors(self) -> List[Dict]:
        """Get all investors"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM investors")
        rows = c.fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    
    def save_match(self, match: Dict):
        """Save a match result"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO matches (founder_id, investor_id, overall_score, sector_score,
                stage_score, geography_score, check_size_score, embedding_score,
                description, match_reasons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match["founder_id"], match["investor_id"], match["overall_score"],
            match.get("sector_score"), match.get("stage_score"),
            match.get("geography_score"), match.get("check_size_score"),
            match.get("embedding_score"), match.get("description"),
            json.dumps(match.get("match_reasons", []))
        ))
        conn.commit()
        conn.close()
    
    def save_feedback(self, founder_id: str, investor_id: str, meeting_booked: bool,
                      notes: str = None, predicted_score: float = None):
        """Save feedback"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO feedback (founder_id, investor_id, meeting_booked, notes, predicted_score)
            VALUES (?, ?, ?, ?, ?)
        """, (founder_id, investor_id, meeting_booked, notes, predicted_score))
        conn.commit()
        conn.close()
    
    def save_outreach(self, founder_id: str, investor_id: str, subject: str,
                      body: str, tone: str, match_score: float):
        """Save outreach log"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO outreach_log (founder_id, investor_id, subject, body, tone, match_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (founder_id, investor_id, subject, body, tone, match_score))
        conn.commit()
        conn.close()
    
    def get_match_count(self) -> int:
        """Get total matches"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM matches")
        count = c.fetchone()[0]
        conn.close()
        return count
    
    def get_feedback_count(self) -> int:
        """Get total feedback"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM feedback")
        count = c.fetchone()[0]
        conn.close()
        return count
    
    def get_meetings_booked(self) -> int:
        """Get meetings booked"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM feedback WHERE meeting_booked = 1")
        count = c.fetchone()[0]
        conn.close()
        return count
    
    def get_score_distribution(self) -> Dict[str, int]:
        """Get distribution of match scores"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT overall_score FROM matches")
        scores = [r[0] for r in c.fetchall()]
        conn.close()
        
        dist = {"high": 0, "medium": 0, "low": 0}
        for s in scores:
            if s >= 0.7:
                dist["high"] += 1
            elif s >= 0.4:
                dist["medium"] += 1
            else:
                dist["low"] += 1
        return dist
    
    def get_recent_matches(self, limit: int = 10) -> List[Dict]:
        """Get recent matches"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT founder_id, investor_id, overall_score, created_at
            FROM matches ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"founder_id": r[0], "investor_id": r[1], "score": r[2], "created_at": r[3]} for r in rows]
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict]:
        """Get recent feedback"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT founder_id, investor_id, meeting_booked, notes, predicted_score, created_at
            FROM feedback ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return [{"founder_id": r[0], "investor_id": r[1], "meeting_booked": r[2],
                 "notes": r[3], "predicted_score": r[4], "created_at": r[5]} for r in rows]
