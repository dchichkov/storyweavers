"""Shared, standard-library-only scene constraint engine. No prose or API calls.

Definitions are immutable. A run owns its state, usage counts and causal trace.
State keys name physical carriers (``bell.ringing``, ``ada.memes.Curiosity``).
Scenes compose through these keys, not through fixed previous/next scene IDs.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import math
import operator
import random


class StoryError(ValueError):
    pass


@dataclass(frozen=True)
class Condition:
    key: str
    op: str
    value: object


@dataclass(frozen=True)
class Effect:
    key: str
    value: object
    op: str = "set"  # set / inc / copy (value is a source state key)


@dataclass(frozen=True)
class Scene:
    id: str
    kernel: str
    actors: tuple[str, ...]
    requires: tuple[Condition, ...]
    effects: tuple[Effect, ...]
    summary: str
    weight: float = 1.0
    max_uses: int = 1
    pivotal: bool = False


@dataclass(frozen=True)
class Rule:
    name: str
    must: tuple[Condition, ...]
    when: tuple[Condition, ...] = ()


@dataclass(frozen=True)
class WorldSpec:
    title: str
    entities: dict[str, dict]  # id -> {name, kind}; state is below
    initial: dict
    scenes: tuple[Scene, ...]
    goal: tuple[Condition, ...]
    rules: tuple[Rule, ...] = ()
    labels: dict[str, str] | None = None
    prune: bool = False
    premise_keys: tuple[str, ...] = ()
    outcome_keys: tuple[str, ...] = ()


OPS = {"eq": operator.eq, "ne": operator.ne, "gt": operator.gt,
       "ge": operator.ge, "lt": operator.lt, "le": operator.le,
       "in": lambda a, b: a in b, "not_in": lambda a, b: a not in b}


def holds(state, conditions):
    for c in conditions:
        if c.key not in state or c.op not in OPS:
            raise StoryError(f"Unknown condition: {c}")
        try:
            if state[c.key] is None and c.op in ("gt", "ge", "lt", "le"):
                return False  # an unobserved value cannot pass a numeric guard
            if not OPS[c.op](state[c.key], c.value):
                return False
        except (TypeError, ValueError) as exc:
            raise StoryError(f"Invalid condition {c}: {exc}") from exc
    return True


def check_rules(state, rules):
    return [r.name for r in rules if holds(state, r.when) and not holds(state, r.must)]


def transition(state, scene, rules=()):
    """Apply effects atomically. Copies read the pre-state; illegal moves fail closed."""
    if not holds(state, scene.requires):
        return None
    after = deepcopy(state)
    for effect in scene.effects:
        if effect.key not in state:
            raise StoryError(f"Undeclared effect key: {effect.key}")
        if effect.op == "set":
            after[effect.key] = deepcopy(effect.value)
        elif effect.op == "copy":
            if effect.value not in state:
                raise StoryError(f"Undeclared copy source: {effect.value}")
            after[effect.key] = deepcopy(state[effect.value])
        elif effect.op == "inc":
            if type(state[effect.key]) not in (int, float) or type(effect.value) not in (int, float):
                raise StoryError(f"Non-numeric increment: {effect.key}")
            after[effect.key] = state[effect.key] + effect.value
        else:
            raise StoryError(f"Unknown effect operation: {effect.op}")
    return None if after == state or check_rules(after, rules) else after


def observe(scene_id, actor, fact, *, requires=(), summary=""):
    """Bind the Observe kernel to a carrier and a physical fact. No invented knowledge."""
    return Scene(scene_id, "Observe", (actor,), tuple(requires),
                 (Effect(f"{actor}.knows.{fact}", fact, "copy"),), summary)


def tell(scene_id, speaker, listener, fact, *, requires=(), summary=""):
    """Transmit the speaker's stored belief, which may become stale later."""
    key = f"{speaker}.knows.{fact}"
    return Scene(scene_id, "Tell", (speaker, listener),
                 (Condition(key, "ne", None),) + tuple(requires),
                 (Effect(f"{listener}.knows.{fact}", key, "copy"),), summary)


def transfer(scene_id, actor, recipient, prop, *, requires=(), summary=""):
    """One ownership slot, so transfer cannot duplicate a prop."""
    return Scene(scene_id, "Transfer", (actor, recipient),
                 (Condition(f"{prop}.owner", "eq", actor),) + tuple(requires),
                 (Effect(f"{prop}.owner", recipient),), summary)


