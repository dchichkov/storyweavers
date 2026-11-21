"""Lookup attention -> symbolic value distribution -> grammar log-weight factors.

No parsing, world updates, model calls, or implicit program-head fallbacks occur
here. Inputs are scoped, typed records supplied by a grammar/world adapter.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
from typing import Iterable


class TableFormatError(ValueError):
    """Malformed authored data; never silently substitute a uniform table."""


class ProgramRequired(NotImplementedError):
    def __init__(self, spec: dict):
        self.head_id = spec["id"]
        self.algorithm = spec["required_program"]
        super().__init__(f'{self.head_id} ({spec["name"]}) requires a program: {self.algorithm}')


@dataclass(frozen=True)
class Source:
    id: str
    channel: str
    scope: str
    key: str
    confidence: float = 1.0

    def __post_init__(self):
        if not all(isinstance(s, str) and s for s in (self.id, self.channel, self.scope, self.key)):
            raise ValueError("source id/channel/scope/key must be nonempty strings")
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError("source confidence must be finite and in [0, 1]")


@dataclass(frozen=True)
class HeadContext:
    head_id: str
    query: str
    scope: str
    strength: float = 1.0

    def __post_init__(self):
        if not all(isinstance(s, str) and s for s in (self.head_id, self.query, self.scope)):
            raise ValueError("head id/query/scope must be nonempty strings")
        if not math.isfinite(self.strength) or not 0 <= self.strength <= 10:
            raise ValueError("head strength must be finite and in [0, 10]")


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    if not weights:
        return {}
    largest = max(weights.values())
    if largest <= 0:
        return {}
    # Preserve positive support across extreme but finite authored weight ranges.
    scaled = {k: max(v / largest, 1e-300) if v > 0 else 0.0 for k, v in weights.items()}
    total = math.fsum(scaled.values())
    return {k: v / total for k, v in scaled.items()}


class Lookup:
    """Bigram backoff with exact trigram override; no fuzzy or wildcard matching."""

    def __init__(self, rows: list[dict], *, lengths=(2, 3), allow_zero=False):
        self.rows = {}
        for row in rows:
            if set(row) != {"tokens", "weight"}:
                raise TableFormatError("table rows require exactly tokens and weight")
            if not isinstance(row["tokens"], list):
                raise TableFormatError("tokens must be a JSON list, not a delimited string")
            key, weight = tuple(row["tokens"]), row["weight"]
            if len(key) not in lengths or not all(isinstance(t, str) and t for t in key):
                raise TableFormatError(f"invalid n-gram: {key}")
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight):
                raise TableFormatError(f"non-finite/nonnumeric weight: {key}")
            if weight < 0 or (weight == 0 and not allow_zero):
                raise TableFormatError(f"invalid weight: {key}")
            if key in self.rows:
                raise TableFormatError(f"duplicate n-gram: {key}")
            self.rows[key] = float(weight)

    def get(self, query, source, output, default=None):
        return self.rows.get((query, source, output), self.rows.get((source, output), default))

    def outputs(self, query, source):
        result = {key[1]: weight for key, weight in self.rows.items()
                  if len(key) == 2 and key[0] == source}
        result.update({key[2]: weight for key, weight in self.rows.items()
                       if len(key) == 3 and key[:2] == (query, source)})
        return result


class HeadLibrary:
    def __init__(self, specs: Iterable[dict]):
        self._specs, self._tables = {}, {}
        for original in specs:
            spec = deepcopy(original)
            head_id = spec["id"]
            if head_id in self._specs:
                raise TableFormatError(f"duplicate head: {head_id}")
            if spec["status"] == "program_required":
                if not spec.get("required_program") or any(spec.get(k) for k in ("selection", "projection", "receiver")):
                    raise TableFormatError(f"deferred head must have a reason and no executable tables: {head_id}")
            elif spec["status"] == "table":
                if spec.get("receiver_mode") not in {"multipliers", "counts"}:
                    raise TableFormatError(f"unknown receiver mode: {head_id}")
                if not spec.get("input_channel"):
                    raise TableFormatError(f"missing input channel: {head_id}")
                alpha = spec.get("smoothing", 1.0)
                if not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or alpha <= 0:
                    raise TableFormatError("smoothing must be finite and positive")
                self._tables[head_id] = (
                    Lookup(spec["selection"], lengths=(2,)),
                    Lookup(spec["projection"]),
                    Lookup(spec["receiver"], allow_zero=spec["receiver_mode"] == "counts"),
                )
            else:
                raise TableFormatError(f"unknown head status: {head_id}")
            self._specs[head_id] = spec

    @property
    def ids(self):
        return tuple(sorted(self._specs))

    def describe(self, head_id: str) -> dict:
        return deepcopy(self._specs[head_id])

    def activate(self, context: HeadContext, memory: Iterable[Source]) -> dict:
        spec = self._specs[context.head_id]
        if spec["status"] == "program_required":
            raise ProgramRequired(spec)
        selection, projection, _ = self._tables[context.head_id]
        records = list(memory)
        if len({s.id for s in records}) != len(records):
            raise ValueError("memory source IDs must be unique")
        matched = []
        for source in records:
            if source.channel != spec["input_channel"] or source.scope != context.scope:
                continue
            weight = selection.rows.get((context.query, source.key), 0)
            values = _normalize(projection.outputs(context.query, source.key))
            if weight and source.confidence and values:
                matched.append((source, weight * source.confidence, values))
        attention = _normalize({source.id: w for source, w, _ in matched})
        features, trace = {}, []
        confidence = 0.0
        for source, _, values in matched:
            a = attention[source.id]
            confidence += a * source.confidence
            for value, p in values.items():
                features[value] = features.get(value, 0.0) + a * p
            trace.append({"source_id": source.id, "key": source.key, "attention": a,
                          "confidence": source.confidence, "values": values})
        return {"head_id": context.head_id, "query": context.query, "scope": context.scope,
                "status": "active" if features else "abstained", "features": features,
                "confidence": confidence, "sources": trace}

    def rerank(self, base: dict[str, float], contexts: Iterable[HeadContext],
               memory: Iterable[Source]) -> dict:
        """Reweight grammar-supported words. Zero/absent words cannot be revived.

        Missing multiplier rows mean factor 1. Count tables use a grammar-prior
        Dirichlet pseudocount on the current candidate set; excluded counts are
        reported and do not create extra candidates. No top-k pruning occurs.
        """
        for word, p in base.items():
            if not isinstance(word, str) or not word or not isinstance(p, (int, float)) or not math.isfinite(p) or p < 0:
                raise ValueError("grammar weights must be finite, nonnegative, with nonempty word keys")
        probabilities = _normalize({w: p for w, p in base.items() if p > 0})
        records, requests = tuple(memory), tuple(contexts)
        if len({c.head_id for c in requests}) != len(requests):
            raise ValueError("activate a head once per prediction; combine its evidence in memory")
        # Deferred requests fail even when the grammar has no continuation.
        activations = [self.activate(c, records) for c in requests]
        scores = {w: math.log(p) for w, p in probabilities.items()}
        for context, activation in zip(requests, activations):
            spec = self._specs[context.head_id]
            receiver = self._tables[context.head_id][2]
            deltas = {w: 0.0 for w in probabilities}
            excluded = set()
            for feature, mass in activation["features"].items():
                rows = receiver.outputs(context.query, feature)
                excluded.update(set(rows) - set(probabilities))
                if spec["receiver_mode"] == "counts":
                    # Scale before summation to avoid overflow on large counts.
                    alpha = spec.get("smoothing", 1.0)
                    scale = max([alpha] + [rows.get(w, 0) for w in probabilities])
                    total = math.fsum(rows.get(w, 0) / scale for w in probabilities)
                    for w, p in probabilities.items():
                        numerator = rows.get(w, 0) / scale + alpha / scale * p
                        denominator = total + alpha / scale
                        adjusted = numerator / denominator
                        # The corpus can shrink probability strongly, but not
                        # erase a legal token through floating-point underflow.
                        deltas[w] += mass * (math.log(max(adjusted, 1e-300)) - math.log(p))
                else:
                    for w in probabilities:
                        deltas[w] += mass * math.log(rows.get(w, 1.0))
            gate = context.strength * activation["confidence"]
            activation["log_adjustments"] = {w: gate * d for w, d in deltas.items()}
            activation["outside_grammar"] = sorted(excluded)
            for w in scores:
                scores[w] += gate * deltas[w]
        if scores:
            largest = max(scores.values())
            result = _normalize({w: math.exp(max(v - largest, -700)) for w, v in scores.items()})
        else:
            result = {}
        return {"base": probabilities, "probabilities": result, "heads": activations}


def load_library(directory: str | Path | None = None) -> HeadLibrary:
    path = Path(directory) if directory else Path(__file__).with_name("data")
    files = sorted(path.glob("P*.json"))
    if not files:
        raise TableFormatError(f"no head specifications in {path}")
    return HeadLibrary(json.loads(p.read_text()) for p in files)


def predict(forest, prefix: tuple[str, ...], library: HeadLibrary,
            contexts: Iterable[HeadContext], memory: Iterable[Source]) -> dict:
    """Adapter for the existing weighted Forest; keeps semantic/rule metadata.

    prefix_probability remains the original grammar-prefix mass, not the new
    sequence probability. The latter is a product of sampled conditional scores.
    """
    prediction = deepcopy(forest.predict(prefix))
    base = {choice["word"]: choice["probability"] for choice in prediction["choices"]}
    result = library.rerank(base, contexts, memory)
    for choice in prediction["choices"]:
        choice["grammar_probability"] = choice["probability"]
        choice["probability"] = result["probabilities"].get(choice["word"], 0.0)
    prediction["choices"].sort(key=lambda c: (-c["probability"], c["word"]))
    prediction["symbolic_heads"] = result["heads"]
    prediction["grammar_prefix_probability"] = prediction.pop("prefix_probability")
    return prediction


def sample(prediction: dict, rng: random.Random) -> str:
    choices = prediction["choices"]
    if not choices:
        raise ValueError("cannot sample an unsupported grammar prefix")
    return rng.choices([c["word"] for c in choices],
                       weights=[c["probability"] for c in choices], k=1)[0]
