#!/usr/bin/env python3
"""
Phase A: Pre-computation (offline, no time limit).
Embed ALL 100K candidates, build FAISS index.
Checkpoints at each major stage for resume after interrupt.
"""
import pickle, time, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from src.config import DATA_RAW, DATA_ARTIFACTS
from src.loader import load_candidates
from src.feature_extractor import extract_features
from src.embedding_engine import EmbeddingEngine

DATA_ARTIFACTS.mkdir(parents=True, exist_ok=True)
t0 = time.time()
CHECKPOINT_FEATURES = DATA_ARTIFACTS / "features_checkpoint.pkl"
CHECKPOINT_EMBEDDINGS = DATA_ARTIFACTS / "embeddings.npy"
FAISS_PATH = DATA_ARTIFACTS / "faiss_index.bin"

def save_checkpoint(obj, path, label):
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    print(f"[{time.time()-t0:.0f}s] Checkpoint saved: {label}")

# ---- Stage 1: Load & extract features ----
if CHECKPOINT_FEATURES.exists():
    print(f"[{time.time()-t0:.0f}s] Resuming from features checkpoint...")
    with open(CHECKPOINT_FEATURES, "rb") as f:
        features = pickle.load(f)
    print(f"[{time.time()-t0:.0f}s] Loaded {len(features)} feature sets from checkpoint")
else:
    print(f"[{time.time()-t0:.0f}s] Loading candidates...")
    candidates = load_candidates(DATA_RAW / "candidates.jsonl")
    print(f"[{time.time()-t0:.0f}s] Loaded {len(candidates)} candidates")

    print(f"[{time.time()-t0:.0f}s] Extracting features...")
    features = [extract_features(c) for c in candidates]
    print(f"[{time.time()-t0:.0f}s] Extracted {len(features)} feature sets")
    del candidates

    save_checkpoint(features, CHECKPOINT_FEATURES, "features")

CHUNK_SIZE = 5000
EMBED_PROGRESS = DATA_ARTIFACTS / "embed_progress.pkl"

# ---- Stage 2: Embeddings (chunked with per-chunk checkpoint) ----
if CHECKPOINT_EMBEDDINGS.exists() and not EMBED_PROGRESS.exists():
    print(f"[{time.time()-t0:.0f}s] Loading complete embeddings checkpoint...")
    embeddings = np.load(CHECKPOINT_EMBEDDINGS)
    print(f"[{time.time()-t0:.0f}s] Embeddings shape: {embeddings.shape}")
else:
    print(f"[{time.time()-t0:.0f}s] Embedding ALL {len(features)} candidates...")
    engine = EmbeddingEngine()
    texts = [f.profile_text for f in features]
    done = 0

    if EMBED_PROGRESS.exists():
        with open(EMBED_PROGRESS, "rb") as f:
            done = pickle.load(f)
        print(f"[{time.time()-t0:.0f}s] Resuming embedding from {done}/{len(texts)}")
        embeddings = np.load(CHECKPOINT_EMBEDDINGS)
    else:
        embeddings = np.zeros((len(texts), engine.dim), dtype=np.float32)

    for chunk_start in range(done, len(texts), CHUNK_SIZE):
        chunk_end = min(chunk_start + CHUNK_SIZE, len(texts))
        chunk_texts = texts[chunk_start:chunk_end]
        chunk_emb = engine.embed(chunk_texts, batch_size=512, show_progress=False)
        embeddings[chunk_start:chunk_end] = chunk_emb

        np.save(CHECKPOINT_EMBEDDINGS, embeddings)
        with open(EMBED_PROGRESS, "wb") as f:
            pickle.dump(chunk_end, f)

        pct = chunk_end / len(texts) * 100
        eta = (time.time() - t0) / chunk_end * (len(texts) - chunk_end)
        print(f"[{time.time()-t0:.0f}s] Embedded {chunk_end}/{len(texts)} ({pct:.0f}%) ETA {eta:.0f}s")

    EMBED_PROGRESS.unlink(missing_ok=True)
    print(f"[{time.time()-t0:.0f}s] Embeddings complete, shape: {embeddings.shape}")

# ---- Stage 3: FAISS index ----
if FAISS_PATH.exists():
    print(f"[{time.time()-t0:.0f}s] FAISS index already exists, skipping build")
else:
    print(f"[{time.time()-t0:.0f}s] Building FAISS index...")
    engine = EmbeddingEngine()
    index = engine.build_index(embeddings)
    engine.save_index(index, str(FAISS_PATH))
    print(f"[{time.time()-t0:.0f}s] FAISS index saved")
    del index

del embeddings

# ---- Stage 4: Final save ----
print(f"[{time.time()-t0:.0f}s] Saving final artifacts...")
with open(DATA_ARTIFACTS / "features.pkl", "wb") as f:
    pickle.dump(features, f)
print(f"[{time.time()-t0:.0f}s] All artifacts saved. Total time: {time.time()-t0:.0f}s")