def scene(scene_id, kernel, actors, *, when=(), set_values=None, increments=None,
          copies=None, summary="", weight=1.0, max_uses=1, pivotal=False):
    """Keyword authoring API: operations cannot be confused with their values."""
    effects = tuple(Effect(k, v) for k, v in (set_values or {}).items())
    effects += tuple(Effect(k, v, "inc") for k, v in (increments or {}).items())
    effects += tuple(Effect(k, v, "copy") for k, v in (copies or {}).items())
    return Scene(scene_id, kernel, tuple(actors), tuple(when), effects, summary,
                 weight, max_uses, pivotal)


def validate_spec(spec):
    if not isinstance(spec, WorldSpec) or not spec.entities or not spec.goal:
        raise StoryError("A world requires entities and a nonempty goal")
    errors = []
    if len({s.id for s in spec.scenes}) != len(spec.scenes):
        errors.append("Duplicate scene IDs")
    for key, value in spec.initial.items():
        if key.split(".")[0] not in spec.entities:
            errors.append(f"Unembedded state: {key}")
        if value is not None and type(value) not in (str, bool, int, float):
            errors.append(f"State values must be scalar: {key}")
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"Nonfinite state: {key}")
    conditions = list(spec.goal)
    for key in spec.premise_keys + spec.outcome_keys:
        if key not in spec.initial:
            errors.append(f"Unknown narrative state key: {key}")
    for rule in spec.rules:
        conditions += list(rule.when) + list(rule.must)
    for s in spec.scenes:
        if not s.actors or any(a not in spec.entities for a in s.actors):
            errors.append(f"Scene {s.id} has no valid physical carrier")
        if not s.effects or s.weight <= 0 or not math.isfinite(s.weight) or s.max_uses < 1:
            errors.append(f"Invalid scene: {s.id}")
        if len({e.key for e in s.effects}) != len(s.effects):
            errors.append(f"Conflicting simultaneous effects: {s.id}")
        conditions += list(s.requires)
        for e in s.effects:
            if e.key not in spec.initial or e.op not in ("set", "inc", "copy"):
                errors.append(f"Undeclared or invalid effect: {s.id}: {e}")
            if e.op == "copy" and e.value not in spec.initial:
                errors.append(f"Unknown copy source: {e.value}")
    # Check EVERY condition, even those behind an earlier false condition.
    for c in conditions:
        if c.key not in spec.initial or c.op not in OPS:
            errors.append(f"Unknown condition: {c}")
    if errors:
        raise StoryError("Invalid world specification:\n" + "\n".join(errors))
    failed = check_rules(spec.initial, spec.rules)
    if failed:
        raise StoryError(f"Invalid initial world: {failed}")
    if holds(spec.initial, spec.goal):
        raise StoryError("Goal already satisfied; no story problem")


def solve(spec, seed=0, *, max_steps=20, max_nodes=6000):
    """Seeded bounded DFS chooses a valid composition reaching the world goal.

    Backtracking happens BEFORE narration. No rejected move is a fictional event.
    This is author-side planning with full state, not an omniscient character.
    Character knowledge must still be expressed in each action's preconditions.
    """
    validate_spec(spec)
    rng = random.Random(seed)
    seen, nodes, pruned = set(), 0, 0

    def visit(state, counts, path):
        nonlocal nodes, pruned
        nodes += 1
        if nodes > max_nodes:
            raise StoryError(f"Search budget exhausted ({max_nodes} nodes)")
        if holds(state, spec.goal):
            return path
        remaining = max_steps - len(path)
        signature = json.dumps([state, counts, remaining], sort_keys=True)
        if remaining <= 0 or signature in seen:
            return None
        seen.add(signature)
        candidates = []
        for s in spec.scenes:
            if counts.get(s.id, 0) >= s.max_uses:
                continue
            after = transition(state, s, spec.rules)
            if after is not None:
                candidates.append((rng.random() ** (1 / s.weight), s, after))
        candidates.sort(key=lambda x: x[0], reverse=True)
        for _, s, after in candidates:
            new_counts = dict(counts)
            new_counts[s.id] = counts.get(s.id, 0) + 1
            answer = visit(after, new_counts, path + [(s, state, after)])
            if answer is not None:
                return answer
            pruned += 1
        return None

    path = visit(deepcopy(spec.initial), {}, [])
    if path is None:
        raise StoryError("No valid composition reaches the goal")
    discarded = []
    if spec.prune:
        from planning import prune_path
        path, discarded = prune_path(spec, path)
    events, last_writer = [], {}
    for index, (scene, before, after) in enumerate(path, 1):
        reads = {c.key for c in scene.requires}
        reads |= {e.value for e in scene.effects if e.op == "copy"}
        reads |= {e.key for e in scene.effects if e.op == "inc"}
        if spec.prune:
            from planning import rule_reads
            reads |= rule_reads(spec.rules, after)
        changes = {k: {"before": before[k], "after": v} for k, v in after.items() if before[k] != v}
        events.append(dict(id=index, scene=scene.id, kernel=scene.kernel, actors=list(scene.actors),
            summary=scene.summary, causes=sorted({last_writer[k] for k in reads if k in last_writer}),
            requires=[dict(key=c.key, op=c.op, value=c.value) for c in scene.requires],
            changes=changes, before=deepcopy(before), after=deepcopy(after)))
        for key in changes:
            last_writer[key] = index
    result = dict(title=spec.title, seed=seed, entities=deepcopy(spec.entities),
        initial=deepcopy(spec.initial), final=deepcopy(path[-1][2]), events=events,
        labels=deepcopy(spec.labels or {}), search=dict(nodes=nodes, backtracks=pruned),
        goal=[dict(key=c.key, op=c.op, value=c.value) for c in spec.goal])
    if spec.prune:
        result.update(engine="storyscenes_v2", pruned_scenes=discarded,
            premise={k: result["initial"][k] for k in spec.premise_keys},
            outcome={k: result["final"][k] for k in spec.outcome_keys})
    return result


