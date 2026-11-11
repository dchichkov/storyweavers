"""Causal grammar heads, additive residual evidence, and a joint grammar readout."""

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import random

from .grammar import GrammarNeuron, canonical, pack, positive, register_types, unpack


SEMANTIC_FIELDS = ("pos", "entity", "role", "location", "event")
PROTECTED = frozenset({"token", "surface", "position", "index", "start", "end", "kind"})


def complete(latent):
    if not isinstance(latent, dict) or not isinstance(latent.get("token"), str) or not latent["token"]:
        raise ValueError("a latent needs a nonempty token")
    return {**dict.fromkeys(SEMANTIC_FIELDS), **deepcopy(latent)}


def semantic(latent):
    return {k: v for k, v in complete(latent).items() if k not in PROTECTED - {"token"}}


@dataclass
class Residual:
    observed: dict
    scores: dict = field(default_factory=dict)

    @classmethod
    def from_latent(cls, latent):
        latent = complete(latent)
        return cls(latent, {k: {"null": 0., canonical(v): 1. if v is not None else 0.}
                            for k, v in latent.items() if k not in PROTECTED})

    def view(self):
        result = deepcopy(self.observed)
        for key, scores in self.scores.items():
            winner = min(scores, key=lambda value: (-scores[value], value != "null", value))
            result[key] = json.loads(winner)
        return result

    def probabilities(self, attribute):
        scores = self.scores.get(attribute, {"null": 0.})
        largest = max(scores.values())
        weights = {key: math.exp(score - largest) for key, score in scores.items()}
        total = math.fsum(weights.values())
        return [{"value": json.loads(key), "probability": value / total} for key, value in sorted(weights.items())]


@dataclass
class GrammarHead:
    neuron: GrammarNeuron
    operation: str = "add"
    strength: float = 1.
    null_mass: float = 1.

    def __post_init__(self):
        if self.operation not in {"add", "suppress"}:
            raise ValueError("head operation must be add or suppress")
        positive(self.strength, "head strength", zero=True)
        positive(self.null_mass, "null match mass")
        for rule in self.neuron.rules:
            if PROTECTED.intersection(rule.emit):
                raise ValueError("heads cannot write observed tokens or positions")

    def propose(self, context):
        matches = self.neuron.activate(context) if self.strength else []
        total = self.null_mass + math.fsum(m.mass for m in matches)
        sign = 1 if self.operation == "add" else -1
        return [(m, sign * self.strength * m.mass / total) for m in matches]


@dataclass
class StoryformerBlock:
    heads: tuple = ()
    num_heads: int = 16

    def __post_init__(self):
        if type(self.num_heads) is not int or self.num_heads < 1 or len(self.heads) > self.num_heads:
            raise ValueError("invalid number of head slots")
        self.heads = tuple(self.heads) + (None,) * (self.num_heads - len(self.heads))

    def forward(self, stream):
        """All heads read one snapshot, write only the current query, then merge."""
        if stream and isinstance(stream[0], dict):
            stream = [Residual.from_latent(row) for row in Storyformer._prepare(stream)]
        snapshot = [row.view() for row in stream]
        output, trace = deepcopy(stream), []
        for i, target in enumerate(output):
            deltas = defaultdict(list)
            for slot, head in enumerate(self.heads):
                if head is None:
                    continue
                # Isolate mutable dictionaries as well as the future prefix.
                for match, delta in head.propose(deepcopy(snapshot[:i + 1])):
                    for attribute, value in match.value.items():
                        if attribute in PROTECTED:
                            raise ValueError("head attempted an observed-field write")
                        deltas[attribute, canonical(value)].append(delta)
                    trace.append(dict(query=snapshot[i]["position"]["token"], head=slot,
                                      neuron=head.neuron.name, rule=match.rule, mass=match.mass,
                                      delta=delta, values=deepcopy(match.value), sources=match.sources))
            for (attribute, value), contributions in sorted(deltas.items()):
                scores = target.scores.setdefault(attribute, {"null": 0.})
                scores[value] = scores.get(value, 0.) + math.fsum(sorted(contributions))
        return output, trace


