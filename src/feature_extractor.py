#!/usr/bin/env python3
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from src.config import PRODUCT_COMPANIES, CONSULTING_COMPANIES, RESEARCH_LABS, NON_TECH_TITLES, NLP_IR_SKILLS, CV_SPEECH_SKILLS, JD_SKILLS_AI, JD_SKILLS_RETRIEVAL

NOW = date(2026, 6, 6)


def _classify_company(company_name: str) -> str:
    cl = company_name.lower()
    if any(pc in cl for pc in PRODUCT_COMPANIES):
        return "product"
    if any(cc in cl for cc in CONSULTING_COMPANIES):
        return "consulting"
    if any(rl in cl for rl in RESEARCH_LABS):
        return "research"
    return "startup"


@dataclass
class CandidateFeatures:
    candidate_id: str
    headline: str = ""
    summary: str = ""
    current_title: str = ""
    current_company: str = ""
    years_of_experience: float = 0.0
    location: str = ""
    country: str = ""
    skills: list = field(default_factory=list)
    skill_names: list = field(default_factory=list)
    skill_count: int = 0
    education: list = field(default_factory=list)
    num_jobs: int = 0
    company_type: str = "other"
    is_non_tech_title: bool = False
    profile_text: str = ""

    # Career history analysis
    all_consulting: bool = False
    all_research: bool = False
    has_product_or_startup: bool = False

    # Skill domain detection
    has_nlp_ir_skills: bool = False
    has_cv_speech_skills: bool = False
    has_any_jd_ai_or_retrieval_skill: bool = False

    # Behavioral signals (raw)
    recruiter_response_rate: float = 0.0
    last_active_date: Optional[str] = None
    days_since_active: int = 999
    open_to_work: bool = False
    profile_views_30d: int = 0
    saved_by_recruiters_30d: int = 0
    interview_completion_rate: float = 0.0
    offer_acceptance_rate: float = 0.0
    github_activity_score: float = 0.0
    connection_count: int = 0
    notice_period_days: int = 90
    has_notice_period: bool = False
    skill_assessment_scores: dict = field(default_factory=dict)
    profile_completeness: float = 50.0
    applications_submitted_30d: int = 0
    willing_to_relocate: bool = False


