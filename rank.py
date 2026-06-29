#!/usr/bin/env python3
"""
Phase B: Ranking (≤5 min CPU, no network).
Loads pre-computed artifacts, embeds JD query, FAISS search, fuses scores,
generates reasoning, outputs CSV.
"""
import pickle, csv, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import DATA_ARTIFACTS, DATA_OUTPUT, TOP_N, SEMANTIC_QUERY
from src.embedding_engine import EmbeddingEngine
from src.scorers import compute_final_score, score_title, score_skills, score_experience, score_company, score_signals, score_location, score_education, detect_honeypot_penalty
from src.reasoning import generate_reasoning

DATA_OUTPUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print(f"[{t0:.0f}s] Loading artifacts...")

with open(DATA_ARTIFACTS / "features.pkl", "rb") as f:
    features = pickle.load(f)
print(f"[{time.time()-t0:.0f}s] Loaded {len(features)} feature sets")

engine = EmbeddingEngine()
index = engine.load_index()
print(f"[{time.time()-t0:.0f}s] FAISS index loaded")

jd_vec = engine.embed_single(SEMANTIC_QUERY)
print(f"[{time.time()-t0:.0f}s] JD embedded")

scores_raw, indices = engine.search(index, jd_vec, k=10000)
print(f"[{time.time()-t0:.0f}s] FAISS search complete, top-10000 retrieved (range {scores_raw[-1]:.4f}-{scores_raw[0]:.4f})")

# Min-max rescale semantic scores to [0,1] within top-1000 for discriminability
sem_pool = scores_raw[:1000]
min_sem, max_sem = float(sem_pool[-1]), float(sem_pool[0])
sem_range = max_sem - min_sem
if sem_range > 0:
    scores_raw = [(s - min_sem) / sem_range for s in scores_raw]
else:
    scores_raw = [0.5] * len(scores_raw)
# Clamp to [0,1] for candidates below top-1000 (can go slightly negative)
scores_raw = [max(0.0, min(1.0, s)) for s in scores_raw]

semantic_by_id = {}
for i, (score, idx) in enumerate(zip(scores_raw, indices)):
    semantic_by_id[features[idx].candidate_id] = float(score)

print(f"[{time.time()-t0:.0f}s] Computing final scores for top-10000...")
ranked = []
for i in indices:
    f = features[i]
    cid = f.candidate_id
    sem = semantic_by_id.get(cid, 0.0)

    f.title_score = score_title(f)
    f.skills_score = score_skills(f)
    f.exp_score = score_experience(f)
    f.company_score = score_company(f)
    f.signal_score = score_signals(f)
    f.loc_score = score_location(f)
    f.edu_score = score_education(f)
    f.hon_penalty, f.hon_flags = detect_honeypot_penalty(f)

    final = compute_final_score(
        f, sem, f.title_score, f.skills_score, f.exp_score,
        f.company_score, f.signal_score, f.loc_score, f.edu_score,
        f.hon_penalty
    )
    ranked.append((cid, final, f))

# Sort by 4-decimal score desc (matches validator), then candidate_id asc for ties
ranked.sort(key=lambda x: (-round(x[1], 4), x[0]))

# Take top 100
top = ranked[:TOP_N]

# Generate reasoning
results = []
for i, (cid, score, f) in enumerate(top):
    scores_dict = {
        "title": f.title_score, "skills": f.skills_score,
        "exp": f.exp_score, "company": f.company_score,
        "signal": f.signal_score, "location": f.loc_score,
        "edu": f.edu_score, "semantic": semantic_by_id.get(cid, 0),
        "hon_penalty": f.hon_penalty,
    }
    reasoning = generate_reasoning(f, scores_dict, i + 1)
    results.append({
        "candidate_id": cid,
        "rank": i + 1,
        "score": f"{score:.4f}",
        "reasoning": reasoning,
    })

# Write CSV (participant ID filename)
out_path = DATA_OUTPUT / "submission.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
    writer.writeheader()
    writer.writerows(results)

elapsed = time.time() - t0
print(f"[{elapsed:.0f}s] Submission saved to {out_path}")
print(f"[{elapsed:.0f}s] Total time: {elapsed:.1f}s / 300s budget")
print(f"Top 5:")
for r in results[:5]:
    print(f"  {r['rank']}. {r['candidate_id']} — {r['score']}")

print(f"\nHoneypots in top 100: checking...")
hon_in_top100 = sum(1 for _, _, f in top if f.hon_penalty > 0.3)
print(f"  Candidates with penalty > 0.3: {hon_in_top100}/{TOP_N}")
if hon_in_top100 > 10:
    print(f"  ⚠️  WARNING: Honeypot rate {hon_in_top100}% exceeds 10% threshold!")
