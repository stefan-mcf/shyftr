"""Embedding provider abstraction for ShyftR vector retrieval.

Defines the ``EmbeddingProvider`` protocol and ships a deterministic,
dependency-free test provider suitable for stable unit tests. No network
calls or model downloads are required.
"""
from __future__ import annotations

import hashlib
import math
from typing import List, Protocol, Sequence, runtime_checkable


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol that every embedding backend must satisfy."""

    @property
    def dimension(self) -> int:
        """Return the fixed dimensionality of produced vectors."""
        ...

    def embed(self, text: str) -> List[float]:
        """Return a unit-length embedding for *text*."""
        ...

    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        """Return embeddings for a batch of texts."""
        ...


# ---------------------------------------------------------------------------
# Deterministic test provider
# ---------------------------------------------------------------------------

class DeterministicEmbeddingProvider:
    """Dependency-free embedding provider for tests.

    Produces deterministic, reproducible vectors by hashing each token
    and distributing the hash bits across a fixed-dimension vector.  The
    result is L2-normalised so cosine similarity reduces to dot product.

    Parameters
    ----------
    dim : int
        Dimensionality of the output vectors (default 64).
    """

    def __init__(self, dim: int = 64) -> None:
        if dim < 2:
            raise ValueError("dim must be >= 2")
        self._dim = dim

    # -- EmbeddingProvider protocol ----------------------------------------

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> List[float]:
        return self._embed_text(text)

    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    # -- internals ---------------------------------------------------------

    def _embed_text(self, text: str) -> List[float]:
        """Hash *text* into a deterministic unit vector."""
        tokens = text.lower().split()
        vec = [0.0] * self._dim
        for token in tokens:
            h = hashlib.sha256(token.encode("utf-8")).digest()
            # Use the first 32 bytes of the hash to fill the vector
            for i in range(self._dim):
                byte_idx = i % len(h)
                # Map byte value to [-1, 1]
                vec[i] += (h[byte_idx] / 127.5) - 1.0
        return _l2_normalise(vec)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _l2_normalise(vec: List[float]) -> List[float]:
    """Return an L2-normalised copy of *vec*."""
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec[:]
    return [v / norm for v in vec]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two equal-length vectors.

    Returns 0.0 for zero-norm vectors.
    """
    if len(a) != len(b):
        raise ValueError(
            f"Vector lengths differ: {len(a)} vs {len(b)}"
        )
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
