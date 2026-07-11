"""
Paires Matcher - Core Matching Engine v2
Real embeddings + SQLite database + multi-factor scoring
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import json

from embeddings import EmbeddingEngine
from database import MatcherDB


@dataclass
class MatchResult:
    founder_id: str
    investor_id: str
    overall_score: float
    sector_score: float
    stage_score: float
    geography_score: float
    check_size_score: float
    embedding_score: float
    description: str
    match_reasons: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MatcherEngine:
    """
    Production matching engine with real embeddings and database persistence
    """
    
    WEIGHTS = {
        "sector": 0.25,
        "stage": 0.15,
        "geography": 0.10,
        "check_size": 0.10,
        "embedding": 0.40
    }
    
    def __init__(self):
        self.db = MatcherDB()
        self.embeddings = EmbeddingEngine()
        self.sector_similarity = {
            "Enterprise AI": {"HealthTech": 0.6, "Fintech": 0.5, "Deep Tech": 0.7, "Enterprise SaaS": 0.8, "Robotics": 0.5},
            "HealthTech": {"Enterprise AI": 0.6, "BioTech": 0.9, "Life Sciences": 0.9, "Deep Tech": 0.5},
            "Fintech": {"Enterprise AI": 0.5, "Enterprise SaaS": 0.6, "Deep Tech": 0.3, "Security": 0.5},
            "Climate Tech": {"Clean Energy": 0.9, "Sustainable Materials": 0.9, "Agriculture": 0.8},
            "Deep Tech": {"Enterprise AI": 0.7, "Defense": 0.8, "Space": 0.8, "Robotics": 0.8},
            "Enterprise SaaS": {"Enterprise AI": 0.8, "Fintech": 0.6, "Security": 0.8, "EdTech": 0.5},
        }
        self.stage_compatibility = {
            "Pre-Seed": {"Pre-Seed": 1.0, "Seed": 0.8, "Series A": 0.4, "Series B": 0.1},
            "Seed": {"Pre-Seed": 0.7, "Seed": 1.0, "Series A": 0.8, "Series B": 0.4},
            "Series A": {"Seed": 0.6, "Series A": 1.0, "Series B": 0.8},
            "Series B": {"Series A": 0.7, "Series B": 1.0},
        }
    
    def _founder_to_text(self, founder: Dict) -> str:
        """Convert founder profile to text for embedding"""
        parts = [
            f"{founder.get('company', '')} - {founder.get('headline', '')}",
            f"Industry: {founder.get('industry', '')}, Sub: {founder.get('sub_industry', '')}",
            f"Stage: {founder.get('funding_stage', '')}, Ask: ${founder.get('ask_amount', 0)//1000000}M",
            f"Description: {founder.get('description', '')}",
            f"Looking for: {', '.join(founder.get('looking_for', []))}",
            f"Technical: {', '.join(founder.get('technical_stack', []))}",
        ]
        return " | ".join(parts)
    
    def _investor_to_text(self, investor: Dict) -> str:
        """Convert investor profile to text for embedding"""
        parts = [
            f"{investor.get('name', '')} - {investor.get('type', '')}",
            f"Sectors: {', '.join(investor.get('preferred_sectors', []))}",
            f"Stages: {', '.join(investor.get('preferred_stages', []))}",
            f"Check: ${investor.get('check_size_min', 0)//1000000}M - ${investor.get('check_size_max', 0)//1000000}M",
            f"Geography: {investor.get('geography', '')}, Focus: {', '.join(investor.get('focus_geographies', []))}",
            f"Thesis: {investor.get('investment_thesis', '')}",
            f"Portfolio: {', '.join(investor.get('portfolio_highlights', []))}",
        ]
        return " | ".join(parts)
    
    def compute_match(self, founder: Dict, investor: Dict) -> MatchResult:
        """Compute full match score with embeddings"""
        sector_score = self._score_sector(founder, investor)
        stage_score = self._score_stage(founder, investor)
        geography_score = self._score_geography(founder, investor)
        check_size_score = self._score_check_size(founder, investor)
        
        # Real embedding similarity
        founder_text = self._founder_to_text(founder)
        investor_text = self._investor_to_text(investor)
        embedding_score = self.embeddings.score_match(founder_text, investor_text)
        embedding_score = max(0, min(embedding_score, 1.0))  # Clamp 0-1
        
        overall = (
            sector_score * self.WEIGHTS["sector"] +
            stage_score * self.WEIGHTS["stage"] +
            geography_score * self.WEIGHTS["geography"] +
            check_size_score * self.WEIGHTS["check_size"] +
            embedding_score * self.WEIGHTS["embedding"]
        )
        
        reasons = self._generate_reasons(founder, investor, sector_score, stage_score, embedding_score)
        description = self._generate_description(founder, investor, overall, embedding_score)
        
        return MatchResult(
            founder_id=founder["id"],
            investor_id=investor["id"],
            overall_score=round(overall, 3),
            sector_score=round(sector_score, 3),
            stage_score=round(stage_score, 3),
            geography_score=round(geography_score, 3),
            check_size_score=round(check_size_score, 3),
            embedding_score=round(embedding_score, 3),
            description=description,
            match_reasons=reasons
        )
    
    def _score_sector(self, founder: Dict, investor: Dict) -> float:
        founder_sector = founder.get("industry", "")
        investor_sectors = investor.get("preferred_sectors", [])
        if founder_sector in investor_sectors:
            return 1.0
        for inv_sector in investor_sectors:
            if founder_sector in self.sector_similarity:
                if inv_sector in self.sector_similarity[founder_sector]:
                    return self.sector_similarity[founder_sector][inv_sector]
        return 0.2
    
    def _score_stage(self, founder: Dict, investor: Dict) -> float:
        founder_stage = founder.get("funding_stage", "")
        investor_stages = investor.get("preferred_stages", [])
        best = 0.0
        for inv_stage in investor_stages:
            if inv_stage in self.stage_compatibility.get(founder_stage, {}):
                best = max(best, self.stage_compatibility[founder_stage][inv_stage])
        return best
    
    def _score_geography(self, founder: Dict, investor: Dict) -> float:
        geography = investor.get("geography", "Global")
        focus_geos = investor.get("focus_geographies", [])
        founder_loc = founder.get("location", "").lower()
        if geography == "Global":
            return 0.9
        for geo in focus_geos:
            if geo.lower() in founder_loc:
                return 1.0
        regions = {
            "US": ["san francisco", "new york", "austin", "boston", "ca", "tx", "ma", "ny"],
            "Europe": ["london", "stockholm", "dublin", "berlin", "uk", "sweden", "ireland"],
            "India": ["mumbai", "bangalore", "delhi", "india"],
        }
        for focus_geo in focus_geos:
            if focus_geo in regions:
                for city in regions[focus_geo]:
                    if city in founder_loc:
                        return 0.85
        return 0.3
    
    def _score_check_size(self, founder: Dict, investor: Dict) -> float:
        ask = founder.get("ask_amount", 0)
        min_c = investor.get("check_size_min", 0)
        max_c = investor.get("check_size_max", float('inf'))
        if min_c <= ask <= max_c:
            return 1.0
        if ask < min_c and min_c / max(ask, 1) <= 2:
            return 0.6
        if ask > max_c and ask / max(max_c, 1) <= 1.5:
            return 0.5
        return 0.2
    
    def _generate_reasons(self, founder, investor, sector, stage, embedding):
        reasons = []
        if sector >= 0.8:
            reasons.append(f"Strong sector alignment: {founder.get('industry')} → {investor.get('name')}")
        if stage >= 0.8:
            reasons.append(f"Stage fit: {founder.get('funding_stage')} aligns with investment strategy")
        if embedding >= 0.7:
            reasons.append(f"High semantic similarity ({embedding:.0%}): profile and thesis strongly align")
        elif embedding >= 0.5:
            reasons.append(f"Moderate semantic similarity ({embedding:.0%}): some alignment detected")
        if founder.get("why_paires"):
            reasons.append(f"Founder seeking: {founder.get('why_paires')[:80]}")
        return reasons[:4]
    
    def _generate_description(self, founder, investor, overall, embedding):
        if overall >= 0.8:
            return f"Exceptional match: {founder.get('company')} and {investor.get('name')} (semantic: {embedding:.0%})"
        elif overall >= 0.6:
            return f"Strong match: {founder.get('company')} ({founder.get('industry')}) with {investor.get('name')}"
        elif overall >= 0.4:
            return f"Moderate match: {founder.get('company')} aligns with some criteria of {investor.get('name')}"
        return f"Low match: {founder.get('company')} does not closely align with {investor.get('name')}'s thesis"
    
    def find_best_matches(self, founder: Dict, investors: List[Dict], top_k: int = 5) -> List[MatchResult]:
        matches = [self.compute_match(founder, inv) for inv in investors]
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        for m in matches[:top_k]:
            self.db.save_match({
                "founder_id": m.founder_id, "investor_id": m.investor_id,
                "overall_score": m.overall_score, "sector_score": m.sector_score,
                "stage_score": m.stage_score, "geography_score": m.geography_score,
                "check_size_score": m.check_size_score, "embedding_score": m.embedding_score,
                "description": m.description, "match_reasons": m.match_reasons
            })
        return matches[:top_k]
    
    def find_best_matches_for_investor(self, investor: Dict, founders: List[Dict], top_k: int = 5) -> List[MatchResult]:
        matches = [self.compute_match(f, investor) for f in founders]
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return matches[:top_k]
    
    def record_feedback(self, founder_id: str, investor_id: str, meeting_booked: bool,
                        notes: str = None, predicted_score: float = None):
        self.db.save_feedback(founder_id, investor_id, meeting_booked, notes, predicted_score)
    
    def get_evals(self) -> Dict[str, Any]:
        total_matches = self.db.get_match_count()
        total_feedback = self.db.get_feedback_count()
        booked = self.db.get_meetings_booked()
        dist = self.db.get_score_distribution()
        
        return {
            "total_matches_generated": total_matches,
            "matches_with_feedback": total_feedback,
            "meetings_booked": booked,
            "conversion_rate": round(booked / total_feedback, 3) if total_feedback > 0 else 0,
            "score_distribution": dist,
            "feedback_recent": self.db.get_recent_feedback(5)
        }
