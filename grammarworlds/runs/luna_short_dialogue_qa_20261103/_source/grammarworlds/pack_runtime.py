"""Evaluate authored packs with the existing word sampler primitives, unchanged.

This experimental adapter never invokes a model. Pack code is loaded only by
the isolated authoring-trial worker, not by ordinary grammarworlds generation.
"""
from copy import deepcopy
from dataclasses import asdict
from itertools import islice
import math
import random

from .engine import score_frame, softmax
from .grammar import Derivation, Forest, detokenize, expand
from .world import Frame, Kernel, World


def build_forest(pack, world):
    before = deepcopy(world.to_dict())
    candidates = pack.candidates(world)
    assert world.to_dict() == before, "candidates mutated world"
    assert candidates, "unfinished world has no candidates"
    assert len({frame for _, frame in candidates}) == len(candidates), "duplicate candidate frames"
    evidence, logits = {}, []
    for kernel, frame in candidates:
        assert isinstance(kernel, Kernel) and isinstance(frame, Frame), "wrong candidate types"
        assert kernel.name == frame.kind, "kernel/frame names differ"
        assert kernel.requires <= world.flags and not kernel.excludes & world.flags, "kernel flag guard violated"
        for entity in (frame.actor, frame.patient, frame.instrument):
            assert not entity or entity in world.entities, f"unknown entity: {entity}"
        valid_causes = set(world.facts) | {f.id for f in world.facts_for_attention()}
        assert set(frame.cause_ids) <= valid_causes, f"unknown cause IDs: {frame.cause_ids}"
        value = score_frame(world, kernel)
        assert math.isfinite(value["logit"]), "nonfinite event logit"
        evidence[kernel.name] = value
        logits.append(value["logit"])
    priors = softmax(logits)
    derivations = []
    for (kernel, frame), prior in zip(candidates, priors):
        rows = list(islice(expand(pack.realize(world, frame, "past")), 513))
        assert 0 < len(rows) <= 512, "frame expansion must contain 1-512 derivations"
        assert math.isclose(sum(p for _, p, _ in rows), 1, abs_tol=1e-9), "grammar mass not normalized"
        for tokens, probability, rules in rows:
            assert 0 < len(tokens) <= 120, "derivation length outside 1-120 tokens"
            assert math.isfinite(probability) and probability > 0, "invalid grammar probability"
            derivations.append(Derivation(tokens, prior * probability, frame, rules))
    assert world.to_dict() == before, "prediction/realization/attention mutated world"
    return Forest(derivations, evidence)


def check_guard_interventions(pack, world, frame):
    checks = 0
    def blocked(changed, kind):
        nonlocal checks
        assert kind not in {f.kind for _, f in pack.candidates(changed)}, f"{kind} survives broken physical/consent guard"
        checks += 1
    if frame.kind == "join":
        changed = world.clone()
        changed.entities["partner"].state.discard("consented")
        blocked(changed, "join")
        changed = world.clone()
        changed.entities["spare"].location = "shelf"
        blocked(changed, "join")
        changed = world.clone()
        changed.entities["partner"].location = "outside"
        blocked(changed, "join")
    elif frame.kind == "perform":
        changed = world.clone()
        changed.entities["drum"].location = "shelf"
        blocked(changed, "perform")
        changed = world.clone()
        changed.entities["program"].state.discard("solo")
        blocked(changed, "perform")
    elif frame.kind == "ending":
        for name, carrier in (("drum", "hero"), ("spare", "partner")):
            changed = world.clone()
            changed.entities[name].location = carrier
            blocked(changed, "ending")
    return checks