def extract_features(candidate: dict) -> CandidateFeatures:
    cid = candidate.get("candidate_id", "?")
    prof = candidate.get("profile") or {}
    sig = candidate.get("redrob_signals") or {}
    ch = candidate.get("career_history") or []
    ed = candidate.get("education") or []
    skills_raw = candidate.get("skills") or []

    skills_list = []
    skill_names = []
    for s in skills_raw:
        if isinstance(s, dict):
            sn = s.get("name", "")
            skills_list.append(s)
            if sn:
                skill_names.append(sn)
        elif isinstance(s, str):
            skill_names.append(s)

    title = (prof.get("current_title") or "").strip()
    company = (prof.get("current_company") or "").strip()
    headline = (prof.get("headline") or "").strip()
    summary = (prof.get("summary") or "").strip()
    location = (prof.get("location") or "").strip()
    country = (prof.get("country") or "").strip()
    yoe = float(prof.get("years_of_experience") or 0)

    is_non_tech = any(nt in title.lower() for nt in NON_TECH_TITLES)
    ctype = _classify_company(company)

    # Career history analysis
    num_product = 0
    num_consulting = 0
    num_research = 0
    num_startup = 0
    for job in ch:
        job_company = (job.get("company") or "").strip()
        jt = _classify_company(job_company)
        if jt == "product":
            num_product += 1
        elif jt == "consulting":
            num_consulting += 1
        elif jt == "research":
            num_research += 1
        else:
            num_startup += 1
    has_prod_or_startup = (num_product + num_startup) > 0
    all_consult = num_consulting > 0 and (num_product + num_startup + num_research) == 0
    all_research_only = num_research > 0 and (num_product + num_startup + num_consulting) == 0

    # Skill domain detection
    names_lower = [s.lower().strip() for s in skill_names]
    has_nlp = any(any(kw in n for kw in NLP_IR_SKILLS) for n in names_lower)
    has_cv = any(any(kw in n for kw in CV_SPEECH_SKILLS) for n in names_lower)
    has_jd_ai = any(any(jd in n for jd in JD_SKILLS_AI) for n in names_lower)
    has_jd_ret = any(any(jd in n for jd in JD_SKILLS_RETRIEVAL) for n in names_lower)
    has_jd_ai_or_ret = has_jd_ai or has_jd_ret

    # Profile text for embedding (enriched with career history and education)
    career_parts = []
    for job in ch[:3]:
        jt = job.get("title", "").strip()
        jc = job.get("company", "").strip()
        jd = job.get("description", "").strip()[:200]
        if jt and jc:
            part = f"{jt} at {jc}"
            if jd:
                part += f": {jd}"
            career_parts.append(part)
    career_str = " | ".join(career_parts)

    edu_parts = []
    for e in ed[:2]:
        deg = e.get("degree", "").strip()
        field = e.get("field_of_study", "").strip()
        inst = e.get("institution", "").strip()
        if deg or field:
            ep = f"{deg} in {field}" if field else deg
            if inst:
                ep += f" from {inst}"
            edu_parts.append(ep)
    edu_str = " | ".join(edu_parts)

    header_parts = [p for p in [headline, summary] if p]
    header_str = " ".join(header_parts)
    profile_text = f"{header_str} {title} at {company}. Skills: {', '.join(skill_names)}." if header_str else f"{title} at {company}. Skills: {', '.join(skill_names)}."
    if career_str:
        profile_text += f" Experience: {career_str}."
    if edu_str:
        profile_text += f" Education: {edu_str}."

    # Signals
    last_active = sig.get("last_active_date") or None
    days_active = 999
    if last_active:
        try:
            lad = datetime.strptime(last_active, "%Y-%m-%d").date()
            days_active = (NOW - lad).days
        except (ValueError, TypeError):
            days_active = 999

    raw_notice = sig.get("notice_period_days")
    has_notice = raw_notice is not None

    return CandidateFeatures(
        candidate_id=cid,
        headline=headline,
        summary=summary,
        current_title=title,
        current_company=company,
        years_of_experience=yoe,
        location=location,
        country=country,
        skills=skills_list,
        skill_names=skill_names,
        skill_count=len(skill_names),
        education=ed,
        num_jobs=len(ch),
        company_type=ctype,
        is_non_tech_title=is_non_tech,
        profile_text=profile_text,
        all_consulting=all_consult,
        all_research=all_research_only,
        has_product_or_startup=has_prod_or_startup,
        has_nlp_ir_skills=has_nlp,
        has_cv_speech_skills=has_cv,
        has_any_jd_ai_or_retrieval_skill=has_jd_ai_or_ret,
        recruiter_response_rate=float(sig.get("recruiter_response_rate") or 0),
        last_active_date=last_active,
        days_since_active=days_active,
        open_to_work=bool(sig.get("open_to_work_flag") or False),
        profile_views_30d=int(sig.get("profile_views_received_30d") or 0),
        saved_by_recruiters_30d=int(sig.get("saved_by_recruiters_30d") or 0),
        interview_completion_rate=float(sig.get("interview_completion_rate") or 0),
        offer_acceptance_rate=float(sig.get("offer_acceptance_rate") or 0),
        github_activity_score=float(sig.get("github_activity_score") or 0),
        connection_count=int(sig.get("connection_count") or 0),
        notice_period_days=int(raw_notice or 90),
        has_notice_period=has_notice,
        skill_assessment_scores=sig.get("skill_assessment_scores") or {},
        profile_completeness=float(sig.get("profile_completeness_score") or 50),
        applications_submitted_30d=int(sig.get("applications_submitted_30d") or 0),
        willing_to_relocate=bool(sig.get("willing_to_relocate") or False),
    )
