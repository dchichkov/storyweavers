"""Execute one generated world without API credentials; used by run.py/factory.py."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import types

import runtime


ALLOWED_IMPORTS = {"__future__", "random", "math", "itertools", "collections", "runtime", "simulation", "prose", "algebra"}
BANNED_CALLS = {"exec", "eval", "open", "compile", "__import__", "globals", "locals", "vars",
                "getattr", "setattr", "delattr", "input", "breakpoint", "print"}


def check_source(source):
    """Accidental I/O/import guard, not a security sandbox for hostile Python."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            if any(n not in ALLOWED_IMPORTS for n in names) or getattr(node, "level", 0):
                raise runtime.StoryError(f"Generated source imports outside the authoring API: {names}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise runtime.StoryError("Generated source uses a dunder attribute")
        if isinstance(node, ast.Name) and (node.id in BANNED_CALLS or node.id.startswith("__") and node.id != "__name__"):
            raise runtime.StoryError(f"Generated source uses a forbidden name: {node.id}")
    return tree


def load(path, name):
    source = path.read_text()
    check_source(source)
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def sample(world, seeds, *, prose=False, prose_seed=None):
    simulation = load(world / "simulation.py", "simulation")
    generator = load(world / "generator.py", "generator") if prose else None
    rows = []
    for seed in seeds:
        try:
            spec = simulation.build(seed)
            trace = runtime.solve(spec, seed)
        except Exception as exc:
            raise runtime.StoryError(f"World {world.name}, seed {seed}: {exc}") from exc
        # Both initialization and search must be deterministic, without global RNG state.
        if trace != runtime.solve(simulation.build(seed), seed):
            raise runtime.StoryError(f"Nondeterministic simulation: seed {seed}")
        if generator:
            ps = seed if prose_seed is None else prose_seed
            row = generator.generate(seed, ps)
            if row.get("trace") != trace:
                raise runtime.StoryError(f"Final generator changed the validated simulation: seed {seed}")
            expected = runtime.realize(trace, generator.render, ps)
            if row != expected:
                raise runtime.StoryError("generate() must use the common realization/QA contract")
        else:
            row = dict(seed=seed, trace=trace)
            if spec.prune:
                row['diagnostics'] = dict(outcome_writes=sorted({e.key for s in spec.scenes for e in s.effects if e.key in spec.outcome_keys}),
                                          candidate_scenes=[s.id for s in spec.scenes])
        row["trace_sha256"] = fingerprint(trace)
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", type=Path)
    parser.add_argument("--seeds", required=True, help="comma-separated integers")
    parser.add_argument("--prose", action="store_true")
    parser.add_argument("--prose-seed", type=int)
    parser.add_argument("--collect-errors", action="store_true")
    args = parser.parse_args()
    seeds = [int(s) for s in args.seeds.split(',')]
    if args.collect_errors:
        for seed in seeds:
            try:
                row = sample(args.world,[seed],prose=args.prose,prose_seed=args.prose_seed)[0]
                row = dict(seed=seed,ok=True)
            except Exception as exc:
                row = dict(seed=seed,ok=False,error=str(exc))
            print(json.dumps(row,ensure_ascii=False))
        return
    for row in sample(args.world, seeds, prose=args.prose, prose_seed=args.prose_seed):
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
