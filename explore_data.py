#!/usr/bin/env python3
"""
Deep data exploration — understand the candidate pool before building.
Analyses: skills, titles, companies, experience, signals, honeypot patterns.
"""
import json, sys, os
from collections import Counter, defaultdict
from pathlib import Path

DATA_PATH = "data/raw/candidates.jsonl"
JD_PATH = "data/raw/job_description.docx"

os.makedirs("data/exploration", exist_ok=True)

# --- JD Parsing ---
from docx import Document
doc = Document(JD_PATH)
jd_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
with open("data/raw/job_description.md", "w", encoding="utf-8") as f:
    f.write(jd_text)
print("JD saved to data/raw/job_description.md")

# --- Load candidates ---
candidates = []
with open(DATA_PATH) as f:
    for i, line in enumerate(f):
        if line.strip():
            candidates.append(json.loads(line))
print(f"Loaded {len(candidates)} candidates")

# --- High-level stats ---
fields_with = defaultdict(int)
field_counts = Counter()
title_counts = Counter()
company_counts = Counter()
skill_counts = Counter()
edu_counts = Counter()
location_counts = Counter()
signal_dists = defaultdict(list)
yoe_list = []
notice_list = []
response_rates = []
recency_days = []
profile_views = []
saved_count = []
assessment_scores = []

honeypot_candidates = []
high_skill_count = 0

for c in candidates:
    cid = c.get("candidate_id", "?")
    prof = c.get("profile") or {}
    sig = c.get("redrob_signals") or {}
    
    # Track top-level fields
    for f in ["candidate_id", "profile", "career_history", "education", "skills", "redrob_signals"]:
        if f in c and c[f] is not None:
            fields_with[f] += 1
    
    # Profile fields
    yoe = prof.get("years_of_experience") or 0
    yoe_list.append(yoe)
    
    title = prof.get("current_title", "UNKNOWN") or "UNKNOWN"
    title_counts[title] += 1
    
    company = prof.get("current_company", "UNKNOWN") or "UNKNOWN"
    company_counts[company] += 1
    
    loc = prof.get("location", "") or ""
    location_counts[loc] += 1
    
    headline = prof.get("headline", "") or ""
    summary = prof.get("summary", "") or ""
    
    # Skills (list of dicts)
    skills_raw = c.get("skills") or []
    skill_names = []
    for s in skills_raw:
        if isinstance(s, str):
            skill_names.append(s)
        elif isinstance(s, dict):
            skill_names.append(s.get("name", "") or "")
    skill_counts.update(n.lower().strip() for n in skill_names if n and n.strip())
    high_skill_count = max(high_skill_count, len(skill_names))
    
    # Education
    edu = c.get("education") or []
    for e in edu:
        if isinstance(e, dict):
            deg = e.get("degree", "")
            if deg:
                edu_counts[deg] += 1
            subj = e.get("field_of_study", "")
            if subj:
                edu_counts[subj] += 1
    
    # Signals
    for k in ["response_rate", "days_since_last_active", "profile_views_last_30d",
              "times_saved_by_recruiters", "skill_assessments_completed",
              "is_open_to_work", "notice_period_days", "availability_start_date",
              "has_completed_interview_process", "profile_completeness_score"]:
        if k in sig and sig[k] is not None:
            signal_dists[k].append(sig[k])
    
    response_rates.append(sig.get("response_rate", 0) or 0)
    recency_days.append(sig.get("days_since_last_active", 999) or 999)
    notice_list.append(sig.get("notice_period_days", 0) or 0)

# --- Print Reports ---
print(f"\n{'='*60}")
print(f"FIELD COVERAGE (out of {len(candidates)})")
print(f"{'='*60}")
for f, c in sorted(fields_with.items(), key=lambda x: -x[1]):
    print(f"  {f}: {c}/{len(candidates)} ({c/len(candidates)*100:.1f}%)")

print(f"\n{'='*60}")
print(f"TOP 20 TITLES")
print(f"{'='*60}")
for title, count in title_counts.most_common(20):
    print(f"  {title}: {count}")

print(f"\n{'='*60}")
print(f"TOP 20 COMPANIES")
print(f"{'='*60}")
for comp, count in company_counts.most_common(20):
    if comp != "UNKNOWN":
        print(f"  {comp}: {count}")

print(f"\n{'='*60}")
print(f"TOP 40 SKILLS")
print(f"{'='*60}")
for skill, count in skill_counts.most_common(40):
    print(f"  {skill}: {count}")

print(f"\n{'='*60}")
print(f"EXPERIENCE DISTRIBUTION")
print(f"{'='*60}")
yoe_sorted = sorted(yoe_list)
print(f"  Min: {min(yoe_list):.1f}")
print(f"  Max: {max(yoe_list):.1f}")
print(f"  Median: {yoe_sorted[len(yoe_sorted)//2]:.1f}")
print(f"  Mean: {sum(yoe_list)/len(yoe_list):.1f}")
for pct in [5, 10, 25, 50, 75, 90, 95]:
    idx = int(len(yoe_sorted) * pct / 100)
    print(f"  P{pct}: {yoe_sorted[idx]:.1f}")

print(f"\n{'='*60}")
print(f"SIGNAL DISTRIBUTIONS")
print(f"{'='*60}")
for k, vals in sorted(signal_dists.items()):
    vs = sorted(vals)
    print(f"  {k}: n={len(vs)}, min={min(vs)}, max={max(vs)}, "
          f"median={vs[len(vs)//2]}, mean={sum(vs)/len(vs):.3f}")

