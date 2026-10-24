#!/usr/bin/env python3
"""Exhaust declared small condition spaces and finite prose choices.

This audit intercepts only the renderer's local random-choice interface. It does
not alter the simulated world or production renderer. Every configuration in
the named audit grid is executed; every choice leaf is rendered, retaining repeats.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import importlib
from itertools import permutations, product
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import harbor_trial as harness


class Branch(Exception):
    def __init__(self, width):
        self.width = width


class Choices:
    def __init__(self, prefix):
        self.prefix, self.index = prefix, 0

    def choice(self, options):
        if self.index == len(self.prefix):
            raise Branch(len(options))
        index = self.prefix[self.index]
        self.index += 1
        return options[index]


def texts(prose, spec, state, config, *, render_name="render"):
    stack, leaves, calls = [()], set(), 0
    while stack:
        prefix = stack.pop()
        calls += 1
        if calls > 10000:
            raise ValueError("Finite prose audit exceeded its explicit per-world bound")
        rng = SimpleNamespace(Random=lambda seed: Choices(prefix))
        with patch.object(prose, "random", rng):
            try:
                leaves.add(getattr(prose, render_name)(spec, state, config, 0).story)
            except Branch as branch:
                stack.extend(prefix + (i,) for i in range(branch.width))
    return leaves


def audit(world):
    module = harness.generator(world)
    prose = importlib.import_module(f"storyscenes.{world}_prose")
    purposes = {"greenhouse": ("water", "support", "light", "leak"), "theater": ("shadow", "cue", "crown")}[world]
    names = [f.name for f in fields(module.Conditions) if f.name != "purpose"]
    if any(type(getattr(module.Conditions(), k)) is not bool for k in names):
        raise ValueError("Audit only covers explicit Boolean condition fields")
    rows, all_texts, all_paths = {}, set(), set()
    count = 0
    for purpose in purposes:
        stories, paths, outcomes = set(), set(), set()
        for values in product((False, True), repeat=len(names)):
            config = module.Conditions(purpose=purpose, **dict(zip(names, values)))
            row, spec, state, _ = module.generate(config=config)
            paths.add(tuple(row["path"]))
            outcomes.add(row["plot"]["outcome"])
            stories.update(texts(prose, spec, state, config))
            count += 1
        rows[purpose] = dict(exact_texts=len(stories), action_paths=len(paths), outcomes=sorted(outcomes))
        all_texts.update(stories)
        all_paths.update(paths)
    return dict(configurations=count, exact_texts=len(all_texts), action_paths=len(all_paths), purposes=rows,
                source_sha256={str(p.relative_to(harness.ROOT.parent)): harness.f.digest(p)
                    for p in (Path(module.__file__), Path(prose.__file__))})


def audit_shared_rope(*, alternatives=False):
    from storyscenes import harbor_story, harbor_interactions, harbor_interaction_prose

    axes = dict(display_ticks=(1, 3, 5), last_launch=(4, 6, 8),
                return_priority=("promise", "display"), direct_path=(False, True), cautious=(False, True))
    if alternatives:
        axes.update(clip_available=(False, True), jetty_board=(False, True),
                    flexible_sailing=(False, True), basin_available=(False, True))
    stories, paths, rows = set(), set(), []
    for values in product(*axes.values()):
        conditions = dict(zip(axes, values))
        config = harbor_story.Conditions(purpose="shared_rope", **conditions)
        row, spec, state, _ = harbor_story.generate(config=config)
        variants = texts(harbor_interaction_prose, spec, state, config, render_name="render_shared_rope")
        stories.update(variants)
        paths.add(tuple(row["path"]))
        rows.append(dict(conditions=conditions, plot=row["plot"], texts=len(variants),
                         trace_sha256=row["trace_sha256"]))
    return dict(scope=f"Shared-rope {len(axes)}-axis grid; other conditions at defaults. Not the entire harbor generator.",
                axes=axes, configurations=len(rows), exact_texts=len(stories), action_paths=len(paths),
                outcomes=sorted({r["plot"]["outcome"] for r in rows}), cases=rows,
                source_sha256={str(Path(m.__file__).relative_to(harness.ROOT.parent)): harness.f.digest(Path(m.__file__))
                    for m in (harbor_story, harbor_interactions, harbor_interaction_prose)})


def composition_axes(*, tradeoffs=False):
    axes = dict(priorities=tuple(permutations(("chart", "lamp", "boat"))),
                supports=tuple(permutations(("rope", "clip", "board"))),
                clip=(False, True), board=(False, True),
                dark_launch=(False, True), light_window=(False, True))
    if tradeoffs:
        axes.update(hold_cover=(False, True), keep_launch_light=(False, True))
    return axes


def audit_composition(*, tradeoffs=False):
    from collections import Counter
    from math import prod
    from storyscenes import goal_planning, harbor_composition_story, harbor_composition_prose
    from storyscenes.capabilities.codec import dumps, loads
    from storyscenes.capabilities.core import replay

    world = "harbor_tradeoffs" if tradeoffs else "harbor_composition"
    module = harness.generator(world)
    prose = importlib.import_module(f"storyscenes.{world}_prose")
    source_files = {Path(m.__file__) for m in
                    (module, prose, goal_planning, harbor_composition_story, harbor_composition_prose)}
    source_files.add(Path(__file__))
    source_files = sorted(source_files)
    hashes = {str(p.relative_to(harness.ROOT.parent)): harness.f.digest(p) for p in source_files}
    axes = composition_axes(tradeoffs=tradeoffs)
    total = prod(len(v) for v in axes.values())
    stories, paths, rows, failures = set(), set(), [], []
    for index, values in enumerate(product(*axes.values()), 1):
        conditions = dict(zip(axes, values))
        try:
            row, spec, state, doc = module.generate(config=module.Conditions(**conditions))
            if replay(module.registry(), loads(module.registry(), dumps(spec)), row["path"]) != state:
                raise ValueError("Serialized world did not exactly replay")
            stories.add(row["story"])
            paths.add(tuple(row["path"]))
            rows.append(dict(conditions=row["conditions"], plot=row["plot"], trace_sha256=row["trace_sha256"],
                             story_sha256=harness.trial.fingerprint(row["story"]),
                             attempted_actions=row["planning"]["attempted_actions"]))
        except Exception as exc:
            failures.append(dict(conditions=conditions, error=f"{type(exc).__name__}: {exc}"))
        if index % 100 == 0:
            print(f"{world} audit: {index}/{total} configurations; {len(failures)} failures", flush=True)
    if hashes != {str(p.relative_to(harness.ROOT.parent)): harness.f.digest(p) for p in source_files}:
        raise ValueError("Composition sources changed during the audit")
    return dict(scope=f"Full declared {world} condition space; deterministic prose, no synonym sampling. Failed cases retained.",
                axes=axes, configurations=total, returned=len(rows), serialized_replays=len(rows),
                failures=failures, exact_texts=len(stories), action_paths=len(paths),
                plot_signatures=len({harness.trial.fingerprint(r["plot"]) for r in rows}),
                outcomes=dict(Counter(r["plot"]["outcome"] for r in rows)),
                max_attempted_actions=max((r["attempted_actions"] for r in rows), default=0),
                cases=rows, source_sha256=hashes)


def question_axes():
    from storyscenes.harbor_questions_story import KINDS
    return dict(kind=KINDS, actual=(False, True), readable=(False, True), reported=(False, True),
                prior_commitment=(False, True), keep_promise_first=(False, True), attempt_first=(False, True), recover=(False, True))


def audit_questions():
    return audit_declared_grid("harbor_questions", question_axes(),
        "Full declared harbor_questions space: four premises, inspection/attempt ordering and prior promises; deterministic prose. Failed cases retained.")


def favor_axes():
    from storyscenes.harbor_favors_story import ACTORS, KINDS, POLICIES
    return dict(projects=tuple(permutations(KINDS)), owners=tuple(permutations(ACTORS)),
                policies=tuple(product(POLICIES, repeat=3)))


def audit_favors():
    return audit_declared_grid("harbor_favors", favor_axes(),
        "972-configuration permutation subspace: each project type and tool owner appears once. "
        "All 27 policy triples; NOT the full 19,683-configuration space, which permits repeats.")


def audit_declared_grid(world, axes, scope):
    from collections import Counter
    from math import prod
    from storyscenes.capabilities.codec import dumps, loads
    from storyscenes.capabilities.core import replay

    module = harness.generator(world)
    files = dict(harness.sources(world), audit=Path(__file__))
    hashes = {name: harness.f.digest(path) for name, path in files.items()}
    total = prod(len(v) for v in axes.values())
    rows, failures, stories, paths = [], [], set(), set()
    for index, values in enumerate(product(*axes.values()), 1):
        conditions = dict(zip(axes, values))
        try:
            row, spec, state, _ = module.generate(config=module.Conditions(**conditions))
            reg = module.registry()
            if replay(reg, loads(reg, dumps(spec)), row["path"]) != state:
                raise ValueError("Serialized world did not exactly replay")
            rows.append(dict(conditions=conditions, plot=row["plot"], trace_sha256=row["trace_sha256"],
                             story_sha256=harness.trial.fingerprint(row["story"])))
            stories.add(row["story"])
            paths.add(tuple(row["path"]))
        except Exception as exc:
            failures.append(dict(conditions=conditions, error=f"{type(exc).__name__}: {exc}"))
        if index % 100 == 0:
            print(f"{world}: {index}/{total}; {len(failures)} failures", flush=True)
    if hashes != {name: harness.f.digest(path) for name, path in files.items()}:
        raise ValueError("Story sources changed during the audit")
    return dict(scope=scope, axes=axes, configurations=total, returned=len(rows),
                serialized_replays=len(rows), failures=failures, exact_texts=len(stories),
                action_paths=len(paths), plot_signatures=len({harness.trial.fingerprint(r["plot"]) for r in rows}),
                outcomes=dict(Counter(r["plot"]["outcome"] for r in rows)), cases=rows, source_sha256=hashes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scope", choices=("replications", "harbor-shared-rope", "harbor-alternatives", "harbor-composition", "harbor-tradeoffs", "harbor-questions", "harbor-favors"), default="replications")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Preserve previous audits; choose a new path")
    results = ({"harbor_favors": audit_favors()} if args.scope == "harbor-favors" else
               {"harbor_questions": audit_questions()} if args.scope == "harbor-questions" else
               {"harbor_tradeoffs": audit_composition(tradeoffs=True)} if args.scope == "harbor-tradeoffs" else
               {"harbor_composition": audit_composition()} if args.scope == "harbor-composition" else
               {w: audit(w) for w in ("greenhouse", "theater")} if args.scope == "replications" else
               {"harbor_shared_rope": audit_shared_rope(alternatives=args.scope == "harbor-alternatives")})
    harness.f.save(args.out, results)
    print(json.dumps({name: {key: value for key, value in result.items() if key != "cases"}
                      for name, result in results.items()}, indent=2))
    if any(result.get("failures") for result in results.values()):
        raise SystemExit("Audit failures preserved; this is not a complete successful condition space")


if __name__ == "__main__":
    main()
