"""
Paires Matcher - Agent Layer
Generates personalized outreach messages for matched founder-investor pairs
"""

from typing import Dict, Any, Optional


class MatchAgent:
    """Agent that generates personalized outreach for matched pairs"""
    
    async def generate_outreach(
        self,
        founder: Dict[str, Any],
        investor: Dict[str, Any],
        match_score: float
    ) -> Dict[str, Any]:
        """Generate a personalized outreach message for this match"""
        
        template = self._pick_template(investor.get("type", "VC"))
        message = template(
            founder_name=founder.get("name", ""),
            company=founder.get("company", ""),
            headline=founder.get("headline", ""),
            description=founder.get("description", "")[:200],
            investor_name=investor.get("name", ""),
            investor_partner="Partner",
            key_metrics=founder.get("key_metrics", [])[:2],
            technical_stack=founder.get("technical_stack", [])[:3],
            match_reason=self._match_reason(founder, investor, match_score),
            ask_amount=founder.get("ask_amount", 0)
        )
        
        return {
            "subject": self._generate_subject(founder, investor, match_score),
            "body": message,
            "tone": "professional_warm" if match_score >= 0.7 else "professional",
            "match_score": match_score,
            "key_selling_points": self._key_selling_points(founder, investor)
        }
    
    def _generate_subject(self, founder: Dict, investor: Dict, score: float) -> str:
        """Generate email subject line"""
        company = founder.get("company", "")
        industry = founder.get("industry", "")
        
        subjects = [
            f"Introducing {company} — {industry} opportunity in {founder.get('funding_stage', '')}",
            f"{company}: {founder.get('headline', '')}",
            f"Portfolio fit? {company} ({industry}, {founder.get('funding_stage', '')})",
            f"New opportunity: {company} — {founder.get('description', '')[:60]}..."
        ]
        
        return subjects[int(score * len(subjects)) % len(subjects)]
    
    def _pick_template(self, investor_type: str):
        """Pick outreach template based on investor type"""
        return self._general_vc_template
    
    def _general_vc_template(self, **kwargs) -> str:
        return f"""Hi {{investment_partner}},

I'm writing to introduce you to {kwargs.get('company')}, a company I believe aligns well with {kwargs.get('investor_name')}'s investment focus.

About {kwargs.get('company')}:
{kwargs.get('headline')}
{kwargs.get('description')}

Key traction metrics:
• {' | '.join(kwargs.get('key_metrics', ['Strong growth']))}

Technical foundation: {' · '.join(kwargs.get('technical_stack', ['Modern stack']))}

Why this match matters:
{kwargs.get('match_reason')}

They are currently raising {kwargs.get('ask_amount', 'their round')} and looking for a partner who brings more than just capital.

Would you be open to an introduction?

Best,
Paires Discovery Team"""

    def _match_reason(self, founder: Dict, investor: Dict, score: float) -> str:
        """Generate a match-specific reason"""
        industry = founder.get("industry", "")
        stage = founder.get("funding_stage", "")
        investor_name = investor.get("name", "")
        
        if score >= 0.8:
            return f"{founder.get('company')} operates at the intersection of {industry} and {', '.join(investor.get('preferred_sectors', ['technology']))} — directly in {investor_name}'s sweet spot at exactly the right stage ({stage})."
        elif score >= 0.6:
            return f"Strong thematic alignment with {investor_name}'s portfolio strategy in {industry}. The {stage} stage and business model fit your investment criteria well."
        else:
            return f"An interesting company in the {industry} space worth a brief look given {investor_name}'s sector focus."
    
    def _key_selling_points(self, founder: Dict, investor: Dict) -> list:
        """Extract key selling points for this match"""
        points = []
        
        if founder.get("arr", 0) > 1000000:
            points.append(f"${founder['arr']//1000000}M+ ARR with {founder.get('gross_margin', 'strong')}% gross margins")
        
        if founder.get("previous_investors"):
            points.append(f"Backed by {', '.join(founder['previous_investors'][:2])}")
        
        points.append(founder.get("headline", ""))
        
        return points[:3]