print(f"\n{'='*60}")
print(f"NOTICE PERIOD DISTRIBUTION")
print(f"{'='*60}")
notice_sorted = sorted(notice_list)
print(f"  Unique values: {sorted(set(notice_list))}")
nc = Counter(notice_list)
for n, c in nc.most_common(10):
    print(f"  {n}: {c}")

print(f"\n{'='*60}")
print(f"LOCATION DISTRIBUTION (TOP 20)")
print(f"{'='*60}")
for loc, count in location_counts.most_common(20):
    print(f"  {loc}: {count}")

print(f"\n{'='*60}")
print(f"TOTAL SKILLS: {len(skill_counts)} unique")
print(f"MAX SKILLS PER CANDIDATE: {high_skill_count}")

# --- Honeypot Investigation ---
print(f"\n{'='*60}")
print(f"HONEYPOT INVESTIGATION")
print(f"{'='*60}")

# Investigate candidates with suspicious patterns
suspicious = []
for c in candidates:
    flags = []
    cid = c.get("candidate_id", "?")
    yoe = c.get("years_of_experience") or 0
    title = c.get("current_title", "")
    skills = c.get("skills") or []
    company = c.get("current_company", "")
    sig = c.get("redrob_signals") or {}
    
    # 1. Impossible tenure check
    total_tenure = 0
    work_hist = c.get("work_history") or c.get("employment_history") or []
    for wh in work_hist:
        if isinstance(wh, dict):
            yrs = wh.get("years_at_role", 0) or wh.get("duration_years", 0) or 0
            total_tenure += yrs
    
    if total_tenure > yoe * 1.5 and yoe > 0:
        flags.append(f"tenure({total_tenure:.0f}) > yoe({yoe:.0f})")
    
    # 2. Non-tech title with many AI skills
    non_tech_keywords = ["hr", "human resource", "recruiter", "marketing", "sales", 
                         "accountant", "graphic designer", "content writer", "writer",
                         "customer support", "operations", "business analyst", "admin",
                         "finance", "legal", "pr"]
    is_non_tech = any(nt in title.lower() for nt in non_tech_keywords)
    ai_skills = [n for n in skill_names if any(ai in n.lower() for ai in 
                 ["ai", "machine learning", "deep learning", "nlp", "neural",
                  "tensorflow", "pytorch", "llm", "gpt", "transformer", "rag",
                  "embedding", "vector", "ranking", "retrieval"])]
    
    if is_non_tech and len(ai_skills) >= 5:
        flags.append(f"non-tech({title}) + {len(ai_skills)} AI skills")
    
    # 3. High skill count (keyword stuffer)
    if len(skill_names) >= 25:
        flags.append(f"{len(skill_names)} skills")
    
    # 4. Response rate + recency anomaly
    resp = sig.get("response_rate", 0) or 0
    recency = sig.get("days_since_last_active", 999) or 999
    
    if resp > 0.9 and recency > 180:
        flags.append(f"high_resp({resp:.2f}) + inactive({recency}d)")
    if resp < 0.05 and recency < 7:
        flags.append(f"low_resp({resp:.2f}) + active({recency}d)")
    
    # 5. Impossible company tenure
    # (would need founding dates, skip for initial scan)
    
    if flags:
        suspicious.append((cid, yoe, title, company, len(skills), flags))

# Score suspiciousness
print(f"\nCandidates with suspicious patterns: {len(suspicious)}")
suspicious.sort(key=lambda x: -len(x[5]))
print(f"\nTop 100 most suspicious:")
for i, (cid, yoe, title, company, nskills, flags) in enumerate(suspicious[:100]):
    print(f"  {cid}: yoe={yoe}, title='{title[:40]}', "
          f"skills={nskills}, flags={flags}")

# Check overlapping suspicious patterns
multi_pattern = [s for s in suspicious if len(s[5]) >= 2]
print(f"\nCandidates with 2+ suspicious patterns: {len(multi_pattern)}")
for i, s in enumerate(multi_pattern[:30]):
    print(f"  {s[0]}: {s[5]}")

# --- Key AI/ML Titles ---
print(f"\n{'='*60}")
print(f"AI/ML TITLE DISTRIBUTION")
print(f"{'='*60}")
ai_titles = [t for t in title_counts if any(kw in t.lower() for kw in 
             ["ai", "machine learning", "ml engineer", "deep learning",
              "nlp", "data scientist", "applied", "research", "computer vision",
              "recommendation", "search", "intelligence"])]
for t in sorted(ai_titles, key=lambda t: -title_counts[t])[:20]:
    print(f"  {t}: {title_counts[t]}")

# Save key stats to file for reference
import pickle
stats = {
    "total": len(candidates),
    "titles": dict(title_counts.most_common(50)),
    "skills": dict(skill_counts.most_common(100)),
    "companies": dict(company_counts.most_common(50)),
    "yoe_dist": {"p5": yoe_sorted[int(len(yoe_sorted)*0.05)],
                  "p25": yoe_sorted[int(len(yoe_sorted)*0.25)],
                  "p50": yoe_sorted[len(yoe_sorted)//2],
                  "p75": yoe_sorted[int(len(yoe_sorted)*0.75)],
                  "p95": yoe_sorted[int(len(yoe_sorted)*0.95)]},
    "signal_summary": {k: {"min": min(v), "max": max(v), 
                           "median": sorted(v)[len(v)//2],
                           "mean": sum(v)/len(v)}
                       for k, v in signal_dists.items()},
}
with open("data/exploration/stats.pkl", "wb") as f:
    pickle.dump(stats, f)
print("\nStats saved to data/exploration/stats.pkl")
