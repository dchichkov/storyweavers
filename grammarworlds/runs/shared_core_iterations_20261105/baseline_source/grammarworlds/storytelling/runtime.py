"""Sample words (including speech punctuation); commit every physical event.

Unnarrated operations have an empty surface and an END transition. They retain
their original probability, guards, effects and history entry. This is semantic
content selection, never deletion or rewriting of generated prose.
"""
from dataclasses import asdict
import hashlib
import math
import random

from ..engine import score_frame, softmax
from ..grammar import Derivation, Forest, expand, text
from ..world import Frame
from ..portable.runtime import setup as portable_setup
from . import library_world, pottery_world, rescue_world, kite_world, key_world, music_world, greenhouse_world
from .plans import plan
from .surface import detokenize

SCENARIOS = ("rescue", "kite", "key", "music", "greenhouse", "library", "pottery")


def setup(scenario, seed=0, **options):
    if scenario == "rescue":
        return rescue_world, rescue_world.make_world(seed, **options)
    if scenario == "kite":
        return kite_world, kite_world.make_world(seed, **options)
    if scenario == "key":
        return key_world, key_world.make_world(seed, **options)
    if scenario == "music":
        return music_world, music_world.make_world(seed, **options)
    if scenario == "greenhouse":
        return greenhouse_world, greenhouse_world.make_world(seed, **options)
    if scenario in {"library", "pottery"}:
        pack = library_world if scenario == "library" else pottery_world
        return pack, pack.make_world(seed, **options)
    return portable_setup("heldout" if scenario == "greenhouse" else scenario, seed, **options)


def build_forest(pack, world, tense="past", *, attention=True, temperature=1, continuations="original"):
    before = world.to_dict()
    available = pack.candidates(world)
    if not available:
        raise ValueError("no available event")
    evidence = [score_frame(world, k, attention=attention) for k, _ in available]
    priors = softmax([e["logit"] for e in evidence], temperature)
    rows, scenes = [], {}
    for (_, f), prior, item in zip(available, priors, evidence):
        rendered = plan(world, f, tense, getattr(pack, "LEXICON", None), continuations=continuations)
        scenes[f] = rendered
        branches = list(expand(rendered.node if rendered else text("")))
        if not 0 < len(branches) <= 512 or not math.isclose(sum(p for _, p, _ in branches), 1, abs_tol=1e-9):
            raise AssertionError("unnormalized or oversized grammar")
        for tokens, probability, labels in branches:
            rows.append(Derivation(tokens, prior * probability, f, labels))
        item.update(frame=asdict(f), prior_probability=prior)
    assert before == world.to_dict(), "prediction mutated state"
    return Forest(rows, {str(i): e for i, e in enumerate(evidence)}), scenes


def generate(scenario="music", seed=7, *, tense="past", attention=True, temperature=1,
             symbolic_heads=False, head_profile="manual", head_strength=1.0,
             head_ids=None, continuations="original", **options):
    if scenario not in SCENARIOS or tense not in {"past", "present"}:
        raise ValueError("unknown scenario or tense")
    pack, w = setup(scenario, seed, **options)
    from .head_adapter import StoryHeads
    heads = StoryHeads(w, profile=head_profile, strength=head_strength, head_ids=head_ids) if symbolic_heads else None
    initial = w.to_dict()
    rng, scenes, traces = random.Random(seed), [], []
    offset = 0
    for _ in range(32):
        if w.finished:
            break
        forest, plans = build_forest(pack, w, tense, attention=attention, temperature=temperature,
                                    continuations=continuations)
        available = pack.candidates(w) if heads else None
        tokens, trace = (), []
        for _ in range(max(len(d.tokens) for d in forest.derivations) + 1):
            prediction = (heads.predict(forest, tokens, w, tense=tense, available=available)
                          if heads else forest.predict(tokens))
            choices = prediction["choices"]
            assert math.isclose(sum(c["probability"] for c in choices), 1, abs_tol=1e-9)
            chosen = rng.choices(choices, weights=[c["probability"] for c in choices])[0]
            prediction.update(selected=chosen["word"], selected_probability=chosen["probability"])
            trace.append(prediction)
            if chosen["word"] == "<END>":
                break
            tokens += (chosen["word"],)
        else:
            raise AssertionError("word sampling did not finish")
        posterior = forest.event_posterior(tokens)
        # Head factors depend only on the observed prefix and committed world,
        # so every derivation of this text receives the same product of factors.
        # They cancel in the conditional posterior over its possible frames.
        frame = rng.choices(list(posterior), weights=list(posterior.values()))[0]
        matches = [d for d in forest.derivations if d.frame == frame and d.tokens == tokens]
        labels = sorted(set.intersection(*(set(d.rules) for d in matches)))
        expected = sum(d.probability for d in forest.derivations if d.tokens == tokens)
        probability = math.prod(p["selected_probability"] for p in trace)
        if not heads or head_strength == 0:
            assert math.isclose(probability, expected, rel_tol=1e-8)
        prose = detokenize(tokens)
        event = pack.commit(w, frame, prose)
        event["referents"] = sorted({r.split(":", 1)[1] for r in labels if r.startswith("referent:")})
        event["speakers"] = sorted({r.split(":", 1)[1] for r in labels if r.startswith("dialogue.speaker:")})
        event["narrated"] = bool(prose)
        if prose:
            if scenes:
                offset += 1
            scenes.append(dict(event_id=event["id"], frame=asdict(frame), text=prose,
                start=offset, end=offset + len(prose), claims=plans[frame].claims,
                speakers=event["speakers"], rules=labels))
            offset += len(prose)
        traces.append(dict(event_id=event["id"], frame=asdict(frame), narrated=bool(prose),
                           probability=probability, grammar_probability=expected,
                           grammar_derivations=len(forest.derivations),
                           grammar_surfaces=len({d.tokens for d in forest.derivations}),
                           word_trace=trace, event_evidence=forest.evidence))
    if not w.finished:
        raise AssertionError("world did not finish within 32 events")
    story = " ".join(s["text"] for s in scenes)
    return dict(scenario=scenario, seed=seed, tense=tense, options=options, story=story,
        attention=attention, temperature=temperature, continuations=continuations,
        symbolic_heads=heads.metadata() if heads else None,
        text_sha256=hashlib.sha256(story.encode()).hexdigest(), scenes=scenes,
        initial_world=initial, final_world=w.to_dict(), trace=traces)


def replay(row):
    pack, w = setup(row["scenario"], row["seed"], **row.get("options", {}))
    assert w.to_dict() == row["initial_world"]
    for saved in row["final_world"]["history"]:
        f = Frame(**{**saved["frame"], "cause_ids": tuple(saved["frame"]["cause_ids"])})
        assert w.snapshot() == saved["before"]
        record = pack.commit(w, f, saved["sentence"])
        for key in ("referents", "speakers", "narrated"):
            record[key] = saved[key]
        assert w.snapshot() == saved["after"]
    assert w.to_dict() == row["final_world"]
    return True
