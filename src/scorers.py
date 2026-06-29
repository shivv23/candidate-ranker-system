#!/usr/bin/env python3
"""All scoring functions."""
import math
from src.config import (
    TITLE_SCORES, TITLE_DEFAULT, TARGET_YOE_MIN, TARGET_YOE_MAX, TARGET_YOE_IDEAL,
    JD_SKILLS_ALL, JD_SKILLS_AI, JD_SKILLS_RETRIEVAL, JD_SKILLS_RANKING, JD_SKILLS_ENGINEERING,
    PRODUCT_COMPANIES, CONSULTING_COMPANIES,
    PUNE_NOIDA, OTHER_INDIAN_CITIES, SIGNAL_WEIGHTS,
    RELEVANT_FIELDS, NON_TECH_TITLES,
    HONEYPOT_EXPERT_SKILL_ZERO_YEARS, HONEYPOT_MAX_AI_SKILLS_NON_TECH,
    HONEYPOT_MAX_SKILL_COUNT, NLP_IR_SKILLS, CV_SPEECH_SKILLS,
    W_SEMANTIC, W_TITLE, W_SKILLS, W_EXPERIENCE, W_COMPANY, W_SIGNALS,
    W_LOCATION, W_EDUCATION, W_HONEYPOT_MODIFIER, FAKE_COMPANIES,
)


def _count_core_ml_skills(names):
    """Count core ML skills across AI/retrieval/ranking categories."""
    ai = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_AI))
    ret = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RETRIEVAL))
    rank = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RANKING))
    return ai + ret + rank


def score_title(features) -> float:
    t = features.current_title.lower().strip()
    if not t:
        return TITLE_DEFAULT
    if t in TITLE_SCORES:
        return TITLE_SCORES[t]
    for key, score in sorted(TITLE_SCORES.items(), key=lambda x: -len(x[0])):
        if key in t or t in key:
            return score
    if features.is_non_tech_title:
        return 0.10
    return TITLE_DEFAULT


def score_skills(features) -> float:
    names = [s.lower().strip() for s in features.skill_names]
    if not names:
        return 0.0

    ai = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_AI))
    retrieval = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RETRIEVAL))
    ranking = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RANKING))
    eng = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_ENGINEERING))

    base = 0.0
    base += min(ai, 5) / 5 * 0.30
    base += min(retrieval, 5) / 5 * 0.25
    base += min(ranking, 3) / 3 * 0.20
    base += min(eng, 5) / 5 * 0.25

    total_jd = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_ALL))
    if total_jd >= 5:
        base = min(base + 0.10, 1.0)

    if features.is_non_tech_title and total_jd >= 8:
        base *= 0.5

    return min(base, 1.0)


def score_experience(features) -> float:
    yoe = features.years_of_experience
    if yoe <= 0:
        return 0.0
    if TARGET_YOE_MIN <= yoe <= TARGET_YOE_MAX:
        return 1.0 - 0.1 * abs(yoe - TARGET_YOE_IDEAL)
    if yoe < TARGET_YOE_MIN:
        return max(0.2, yoe / TARGET_YOE_MIN * 0.7)
    over = yoe - TARGET_YOE_MAX
    return max(0.1, 0.8 - over * 0.08)


def score_company(features) -> float:
    cl = features.current_company.lower()
    if any(pc in cl for pc in PRODUCT_COMPANIES):
        return 1.0
    if any(cc in cl for cc in CONSULTING_COMPANIES):
        return 0.40
    return 0.60


def score_signals(features) -> float:
    scores = {}
    scores["recruiter_response_rate"] = min(features.recruiter_response_rate * 1.5, 1.0)
    scores["last_active_days_ago"] = max(0.0, 1.0 - features.days_since_active / 365)
    scores["open_to_work_flag"] = 1.0 if features.open_to_work else 0.3
    scores["profile_views_received_30d"] = min(features.profile_views_30d / 50, 1.0)
    scores["saved_by_recruiters_30d"] = min(features.saved_by_recruiters_30d / 20, 1.0)
    scores["interview_completion_rate"] = features.interview_completion_rate if features.interview_completion_rate >= 0 else 0.5
    scores["offer_acceptance_rate"] = features.offer_acceptance_rate if features.offer_acceptance_rate >= 0 else 0.5
    scores["github_activity_score"] = max(0, features.github_activity_score) / 50 if features.github_activity_score > 0 else 0.3
    scores["connection_count"] = min(features.connection_count / 500, 1.0)
    scores["profile_completeness"] = features.profile_completeness / 100

    total = sum(scores.get(k, 0) * w for k, w in SIGNAL_WEIGHTS.items())
    return min(total, 1.0)


def score_location(features) -> float:
    loc_lower = features.location.lower()
    if any(pn in loc_lower for pn in PUNE_NOIDA):
        return 1.0
    willing = getattr(features, 'willing_to_relocate', False)
    if willing:
        return 1.0
    if any(oc in loc_lower for oc in OTHER_INDIAN_CITIES):
        return 0.85
    if features.country.lower() in ("india", ""):
        return 0.70
    return 0.40


def score_education(features) -> float:
    if not features.education:
        return 0.30
    for edu in features.education:
        if isinstance(edu, dict):
            field = (edu.get("field_of_study") or "").lower()
            if any(rf in field for rf in RELEVANT_FIELDS):
                return 1.0
    return 0.50


