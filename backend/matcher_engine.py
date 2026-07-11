"""
Paires Matcher - Core Matching Engine
Embedding-based scoring, ranking, feedback loops
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import math
import json


@dataclass
class MatchResult:
    founder_id: str
    investor_id: str
    overall_score: float
    sector_score: float
    stage_score: float
    geography_score: float
    check_size_score: float
    description: str
    match_reasons: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    feedback: Optional[str] = None
    meeting_booked: Optional[bool] = None


class MatcherEngine:
    """
    Core matching engine that scores founder-investor compatibility
    using multi-factor weighted scoring
    """
    
    # Weights for each scoring dimension
    WEIGHTS = {
        "sector": 0.35,
        "stage": 0.20,
        "geography": 0.15,
        "check_size": 0.15,
        "description_embedding": 0.15
    }
    
    def __init__(self):
        self.match_history: List[MatchResult] = []
        self.feedback_log: List[Dict] = []
        
        # Sector similarity matrix (how related industries are)
        self.sector_similarity = {
            "Enterprise AI": {"HealthTech": 0.6, "Fintech": 0.5, "Deep Tech": 0.7, "Enterprise SaaS": 0.8, "Robotics": 0.5, "Climate Tech": 0.3, "EdTech": 0.4, "Security": 0.7},
            "HealthTech": {"Enterprise AI": 0.6, "Fintech": 0.2, "BioTech": 0.9, "Life Sciences": 0.9, "Enterprise SaaS": 0.4, "Deep Tech": 0.5, "Climate Tech": 0.2},
            "Fintech": {"Enterprise AI": 0.5, "Enterprise SaaS": 0.6, "Deep Tech": 0.3, "Climate Tech": 0.2, "EdTech": 0.3, "Security": 0.5, "Payments": 0.9, "Lending": 0.9},
            "Climate Tech": {"Clean Energy": 0.9, "Sustainable Materials": 0.9, "Agriculture": 0.8, "Enterprise AI": 0.3, "Deep Tech": 0.4, "Manufacturing": 0.5},
            "Deep Tech": {"Enterprise AI": 0.7, "Defense": 0.8, "Space": 0.8, "Robotics": 0.8, "Quantum Communication": 0.9, "HealthTech": 0.4},
            "Enterprise SaaS": {"Enterprise AI": 0.8, "Fintech": 0.6, "Security": 0.8, "HealthTech": 0.4, "EdTech": 0.5, "Climate Tech": 0.3},
        }
        
        # Stage compatibility matrix
        self.stage_compatibility = {
            "Pre-Seed": {"Pre-Seed": 1.0, "Seed": 0.8, "Series A": 0.4, "Series B": 0.1, "Growth": 0.0},
            "Seed": {"Pre-Seed": 0.7, "Seed": 1.0, "Series A": 0.8, "Series B": 0.4, "Growth": 0.1},
            "Series A": {"Pre-Seed": 0.2, "Seed": 0.6, "Series A": 1.0, "Series B": 0.8, "Growth": 0.4},
            "Series B": {"Pre-Seed": 0.0, "Seed": 0.2, "Series A": 0.7, "Series B": 1.0, "Growth": 0.8},
            "Growth": {"Pre-Seed": 0.0, "Seed": 0.1, "Series A": 0.3, "Series B": 0.7, "Growth": 1.0},
        }
    
    def compute_match(self, founder: Dict, investor: Dict) -> MatchResult:
        """Compute match score between a founder and investor"""
        
        sector_score = self._score_sector(founder, investor)
        stage_score = self._score_stage(founder, investor)
        geography_score = self._score_geography(founder, investor)
        check_size_score = self._score_check_size(founder, investor)
        description_score = self._score_description_similarity(founder, investor)
        
        overall = (
            sector_score * self.WEIGHTS["sector"] +
            stage_score * self.WEIGHTS["stage"] +
            geography_score * self.WEIGHTS["geography"] +
            check_size_score * self.WEIGHTS["check_size"] +
            description_score * self.WEIGHTS["description_embedding"]
        )
        
        reasons = self._generate_match_reasons(founder, investor, sector_score, stage_score, geography_score, check_size_score)
        description = self._generate_match_description(founder, investor, overall, reasons)
        
        return MatchResult(
            founder_id=founder["id"],
            investor_id=investor["id"],
            overall_score=round(overall, 3),
            sector_score=round(sector_score, 3),
            stage_score=round(stage_score, 3),
            geography_score=round(geography_score, 3),
            check_size_score=round(check_size_score, 3),
            description=description,
            match_reasons=reasons
        )
    
    def _score_sector(self, founder: Dict, investor: Dict) -> float:
        """Score sector compatibility"""
        founder_sector = founder.get("industry", "")
        investor_sectors = investor.get("preferred_sectors", [])
        
        # Direct match
        if founder_sector in investor_sectors:
            return 1.0
        
        # Check sub-industry
        founder_sub = founder.get("sub_industry", "")
        for inv_sector in investor_sectors:
            if founder_sub in investor_sectors:
                return 0.95
            if founder_sector in self.sector_similarity:
                if inv_sector in self.sector_similarity[founder_sector]:
                    return self.sector_similarity[founder_sector][inv_sector]
        
        # Check via investor's recent investments
        recent = [r.lower() for r in investor.get("recent_investments", [])]
        founder_industry = founder_sector.lower()
        founder_sub = founder.get("sub_industry", "").lower()
        
        for r in recent:
            if founder_industry in r or founder_sub in r:
                return 0.7
        
        return 0.2
    
    def _score_stage(self, founder: Dict, investor: Dict) -> float:
        """Score stage compatibility"""
        founder_stage = founder.get("funding_stage", "")
        investor_stages = investor.get("preferred_stages", [])
        
        best_match = 0.0
        for inv_stage in investor_stages:
            if inv_stage in self.stage_compatibility.get(founder_stage, {}):
                score = self.stage_compatibility[founder_stage][inv_stage]
                best_match = max(best_match, score)
            elif founder_stage in self.stage_compatibility.get(inv_stage, {}):
                score = self.stage_compatibility[inv_stage][founder_stage]
                best_match = max(best_match, score)
        
        return best_match
    
    def _score_geography(self, founder: Dict, investor: Dict) -> float:
        """Score geography compatibility"""
        founder_loc = founder.get("location", "")
        geography = investor.get("geography", "Global")
        focus_geos = investor.get("focus_geographies", [])
        
        if geography == "Global":
            return 0.9
        
        # Check focus geographies
        for geo in focus_geos:
            geo_lower = geo.lower()
            if geo_lower in founder_loc.lower():
                return 1.0
        
        # Broader region check
        regions = {
            "US": ["san francisco", "new york", "austin", "boston", "silicon valley", "ca", "tx", "ma", "ny"],
            "Europe": ["london", "stockholm", "dublin", "berlin", "paris", "uk", "sweden", "ireland", "germany", "france"],
            "India": ["mumbai", "bangalore", "delhi", "india"],
            "Southeast Asia": ["vietnam", "indonesia", "thailand", "singapore", "malaysia"],
            "Latin America": ["mexico", "brazil", "argentina", "colombia"],
            "Africa": ["lagos", "nairobi", "nigeria", "kenya", "south africa"],
        }
        
        for focus_geo in focus_geos:
            if focus_geo in regions:
                founder_lower = founder_loc.lower()
                for city in regions[focus_geo]:
                    if city in founder_lower:
                        return 0.9
                for country in regions[focus_geo]:
                    if country in founder_lower:
                        return 0.85
        
        return 0.3
    
    def _score_check_size(self, founder: Dict, investor: Dict) -> float:
        """Score check size compatibility"""
        ask = founder.get("ask_amount", 0)
        min_check = investor.get("check_size_min", 0)
        max_check = investor.get("check_size_max", float('inf'))
        
        if min_check <= ask <= max_check:
            return 1.0
        
        # Close to range
        if ask < min_check and min_check / ask <= 2:
            return 0.6
        if ask > max_check and ask / max_check <= 1.5:
            return 0.5
        
        return 0.2
    
    def _score_description_similarity(self, founder: Dict, investor: Dict) -> float:
        """Score semantic similarity between founder description and investor thesis"""
        founder_text = (founder.get("description", "") + " " + 
                       " ".join(founder.get("looking_for", []))).lower()
        thesis = investor.get("investment_thesis", "").lower()
        
        # Simple keyword overlap scoring
        founder_words = set(founder_text.split())
        thesis_words = set(thesis.split())
        
        if not thesis_words:
            return 0.5
        
        overlap = len(founder_words & thesis_words)
        # Normalize by smaller set
        smaller = min(len(founder_words), len(thesis_words))
        if smaller == 0:
            return 0.5
        
        return min(overlap / smaller * 2, 1.0) * 0.7 + 0.3
    
    def _generate_match_reasons(self, founder: Dict, investor: Dict, 
                               sector_score: float, stage_score: float,
                               geo_score: float, check_score: float) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []
        
        if sector_score >= 0.8:
            reasons.append(f"Strong sector alignment: {founder.get('industry')} matches {investor.get('name')}'s focus")
        elif sector_score >= 0.5:
            reasons.append(f"Partial sector match: {founder.get('industry')} overlaps with portfolio focus")
        
        if stage_score >= 0.8:
            reasons.append(f"Stage fit: {founder.get('funding_stage')} stage aligns with investment strategy")
        
        if geo_score >= 0.8:
            reasons.append(f"Geographic match: {founder.get('location')} is within focus region")
        
        if check_score >= 0.8:
            reasons.append(f"Deal size compatible: ${founder.get('ask_amount', 0)//1000000}M ask fits check range")
        
        if founder.get("why_paires"):
            reasons.append(f"Founder seeking: {founder.get('why_paires')[:80]}...")
        
        # Portfolio relevance
        portfolio_h = investor.get("portfolio_highlights", [])
        founder_industry = founder.get("industry", "").lower()
        relevant = [p for p in portfolio_h if any(word in p.lower() for word in founder_industry.split())]
        if relevant:
            reasons.append(f"Relevant portfolio: {', '.join(relevant[:2])}")
        
        return reasons[:4]  # Max 4 reasons
    
    def _generate_match_description(self, founder: Dict, investor: Dict, 
                                   score: float, reasons: List[str]) -> str:
        """Generate a natural language match description"""
        if score >= 0.8:
            return f"Exceptional match between {founder.get('company')} and {investor.get('name')}. {reasons[0] if reasons else ''}"
        elif score >= 0.6:
            return f"Strong match: {founder.get('company')} ({founder.get('industry')}, {founder.get('funding_stage')}) with {investor.get('name')}. Key synergies identified."
        elif score >= 0.4:
            return f"Moderate match: {founder.get('company')} aligns with some of {investor.get('name')}'s criteria. Worth exploring."
        else:
            return f"Low match probability: {founder.get('company')} does not closely align with {investor.get('name')}'s current thesis."
    
    def find_best_matches(self, founder: Dict, investors: List[Dict], top_k: int = 5) -> List[MatchResult]:
        """Find the best investor matches for a founder"""
        matches = [self.compute_match(founder, inv) for inv in investors]
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        
        # Store in history
        self.match_history.extend(matches)
        
        return matches[:top_k]
    
    def find_best_matches_for_investor(self, investor: Dict, founders: List[Dict], top_k: int = 5) -> List[MatchResult]:
        """Find the best founder matches for an investor"""
        matches = [self.compute_match(f, investor) for f in founders]
        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return matches[:top_k]
    
    def record_feedback(self, match: MatchResult, meeting_booked: bool, notes: Optional[str] = None):
        """Record feedback on a match to improve future scoring"""
        match.feedback = notes
        match.meeting_booked = meeting_booked
        
        self.feedback_log.append({
            "founder_id": match.founder_id,
            "investor_id": match.investor_id,
            "predicted_score": match.overall_score,
            "meeting_booked": meeting_booked,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_evals(self) -> Dict[str, Any]:
        """Get evaluation metrics for matching quality"""
        total_matches = len(self.match_history)
        total_feedback = len(self.feedback_log)
        
        if total_feedback == 0:
            return {
                "total_matches_generated": total_matches,
                "matches_with_feedback": 0,
                "conversion_rate": 0,
                "average_predicted_score": self._avg_predicted_score(),
                "score_distribution": self._score_distribution()
            }
        
        booked = sum(1 for f in self.feedback_log if f["meeting_booked"])
        
        return {
            "total_matches_generated": total_matches,
            "matches_with_feedback": total_feedback,
            "meetings_booked": booked,
            "conversion_rate": round(booked / total_feedback, 3),
            "average_predicted_score": self._avg_predicted_score(),
            "score_distribution": self._score_distribution(),
            "feedback_recent": self.feedback_log[-10:]
        }
    
    def _avg_predicted_score(self) -> float:
        if not self.match_history:
            return 0.0
        return round(sum(m.overall_score for m in self.match_history) / len(self.match_history), 3)
    
    def _score_distribution(self) -> Dict[str, int]:
        dist = {"high": 0, "medium": 0, "low": 0}
        for m in self.match_history:
            if m.overall_score >= 0.7:
                dist["high"] += 1
            elif m.overall_score >= 0.4:
                dist["medium"] += 1
            else:
                dist["low"] += 1
        return dist
    
    def get_founder_recommendations(self, founder_id: str) -> Optional[List[MatchResult]]:
        """Get stored matches for a specific founder"""
        return [m for m in self.match_history if m.founder_id == founder_id]
