# Candidate Ranking System

India Runs Data & AI Challenge 2026 — Ranking 100K candidates against a Senior AI Engineer job description.

## Setup

```bash
pip install -r requirements.txt
```

Place `candidates.jsonl` in `data/raw/` and the JD file in the same directory. The dataset is not included in this repository.

## Reproduce Submission

### Phase A: Pre-computation (offline, ~14 min)

Generates embeddings and FAISS index for all 100K candidates:

```bash
python precompute.py
```

This runs once. Artifacts are cached in `data/artifacts/`.

### Phase B: Ranking (≤5 min CPU, no network)

Loads precomputed artifacts, embeds the JD query, retrieves top-10K by cosine similarity, fuses 8 scoring dimensions, and outputs the top-100:

```bash
python rank.py
```

Output: `data/output/submission.csv`

### Validate

```bash
python data/validate_submission.py data/output/submission.csv
```

## Architecture

Two-phase pipeline designed for the 5-minute CPU ranking constraint:

### Phase A (Offline)

```
candidates.jsonl → Feature Extraction → all-MiniLM-L6-v2 Embeddings → FAISS Index
```

- Extracts 20+ features per candidate: title, skills (named + categorized), experience, company type, location, 9 behavioral signals, education, career history descriptions
- Profile text is enriched with career_history descriptions (last 3 jobs) and education for better semantic matching
- Embeddings checkpointed every 5000 texts for resume after interrupt

### Phase B (Ranking)

```
JD Query → Embed → FAISS Search (top-10K) → Min-Max Normalize → Score Fusion → Top-100
```

Eight scoring dimensions are fused linearly:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Semantic | 20% | Profile-JD cosine similarity (all-MiniLM-L6-v2) |
| Skills | 30% | Matched skills across AI/ML, retrieval, ranking, engineering |
| Title | 15% | Title relevance with 35+ scoring tiers |
| Experience | 10% | Bell curve centered on 7yr (target 4-10yr) |
| Signals | 10% | 9 behavioral signals (response rate, activity, engagement) |
| Company | 5% | Product=1.0, Startup=0.6, Consulting=0.4 |
| Location | 5% | Pune/Noida=1.0, other India=0.7, willing to relocate=1.0 |
| Education | 5% | CS/AI/ML/related=1.0, else=0.5 |

### Modifiers

- **Honeypot penalty**: Multiplicative `base × (1.0 − 0.8 × penalty)`. Detects keyword stuffing, ghost profiles, fake companies, all-consulting backgrounds, and CV/speech-only profiles
- **Notice period**: ≤30d ×1.05, 61-90d ×0.93, >90d ×0.85
- **Score spread**: `1.0 − 1.5 × (1.0 − base)` to widen distribution

## Results

- **Score range**: 0.5895 – 0.9704
- **Unique scores**: 98/100 (2 tied pairs, resolved by candidate_id ascending)
- **Honeypots in top 100**: 0
- **Phase B runtime**: 14.2s / 300s budget
- **Validation**: PASS

## Project Structure

```
├── precompute.py          # Phase A: feature extraction, embedding, index build
├── rank.py                # Phase B: JD embed, search, score fusion, CSV output
├── sandbox.ipynb          # Colab notebook for Stage 3 verification
├── requirements.txt       # Dependencies
├── submission_metadata.yaml
├── deck/
│   └── presentation.pptx
├── src/
│   ├── config.py          # Weights, thresholds, skill lists, company lists
│   ├── loader.py          # JSONL/JSON loader
│   ├── feature_extractor.py  # CandidateFeatures dataclass + extraction
│   ├── embedding_engine.py   # Sentence-transformers + FAISS wrapper
│   ├── scorers.py         # All scoring functions + honeypot detection
│   └── reasoning.py       # Stage 4 reasoning generator
├── tests/                 # (placeholder)
└── data/
    ├── raw/               # candidates.jsonl (not in repo)
    ├── artifacts/         # Embeddings, FAISS index, features (not in repo)
    └── output/            # submission.csv (not in repo)
```