class JointDistribution:
    def __init__(self, weighted, top_k=10):
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be positive")
        bundles, values = defaultdict(list), {}
        for latent, mass in weighted:
            positive(mass, "candidate mass")
            latent = complete(latent)
            key = canonical(latent)
            values[key] = latent
            bundles[key].append(mass)
        masses = {key: math.fsum(parts) for key, parts in bundles.items()}
        total = math.fsum(masses.values())
        self.joint = [{"latent": values[key], "probability": mass / total}
                      for key, mass in sorted(masses.items())]
        words = defaultdict(float)
        for candidate in self.joint:
            words[candidate["latent"]["token"]] += candidate["probability"]
        kept = sorted(words, key=lambda word: (-words[word], word))[:top_k]
        self.retained_mass = math.fsum(words[word] for word in kept)
        self.probabilities = {word: words[word] / self.retained_mass for word in kept}
        self.candidates = [{**deepcopy(row), "probability": row["probability"] / self.retained_mass}
                           for row in self.joint if row["latent"]["token"] in self.probabilities]

    def probability(self, target):
        target = semantic(target)
        return math.fsum(row["probability"] for row in self.joint
                         if all(canonical(row["latent"].get(k)) == canonical(v) for k, v in target.items()))

    def sample(self, rng=None):
        if not self.candidates:
            raise ValueError("no output grammar matched; supply an explicit backoff grammar")
        row = (rng or random).choices(self.candidates, weights=[c["probability"] for c in self.candidates])[0]
        return deepcopy(row["latent"])

    def to_dict(self):
        return dict(probabilities=self.probabilities, candidates=deepcopy(self.candidates), retained_mass=self.retained_mass)


@dataclass
class GrammarProjection:
    neurons: dict = field(default_factory=dict)

    def activations(self, context):
        result = []
        for word, neuron in sorted(self.neurons.items()):
            for match in neuron.activate(context):
                if "token" in match.value and match.value["token"] != word:
                    raise ValueError("output grammar emitted a different vocabulary token")
                result.append((word, neuron, match, complete({**match.value, "token": word})))
        return result

    def read(self, context, top_k=10, *, position_context=None):
        from .positions import add_positions

        history = context if position_context is None else position_context
        rows = []
        for _word, _neuron, match, latent in self.activations(context):
            # Positions are deterministic metadata; never supplied by an LLM.
            positioned = add_positions([*history, latent])
            position = positioned[-1]["position"]
            if history and isinstance(history[-1].get("position"), dict):
                old, local = history[-1]["position"], positioned[-2]["position"]
                position["token"] += old["token"] - local["token"]
                position["sentence"] += old["sentence"] - local["sentence"]
                if positioned[-1]["position"]["sentence"] == old["sentence"]:
                    position["in_sentence"] += old["in_sentence"] - local["in_sentence"]
            latent["position"] = position
            rows.append((latent, match.mass))
        return JointDistribution(rows, top_k)


@dataclass
class GrammarForward:
    residual_stream: list
    evidence: list
    predictions: list
    next_latent: JointDistribution
    trace: list


register_types(GrammarHead, StoryformerBlock, GrammarProjection)


