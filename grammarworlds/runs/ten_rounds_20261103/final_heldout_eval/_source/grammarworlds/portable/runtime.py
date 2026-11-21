"""Ported rules -> original weighted Forest -> original word sampler semantics."""
from __future__ import annotations

from dataclasses import asdict
import math
import random

from ..engine import score_frame, softmax
from ..grammar import Derivation, Forest, detokenize, expand
from .language import Language
from .worlds import recovery, music

SCENARIOS = ("rescue", "kite", "key", "music")


def setup(scenario, seed, **options):
    if scenario in {"rescue", "kite", "key"}:
        return recovery, recovery.make_world(scenario, seed, **options)
    if scenario == "music":
        return music, music.make_world(seed, **options)
    if scenario == "heldout":
        from .worlds import heldout
        return heldout, heldout.make_world(seed, **options)
    raise ValueError(f"unknown scenario {scenario!r}")


def build_forest(pack, world, *, tense="past", attention=True, temperature=1):
    before = world.to_dict()
    candidates = pack.candidates(world)
    if not candidates:
        raise ValueError("world has ended or has no executable next event")
    if len({f for _, f in candidates}) != len(candidates):
        raise ValueError("duplicate semantic frames")
    evidence = [score_frame(world, k, attention=attention) for k, _ in candidates]
    priors = softmax([e["logit"] for e in evidence], temperature)
    rows = []
    for (kernel, frame), prior, details in zip(candidates, priors, evidence):
        details["prior_probability"] = prior
        details["frame"] = asdict(frame)
        node = Language.utter(pack.plan(world, frame, tense))
        expansion = list(expand(node))
        if not 0 < len(expansion) <= 512:
            raise ValueError("bounded port trial permits 1-512 derivations per frame")
        if not math.isclose(sum(p for _, p, _ in expansion), 1, abs_tol=1e-9):
            raise ValueError("frame grammar mass is not normalized")
        for tokens, probability, rules in expansion:
            rows.append(Derivation(tokens, prior * probability, frame, rules))
    if before != world.to_dict():
        raise AssertionError("prediction mutated physical/discourse state")
    # Frames sharing a kernel (e.g. returning different instruments) retain separate priors.
    return Forest(rows, {str(i): item for i, item in enumerate(evidence)})


def sample_sentence(pack, world, rng, **options):
    forest = build_forest(pack, world, **options)
    tokens, trace = (), []
    for _ in range(max(len(d.tokens) for d in forest.derivations) + 1):
        prediction = forest.predict(tokens)
        choices = prediction["choices"]
        selected = rng.choices(choices, weights=[c["probability"] for c in choices])[0]
        prediction["selected"] = selected["word"]
        prediction["selected_probability"] = selected["probability"]
        trace.append(prediction)
        if selected["word"] == "<END>":
            break
        tokens += (selected["word"],)
    else:
        raise RuntimeError("finite grammar did not complete")
    posterior = forest.event_posterior(tokens)
    frame = rng.choices(list(posterior), weights=list(posterior.values()))[0]
    rows = [d for d in forest.derivations if d.frame == frame and d.tokens == tokens]
    rules = sorted({r for d in rows for r in d.rules})
    sentence = detokenize(tokens)
    event = pack.commit(world, frame, sentence)
    # Register only referents in the chosen surface/interpretation. This records
    # typed rule provenance, never searches the English text for entity names.
    event["referents"] = sorted({r.split(":", 1)[1] for r in rules if r.startswith("referent:")})
    probability = math.prod(p["selected_probability"] for p in trace)
    expected = sum(d.probability for d in forest.derivations if d.tokens == tokens)
    if not math.isclose(probability, expected, rel_tol=1e-8):
        raise AssertionError("word probabilities do not telescope to sentence mass")
    return {"text": sentence, "frame": asdict(frame), "probability": probability,
            "rules": rules, "referents": event["referents"], "derivation_count": len(forest.derivations),
            "event_evidence": forest.evidence, "word_trace": trace}


def generate(scenario="rescue", seed=7, *, tense="past", attention=True, temperature=1, **world_options):
    pack, world = setup(scenario, seed, **world_options)
    initial = world.to_dict()
    rng, sentences = random.Random(seed), []
    for _ in range(24):
        if world.finished:
            break
        sentences.append(sample_sentence(pack, world, rng, tense=tense, attention=attention, temperature=temperature))
    if not world.finished:
        raise RuntimeError("story did not reach an ending within 24 events")
    return {"scenario": scenario, "seed": seed, "tense": tense,
            "grammar": "ported-python", "initial_world": initial, "final_world": world.to_dict(),
            "story": " ".join(s["text"] for s in sentences), "sentences": sentences}
