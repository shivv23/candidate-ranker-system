#!/usr/bin/env python3
import json

with open('data/raw/candidates.jsonl') as f:
    lines = [json.loads(l) for l in f if l.strip()]

print("=== First 5 candidates in detail ===")
for c in lines[:5]:
    cid = c['candidate_id']
    prof = c['profile']
    ch = c.get('career_history', [])
    skills = c.get('skills', [])
    sig = c.get('redrob_signals', {})

    print(f'\n=== {cid} ===')
    print(f'  Headline: {prof.get("headline","")[:100]}')
    print(f'  Title: {prof.get("current_title")}')
    print(f'  Company: {prof.get("current_company")}')
    print(f'  YOE: {prof.get("years_of_experience")}')
    print(f'  Location: {prof.get("location")}')
    print(f'  Summary (first 200): {str(prof.get("summary",""))[:200]}')
    
    for i, job in enumerate(ch):
        print(f'  Job {i+1}: {job.get("title","?")} @ {job.get("company","?")} ({job.get("duration_years","?")}yr)')
    
    for s in skills[:5]:
        print(f'  Skill: {s.get("name","?")} (prof={s.get("proficiency","?")}, yrs={s.get("years_of_experience","?")})')
    if len(skills) > 5:
        print(f'  ... and {len(skills)-5} more')
    
    print(f'  Signals keys: {list(sig.keys())}')
    flat = {k: v for k, v in sig.items() if not isinstance(v, (dict, list))}
    print(f'  Signal values: {flat}')

# Check career history patterns and look for honeypots
print("\n\n=== HONEYPOT PATTERN ANALYSIS ===")
honeypot_candidates = []
for c in lines:
    cid = c['candidate_id']
    prof = c['profile']
    ch = c.get('career_history', [])
    skills = c.get('skills', [])
    yoe = prof.get('years_of_experience', 0) or 0
    title = prof.get('current_title', '') or ''

    flags = []

    # 1. Impossible tenure: career history years > claimed YOE
    total_career_years = sum(job.get('duration_years', 0) or 0 for job in ch)
    num_jobs = len(ch)
    
    if total_career_years > yoe * 1.5 and yoe > 0:
        flags.append(f'career_sum({total_career_years:.1f}) > 1.5x yoe({yoe})')
    
    # 2. Too many jobs for YOE
    if yoe > 0 and num_jobs > yoe * 2:
        flags.append(f'{num_jobs} jobs for {yoe}yr')
    
    # 3. Skill proficiency check (expert in many skills with 0 years)
    expert_zero = sum(1 for s in skills if isinstance(s, dict) and 
                      str(s.get('proficiency','')).lower() in ('expert','advanced','5') 
                      and (s.get('years_of_experience', 0) or 0) == 0)
    if expert_zero >= 3:
        flags.append(f'{expert_zero} expert skills with 0yr exp')
    
    # 4. Skills with absurd duration
    max_skill_yrs = max((s.get('years_of_experience', 0) or 0) for s in skills) if skills else 0
    if max_skill_yrs > yoe + 3 and yoe > 0:
        flags.append(f'skill_yrs({max_skill_yrs}) > yoe({yoe})+3')
    
    # 5. Non-tech title with heavy AI skills
    non_tech = ['hr', 'marketing', 'sales', 'accountant', 'graphic designer', 
                'content writer', 'customer support', 'operations', 'business analyst',
                'civil engineer', 'mechanical engineer']
    nt_match = any(nt in title.lower() for nt in non_tech)
    ai_skill_names = [s.get('name','') for s in skills if isinstance(s, dict)]
    ai_count = sum(1 for n in ai_skill_names if any(kw in n.lower() for kw in
                   ['machine learning', 'deep learning', 'tensorflow', 'pytorch',
                    'ai', 'nlp', 'neural', 'llm', 'transformer', 'rag', 'embedding']))
    if nt_match and ai_count >= 5:
        flags.append(f'{title} with {ai_count} AI skills')
    
    if flags:
        honeypot_candidates.append((cid, yoe, title, flags, total_career_years, num_jobs))

print(f'Candidates with suspicious patterns: {len(honeypot_candidates)}')
honeypot_candidates.sort(key=lambda x: -len(x[3]))
for cid, yoe, title, flags, tcy, nj in honeypot_candidates[:30]:
    print(f'  {cid}: yoe={yoe}, title="{title[:30]}" careersum={tcy:.1f} jobs={nj} | {flags}')
