"""Sparse weighted continuation counts, analogous to a symbolic unembedding."""

from collections import Counter
from dataclasses import dataclass
import heapq
import math
from typing import Iterable, Sequence

from .latents import token_key, tokenize


@dataclass(frozen=True)
class Readout:
    distribution: dict[str, float]
    recent_tokens: tuple[str, ...]
    matched_context: tuple[str, ...]
    order: int
    retained_mass: float
    observations: float


class FrequencyHead:
    """Learn C(prefix, next) for prefixes of length 0, 1, and 2.

    This is count estimation, not gradient descent. Only observed continuations
    are stored; neither training nor prediction allocates a vocabulary-sized row.
    """

    def __init__(self):
        self.counts: dict[tuple[str, ...], Counter] = {}

    def observe(self, context: Sequence[str], target: str, *, weight: float = 1.0):
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("training weight must be positive and finite")
        recent = tuple(token_key(t) for t in context[-2:])
        target = token_key(target)
        for length in range(len(recent) + 1):
            key = recent[-length:] if length else ()
            self.counts.setdefault(key, Counter())[target] += weight

    def fit(self, documents: Iterable[str], *, weight: float = 1.0):
        """Add observations; never make n-grams across document boundaries."""
        for document in documents:
            tokens = tokenize(document)
            for i, target in enumerate(tokens):
                self.observe(tokens[max(0, i - 2):i], target, weight=weight)
        return self

    def fit_grammar(self, node):
        """Optional bridge: grammarworlds derivation mass becomes count weight.

        Expansion is exhaustive, so use only small finite grammars. This imports
        grammarworlds lazily and does not read or change a grammarworld World.
        """
        from grammarworlds.grammar import expand

        for tokens, probability, _rules in expand(node):
            for i, target in enumerate(tokens):
                self.observe(tokens[max(0, i - 2):i], target, weight=probability)
        return self

    def read(self, latents: Sequence[dict], *, top_k: int = 10) -> Readout:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        recent = tuple(latent["token"] for latent in latents[-3:])
        # A trigram contains TWO conditioning tokens plus the proposed next word.
        # The third recent latent is exposed for future readout heads.
        for length in range(min(2, len(recent)), -1, -1):
            key = recent[-length:] if length else ()
            row = self.counts.get(key)
            if row:
                # Stable ties, bounded top-k selection, no full probability table.
                best = heapq.nsmallest(top_k, row.items(), key=lambda item: (-item[1], item[0]))
                kept = math.fsum(count for _, count in best)
                total = math.fsum(row.values())
                return Readout(
                    {token: count / kept for token, count in best}, recent, key,
                    length + 1, kept / total, total,
                )
        return Readout({}, recent, (), 0, 0.0, 0.0)

    def to_rows(self) -> list[dict]:
        return [{"context": list(key), "next": dict(sorted(row.items()))}
                for key, row in sorted(self.counts.items())]

    @classmethod
    def from_rows(cls, rows: list[dict]):
        head = cls()
        for row in rows:
            key = tuple(row["context"])
            values = row["next"]
            if (len(key) > 2 or key in head.counts
                    or any(not isinstance(t, str) or not t or token_key(t) != t for t in key)
                    or not isinstance(values, dict) or not values):
                raise ValueError("invalid or duplicate frequency context")
            if any(not isinstance(t, str) or not t or token_key(t) != t
                   or isinstance(c, bool) or not isinstance(c, (int, float))
                   or not math.isfinite(c) or c <= 0 for t, c in values.items()):
                raise ValueError("invalid continuation count")
            head.counts[key] = Counter(values)
        return head
