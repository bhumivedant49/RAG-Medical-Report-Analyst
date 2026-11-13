import faiss
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

@st.cache_resource(show_spinner="Loading the text embedding model...")
def get_embedding_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class ReportIndex:
    """In-memory vector index for the currently uploaded report set."""
    def __init__(self, chunks: list[dict], model: SentenceTransformer):
        if not chunks:
            raise ValueError("No text passages were supplied.")
        self.chunks = chunks
        self.model = model
        vectors = model.encode(
            [item["text"] for item in chunks],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        vector = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")
        count = min(top_k, len(self.chunks))
        scores, indices = self.index.search(vector, count)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            item = dict(self.chunks[int(idx)])
            item["score"] = float(score)
            results.append(item)
        return results