class Storyformer:
    """Two 16-head layers by default; consumes and predicts complete latents."""

    def __init__(self, projection=None, *, layers=None, context_size=256, num_layers=2, num_heads=16, top_k=10,
                 features=None):
        if type(context_size) is not int or context_size < 1 or type(top_k) is not int or top_k < 1:
            raise ValueError("context_size and top_k must be positive")
        if type(num_layers) is not int or num_layers < 0:
            raise ValueError("num_layers must be nonnegative")
        self.projection = projection if projection is not None else GrammarProjection()
        self.layers = tuple(layers) if layers is not None else tuple(StoryformerBlock(num_heads=num_heads) for _ in range(num_layers))
        self.context_size, self.top_k = context_size, top_k
        if features is not None and not isinstance(features, dict):
            raise ValueError("features must be a registry object")
        canonical(features or {})
        self.features = deepcopy(features or {})

    @staticmethod
    def _prepare(latents):
        from .positions import add_positions

        rows = [complete(row) for row in latents]
        if rows and not all(isinstance(row.get("position"), dict) for row in rows):
            rows = add_positions(rows)
        return rows

    def _run(self, latents):
        history = self._prepare(latents)
        offset = max(0, len(history) - self.context_size)
        stream = [Residual.from_latent(row) for row in history[offset:]]
        trace = []
        for index, layer in enumerate(self.layers):
            stream, events = layer.forward(stream)
            trace.extend({"layer": index, **event} for event in events)
        return history, stream, trace

    def forward(self, latents):
        history, stream, trace = self._run(latents)
        offset = max(0, len(history) - self.context_size)
        views = [row.view() for row in stream]
        predictions = [self.projection.read(views[:i + 1], self.top_k, position_context=history[:offset + i + 1])
                       for i in range(len(views))]
        last = predictions[-1] if predictions else self.projection.read([], self.top_k)
        return GrammarForward(views, stream, predictions, last, trace)

    def predict(self, latents):
        history, stream, _trace = self._run(latents)
        return self.projection.read([row.view() for row in stream], self.top_k, position_context=history)

    def generate(self, context, steps, *, seed=0):
        if type(steps) is not int or steps < 0:
            raise ValueError("steps must be nonnegative")
        history, rng = self._prepare(context), random.Random(seed)
        for _ in range(steps):
            latent = self.predict(history).sample(rng)
            history.append(latent)
            if latent["token"] == "<END>":
                break
        return history

    def examples(self, documents):
        for document in documents:
            rows = self._prepare(document)
            for i, target in enumerate(rows):
                yield rows[max(0, i - self.context_size):i], target

    def loss(self, documents):
        losses = []
        for context, target in self.examples(documents):
            p = self.predict(context).probability(target)
            losses.append(-math.log(p) if p else math.inf)
        return math.fsum(losses) / len(losses) if losses else 0.

    def fit(self, documents, *, epochs=1, learning_rate=.1):
        """Exact log-weight gradients for fixed output grammars and full targets.

        Structure, head grammars and head strengths remain authored. No target
        enters the blocks, and training uses all joint candidates before top-k.
        """
        positive(learning_rate, "learning rate")
        if type(epochs) is not int or epochs < 1:
            raise ValueError("epochs must be positive")
        head_rules = {id(rule) for layer in self.layers for head in layer.heads if head is not None
                      for rule in head.neuron.rules}
        if any(id(rule) in head_rules for neuron in self.projection.neurons.values() for rule in neuron.rules):
            raise ValueError("output-weight training requires parameters separate from attention-head rules")
        examples = list(self.examples(documents))
        for _ in range(epochs):
            for context, target in examples:
                _history, stream, _trace = self._run(context)
                processed = [row.view() for row in stream]
                active = self.projection.activations(processed)
                total = math.fsum(match.mass for _, _, match, _ in active)
                expected = semantic(target)
                good = [row for row in active if all(canonical(row[3].get(k)) == canonical(v) for k, v in expected.items())]
                correct = math.fsum(match.mass for _, _, match, _ in good)
                if not correct:
                    raise ValueError(f"target outside output grammar support: {target['token']!r}")
                gradients, rules = defaultdict(float), {}
                for group, denominator, sign in ((active, total, -1), (good, correct, 1)):
                    for _word, neuron, match, _latent in group:
                        rule = neuron.rules[match.rule]
                        rules[id(rule)] = rule
                        gradients[id(rule)] += sign * match.mass / denominator
                for identity, gradient in gradients.items():
                    rule = rules[identity]
                    rule.weight = math.exp(max(-60., min(60., math.log(rule.weight) + learning_rate * gradient)))
        return self

    def save(self, path):
        payload = dict(format="storyformer-grammar-v1", context_size=self.context_size, top_k=self.top_k,
                       definition=pack(dict(projection=self.projection, layers=self.layers)), features=self.features)
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text())
        if data.get("format") != "storyformer-grammar-v1":
            raise ValueError("unsupported grammar checkpoint")
        definition = unpack(data["definition"])
        return cls(**definition, context_size=data["context_size"], top_k=data["top_k"], features=data.get("features"))
