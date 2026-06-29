#!/usr/bin/env python3
"""Reasoning generator for Stage 4 manual review."""
from src.config import JD_SKILLS_AI, JD_SKILLS_RETRIEVAL, JD_SKILLS_RANKING


def generate_reasoning(features, scores, rank):
    title = features.current_title or "Professional"
    company = features.current_company or "unknown"
    yoe = features.years_of_experience

    # Top strengths
    strengths = []
    if scores["title"] >= 0.8:
        strengths.append(f"{title}")
    if scores["skills"] >= 0.5:
        names = features.skill_names
        matched = []
        for cat_name, cat_list in [("AI/ML", JD_SKILLS_AI), ("retrieval", JD_SKILLS_RETRIEVAL),
                                     ("ranking", JD_SKILLS_RANKING)]:
            m = [n for n in names if any(k in n.lower() for k in cat_list)]
            if m:
                matched.append(f"{cat_name}: {', '.join(m[:3])}")
        if matched:
            strengths.append("; ".join(matched[:2]))
    if features.company_type == "product":
        strengths.append("product company background")
    elif features.company_type == "startup":
        strengths.append("startup experience")
    if features.open_to_work:
        strengths.append("actively looking")

    # Concerns
    concerns = []
    if yoe < 4:
        concerns.append(f"below ideal experience ({yoe:.0f}yr)")
    if yoe > 12:
        concerns.append(f"over seniority ({yoe:.0f}yr)")
    if features.notice_period_days > 60:
        concerns.append(f"{features.notice_period_days}d notice")
    elif features.notice_period_days > 30:
        concerns.append(f"{features.notice_period_days}d notice")
    if features.days_since_active > 90:
        concerns.append(f"inactive {features.days_since_active}d")
    if features.is_non_tech_title:
        concerns.append("title-role mismatch")
    if features.company_type == "consulting":
        concerns.append("consulting background")

    # Build reasoning
    exp_str = f"{yoe}yr at {company}" if company else f"{yoe}yr experience"
    strength_str = "; ".join(strengths[:3]) if strengths else "relevant background"
    concern_str = f"; {'. '.join(concerns[:2])}" if concerns else ""

    if rank <= 10:
        return f"{title} with {exp_str}; {strength_str}{concern_str}.".strip()
    elif rank <= 50:
        return f"{title}, {exp_str}; {strength_str}{concern_str}.".strip()
    else:
        basic = f"{title} ({yoe}yr)"
        con = f" | {concerns[0]}" if concerns else ""
        return f"{basic}{con}."