def sample(pack, seed, *, partner_willing=None, interventions=False):
    world = pack.make_world(seed, partner_willing=partner_willing)
    assert isinstance(world, World), "make_world must return World or subclass"
    assert {"hero", "partner", "teacher", "drum", "spare", "program"} <= set(world.entities)
    assert not world.finished and not world.history, "world starts resolved"
    assert not {"consented", "joined"} & world.entities["partner"].state, "initial consent/join is not allowed"
    assert all(world.entities[k].location == "shelf" for k in ("drum", "spare")), "instruments must start on shelf"
    initial = deepcopy(world.to_dict())
    before = deepcopy(world.to_dict())
    try:
        pack.commit(world, Frame("__forged__", "hero"), "Must be rejected.")
    except ValueError:
        pass
    else:
        raise AssertionError("forged frame accepted")
    assert world.to_dict() == before, "failed commit mutated world"
    rng, sentences, steps, checks = random.Random(seed), [], [], 0
    for index in range(24):
        if world.finished:
            break
        forest = build_forest(pack, world)
        if interventions:
            for frame in {d.frame for d in forest.derivations}:
                checks += check_guard_interventions(pack, world, frame)
        tokens, probabilities = (), []
        for _ in range(121):
            prediction = forest.predict(tokens)
            choices = prediction["choices"]
            assert choices and math.isclose(sum(c["probability"] for c in choices), 1, abs_tol=1e-9)
            assert all(math.isfinite(c["probability"]) and c["probability"] > 0 for c in choices)
            selected = rng.choices(choices, weights=[c["probability"] for c in choices])[0]
            probabilities.append(selected["probability"])
            steps.append(dict(event=index, prefix=list(tokens), selected=selected["word"],
                              choices=[dict(word=c["word"], probability=c["probability"]) for c in choices]))
            if selected["word"] == "<END>":
                break
            tokens += (selected["word"],)
        else:
            raise AssertionError("sentence failed to stop")
        posterior = forest.event_posterior(tokens)
        assert posterior, "no interpretation for sampled words"
        frame = rng.choices(list(posterior), weights=list(posterior.values()))[0]
        assert math.isclose(math.prod(probabilities), sum(d.probability for d in forest.derivations if d.tokens == tokens), rel_tol=1e-8)
        before = deepcopy(world.snapshot())
        partner = world.entities["partner"]
        if frame.kind == "join":
            assert "consented" in partner.state, "joined without consent"
            assert partner.location == world.entities["hero"].location, "remote partner joined"
            assert world.entities["spare"].location == "partner", "joined without held instrument"
            assert partner_willing is not False, "unwilling partner joined"
        if frame.kind == "perform":
            assert world.entities["drum"].location == "hero" and "solo" in world.entities["program"].state
        if frame.kind == "ending":
            assert any(s["frame"]["kind"] == "perform" for s in sentences), "ending before performance"
            assert all(world.entities[k].location == "shelf" for k in ("drum", "spare")), "ending before instrument return"
        text = detokenize(tokens)
        record = pack.commit(world, frame, text)
        assert len(world.history) == index + 1 and world.history[-1] == record, "history contract violated"
        assert record["before"] == before and record["after"] == world.snapshot(), "recorded state differs from execution"
        assert record["frame"] == asdict(frame) and record["sentence"] == text and record["id"] == index + 1
        for state, required_kind in (("consented", "consent"), ("joined", "join")):
            if state not in before["entities"]["partner"]["state"] and state in partner.state:
                assert frame.kind == required_kind and frame.actor == "partner", f"{state} assigned by wrong event/actor"
        sentences.append(dict(text=text, frame=asdict(frame), probability=math.prod(probabilities),
                              before=before, after=deepcopy(world.snapshot())))
    assert world.finished, "story did not end within 24 events"
    assert not pack.candidates(world), "ended world still offers events"
    assert any(s["frame"]["kind"] == "perform" for s in sentences), "no public performance"
    assert all(world.entities[k].location == "shelf" for k in ("drum", "spare"))
    assert partner_willing is not False or "joined" not in world.entities["partner"].state
    return dict(seed=seed, partner_willing=partner_willing, story=" ".join(s["text"] for s in sentences),
        frames=[s["frame"] for s in sentences], sentences=sentences, initial_world=initial,
        final_world=world.to_dict(), joined="joined" in world.entities["partner"].state,
        event_count=len(sentences), word_count=sum(len(s["text"].split()) for s in sentences),
        guard_interventions=checks, prediction_steps=len(steps),
        branching_steps=sum(len(s["choices"]) > 1 for s in steps), word_trace=steps)


def replay(pack, row):
    """Reexecute semantic frames without resampling or consulting prose content."""
    world = pack.make_world(row["seed"], partner_willing=row["partner_willing"])
    assert world.to_dict() == row["initial_world"], "initial world does not reproduce"
    for sentence in row["sentences"]:
        frame = Frame(**{**sentence["frame"], "cause_ids": tuple(sentence["frame"]["cause_ids"])})
        assert frame in [f for _, f in pack.candidates(world)], "saved frame cannot replay"
        assert world.snapshot() == sentence["before"], "replay before-state differs"
        pack.commit(world, frame, sentence["text"])
        assert world.snapshot() == sentence["after"], "replay after-state differs"
    assert world.to_dict() == row["final_world"], "replay final world differs"