def realize(result, render, prose_seed=0):
    """Accept trace-linked paragraphs; prose may not mutate its simulation input."""
    view = deepcopy(result)
    paragraphs = render(view, random.Random(prose_seed))
    if view != result:
        raise StoryError("Renderer mutated the frozen simulation")
    if not isinstance(paragraphs, list) or len(paragraphs) < 3:
        raise StoryError("Need beginning, scenes and ending paragraphs")
    if paragraphs[0].get("kind") != "beginning" or paragraphs[-1].get("kind") != "ending":
        raise StoryError("Missing beginning or ending")
    valid_ids = {e["id"] for e in result["events"]}
    covered = set()
    for p in paragraphs:
        if set(p) not in ({"text", "event_ids", "kind"}, {"text", "event_ids", "kind", "facts"}) or not isinstance(p["text"], str) or not p["text"].strip():
            raise StoryError("Invalid paragraph")
        if p["kind"] not in ("beginning", "scene", "ending") or not isinstance(p["event_ids"], list):
            raise StoryError("Invalid paragraph kind or evidence")
        if any(type(i) is not int or i not in valid_ids for i in p["event_ids"]):
            raise StoryError("Unknown event cited by prose")
        if p["kind"] != "beginning" and not p["event_ids"]:
            raise StoryError("Scene/ending needs event evidence")
        covered.update(p["event_ids"])
        for fact in p.get("facts", []):
            at = fact.get("at")
            if type(at) is not int or at < 0 or at > len(result["events"]):
                raise StoryError("Unknown fact time")
            state = result["initial"] if at == 0 else result["events"][at - 1]["after"]
            if fact.get("key") not in state or state[fact["key"]] != fact.get("value"):
                raise StoryError(f"Contradicted prose fact: {fact}")
    if covered != valid_ids or result["events"][-1]["id"] not in paragraphs[-1]["event_ids"]:
        raise StoryError("Unnarrated events or ungrounded ending")
    story = "\n\n".join(p["text"].strip() for p in paragraphs)
    return dict(seed=result["seed"], prose_seed=prose_seed, title=result["title"], story=story,
                paragraphs=paragraphs, trace=deepcopy(result), qa=qa_from_trace(result))


def qa_from_trace(result):
    """Mechanical state-audit QA, with evidence. Literary QA is future work."""
    rows = []
    for e in result["events"]:
        parts = []
        for key, values in e["changes"].items():
            label = result["labels"].get(key, key)
            parts.append(f"{label} changed from {json.dumps(values['before'])} to {json.dumps(values['after'])}")
        answer = "; ".join(parts) + "."
        if e["causes"]:
            names = [result["events"][i-1]["summary"] for i in e["causes"]]
            answer += " This used state established when " + "; ".join(names) + "."
        rows.append(dict(question=f"What changed when {e['summary'].rstrip('.')}?",
                         answer=answer, event_ids=[e["id"]], cause_ids=e["causes"]))
    return rows
