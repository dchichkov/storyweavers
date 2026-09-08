"""Causal relevance and diversity diagnostics, over world traces rather than prose."""
import hashlib
import json
from runtime import holds, transition, StoryError


def rule_reads(rules, after):
    keys = set()
    for rule in rules:
        if holds(after, rule.when):
            keys.update(c.key for c in rule.when + rule.must)
    return keys


def prune_path(spec, path):
    """Backward slice from the goal and explicit character turns, then REPLAY.

    Rule dependencies matter: a reinforcement can enable a later load without
    appearing among that scene's explicit action guards. Kept scenes are never
    merely deleted from an old trace; their pre/post snapshots are re-executed.
    """
    needed = {c.key for c in spec.goal}
    needed.update(spec.outcome_keys)
    selected, discarded = [], []
    for s, before, after in reversed(path):
        writes = {k for k in after if after[k] != before[k]}
        if s.pivotal or writes & needed:
            selected.append(s)
            needed -= writes
            needed.update(c.key for c in s.requires)
            needed.update(e.value for e in s.effects if e.op == "copy")
            needed.update(e.key for e in s.effects if e.op == "inc")
            needed.update(rule_reads(spec.rules, after))
        else:
            discarded.append(s.id)
    state, rebuilt = dict(spec.initial), []
    for s in reversed(selected):
        after = transition(state, s, spec.rules)
        if after is None:
            raise StoryError(f"Causal pruning removed a prerequisite of {s.id}")
        rebuilt.append((s, state, after))
        state = after
    if not rebuilt or not holds(state, spec.goal):
        raise StoryError("Pruned plan did not preserve its goal")
    return rebuilt, list(reversed(discarded))


def signatures(trace):
    """Order-free ancestry signatures. Proxies, not semantic plot judgments."""
    ancestors = {}
    for event in trace["events"]:
        key = [event["kernel"], sorted(ancestors[i] for i in event["causes"])]
        ancestors[event["id"]] = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
    return dict(scene_set=sorted({e["scene"] for e in trace["events"]}),
                causal_graph=sorted(ancestors.values()), outcome=trace.get("outcome", {}))