def detect_honeypot_penalty(features) -> float:
    penalty = 0.0
    flags = []

    names = [s.lower().strip() for s in features.skill_names]

    # 1. Keyword stuffing: non-tech title with too many skills
    if features.is_non_tech_title and features.skill_count >= HONEYPOT_MAX_SKILL_COUNT:
        penalty += 0.30
        flags.append("stuffing")

    # 2. Non-tech title with heavy AI skills
    if features.is_non_tech_title:
        ai_count = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_AI))
        if ai_count >= HONEYPOT_MAX_AI_SKILLS_NON_TECH:
            penalty += 0.30
            flags.append("ai_stuffing")

    # 3. Too many skills overall (impossible to be expert in all)
    if features.skill_count >= 22:
        penalty += 0.20
        flags.append("many_skills")

    # 4. Low response rate + high profile views (dead profile)
    if features.recruiter_response_rate < 0.10 and features.profile_views_30d > 30:
        penalty += 0.15
        flags.append("ghost")

    # 5. Inactive + low response + NOT open to work
    if features.days_since_active > 200 and not features.open_to_work:
        penalty += 0.15
        flags.append("inactive")

    # 6. Expert-level skills with zero years of experience
    # NOTE: ALL skills in the dataset have years_of_experience=None, making this
    #       flag structurally meaningless. Disabled: no penalty applied.
    # expert_zero = sum(1 for s in features.skills if isinstance(s, dict) and
    #     (s.get('proficiency') or '').lower() in ('expert', 'advanced') and
    #     (s.get('years_of_experience') or 0) == 0)
    # if expert_zero >= HONEYPOT_EXPERT_SKILL_ZERO_YEARS:
    #     flags.append("expert_zero_yoE")
    pass

    # 7. CV/speech skills without NLP/IR (JD explicitly disqualifies)
    if features.has_cv_speech_skills and not features.has_nlp_ir_skills:
        penalty += 0.20
        flags.append("cv_speech_no_nlp")

    # 8. All consulting background (JD explicitly avoids)
    if features.all_consulting:
        penalty += 0.25
        flags.append("all_consulting")

    # 9. Pure research without any product/startup experience
    if features.all_research and not features.has_product_or_startup:
        penalty += 0.20
        flags.append("pure_research")

    # 10. Fake/placeholder company name (synthetic profile)
    cl = features.current_company.lower()
    if any(fc in cl for fc in FAKE_COMPANIES):
        penalty += 0.50
        flags.append("fake_company")

    # 11. Non-tech title with keyword stuffing at moderate AI counts
    if features.is_non_tech_title:
        ais_n11 = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_AI))
        rets_n11 = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RETRIEVAL))
        ranks_n11 = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RANKING))
        total_jd_n11 = ais_n11 + rets_n11 + ranks_n11
        if total_jd_n11 >= 6 and features.skill_count >= 10:
            penalty += 0.30
            flags.append("non_tech_keyword_stuffing")

    # 12. Non-AI/ML title (tech but non-ML) with too few AI/ML-relevant skills
    title_lower = features.current_title.lower()
    is_ai_title_check = any(t in title_lower for t in
        ['ml engineer', 'machine learning', 'ai specialist', 'ai engineer',
         'ai research', 'ai architect', 'artificial intelligence',
         'deep learning', 'nlp', 'llm', 'data scientist',
         'research engineer', 'computer vision',
         'recommendation', 'search engineer', 'data engineer',
         'applied scientist'])
    if not features.is_non_tech_title and not is_ai_title_check:
        ai_count_f11 = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_AI))
        ret_count_f11 = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RETRIEVAL))
        rank_count_f11 = sum(1 for n in names if any(jd in n for jd in JD_SKILLS_RANKING))
        core_ml_total = ai_count_f11 + ret_count_f11 + rank_count_f11
        if core_ml_total == 0:
            penalty += 0.50
            flags.append("tech_non_ml_zero_ml_skills")
        elif core_ml_total <= 2:
            penalty += 0.35
            flags.append("tech_non_ml_minimal_ml_skills")

    return min(penalty, 0.80), flags


def compute_final_score(features, semantic_score, title_score, skills_score,
                        exp_score, company_score, signal_score, loc_score,
                        edu_score, hon_penalty) -> float:
    # Skill relevance factor: tiered semantic de-weighting for low-skill candidates
    names_fs = [s.lower().strip() for s in features.skill_names]
    core_ml_count = _count_core_ml_skills(names_fs)
    if core_ml_count == 0:
        skill_relevance = 0.50
    elif core_ml_count == 1:
        skill_relevance = 0.65
    elif core_ml_count == 2:
        skill_relevance = 0.80
    else:
        skill_relevance = 1.0
    semantic_effective = semantic_score * skill_relevance

    base = (
        W_SEMANTIC * semantic_effective +
        W_TITLE * title_score +
        W_SKILLS * skills_score +
        W_EXPERIENCE * exp_score +
        W_COMPANY * company_score +
        W_SIGNALS * signal_score +
        W_LOCATION * loc_score +
        W_EDUCATION * edu_score
    )

    if hon_penalty > 0:
        base *= (1.0 - 0.8 * hon_penalty)

    if getattr(features, 'has_notice_period', True) and features.notice_period_days <= 30:
        base *= 1.05
    elif getattr(features, 'has_notice_period', True) and features.notice_period_days > 90:
        base *= 0.85
    elif getattr(features, 'has_notice_period', True) and features.notice_period_days > 60:
        base *= 0.93

    # Spread scores to widen distribution and reduce ties
    base = 1.0 - 1.5 * (1.0 - base)

    return max(0.0001, min(base, 1.0))
