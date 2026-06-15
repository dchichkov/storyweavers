#!/usr/bin/env python3
"""
storyworlds/asp.py
==================

Shared clingo (Answer-Set Programming) helper for the storyworld scripts.

This is one of the two *common* modules (alongside ``results.py``); everything
else for a given world -- prose, registries, AND the ASP rules (inline, under a
``ASP_RULES`` string) -- lives in that world's single file.  The world emits ASP
*facts* from its registries, concatenates them with its inline rules, and uses
the helpers here to solve and read back the model.

Only imported when an ASP mode is actually used, so the prose engine still runs
without clingo installed.
"""
from __future__ import annotations

import os

import clingo


def load_rules(path: str) -> str:
    """Read a standalone ``.lp`` rule file (kept for file-based rule sets;
    the bundled worlds inline their rules in an ``ASP_RULES`` string instead)."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def term(value) -> str:
    """Render a Python value as an ASP term (integer, constant, or string)."""
    if isinstance(value, bool):
        raise TypeError("model booleans as the presence/absence of a fact")
    if isinstance(value, int):
        return str(value)
    s = str(value)
    if s and (s[0].islower() or s[0] == "_") and all(c.isalnum() or c == "_" for c in s):
        return s                       # already a safe ASP constant
    return f'"{s}"'                    # otherwise fall back to a quoted string


def fact(name: str, *args) -> str:
    """Build a ground ASP fact, e.g. ``fact("affords", "park", "rain")``."""
    if not args:
        return f"{name}."
    return f"{name}({','.join(term(a) for a in args)})."


def solve(program: str, models: int = 0) -> list[list[clingo.Symbol]]:
    """Ground + solve a program; return a list of models (shown atoms each).

    ``models=0`` enumerates every answer set; ``models=1`` returns the first.
    """
    ctl = clingo.Control([f"--models={models}", "--warn=none"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    out: list[list[clingo.Symbol]] = []
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            out.append(list(model.symbols(shown=True)))
    return out


def one_model(program: str) -> list[clingo.Symbol]:
    """Solve for a single model (our rule sets are deterministic in this mode)."""
    models = solve(program, models=1)
    return models[0] if models else []


def _py(sym: clingo.Symbol):
    if sym.type == clingo.SymbolType.Number:
        return sym.number
    if sym.type == clingo.SymbolType.String:
        return sym.string
    return sym.name                    # a constant -> its name


def atoms(symbols: list[clingo.Symbol], name: str) -> list[tuple]:
    """Argument tuples of every shown atom whose predicate is ``name``."""
    res = []
    for sym in symbols:
        if sym.name == name:
            res.append(tuple(_py(a) for a in sym.arguments))
    return res
