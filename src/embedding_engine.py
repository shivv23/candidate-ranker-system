#!/usr/bin/env python3
"""Sentence-transformers embedding + FAISS index."""
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.config import DATA_ARTIFACTS


class EmbeddingEngine:
    def __init__(self, model_name="all-MiniLM-L6-v2", cache_dir=None):
        if cache_dir is None:
            cache_dir = str(DATA_ARTIFACTS / "model_cache")
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts, batch_size=1024, show_progress=True):
        emb = self.model.encode(texts, batch_size=batch_size,
                                show_progress_bar=show_progress,
                                normalize_embeddings=True)
        return np.array(emb, dtype=np.float32)

    def embed_single(self, text):
        return self.embed([text], show_progress=False)[0]

    def build_index(self, embeddings):
        index = faiss.IndexFlatIP(self.dim)
        index.add(embeddings)
        return index

    def save_index(self, index, path=None):
        if path is None:
            path = str(DATA_ARTIFACTS / "faiss_index.bin")
        faiss.write_index(index, path)
        return path

    def load_index(self, path=None):
        if path is None:
            path = str(DATA_ARTIFACTS / "faiss_index.bin")
        return faiss.read_index(path)

    def search(self, index, query_vec, k=1000):
        scores, indices = index.search(query_vec.reshape(1, -1), k)
        return scores[0], indices[0]
