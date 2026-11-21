"""Small searchable authoring contracts; implementations stay outside prompts."""
from __future__ import annotations

import argparse
import inspect
import json

RULES = {}
GF_SOURCE = "https://github.com/GrammaticalFramework/gf-rgl/blob/20260403/src/english/"


def rule(identifier, source_file, source_rule, *, dependencies=(), tags=()):
    def decorate(function):
        RULES[identifier] = {
            "id": identifier, "module": function.__module__,
            "signature": function.__name__ + str(inspect.signature(function)),
            "contract": inspect.getdoc(function) or "",
            "source": GF_SOURCE + source_file if identifier.startswith("gf.") else source_file,
            "source_rule": source_rule, "dependencies": list(dependencies), "tags": list(tags),
        }
        return function
    return decorate


def context(query, *, budget=6000, rules=None):
    """Retrieve contracts plus dependency closure, under a strict character cap.

    A contract that cannot fit with its dependencies is omitted as a whole.
    This searches metadata, not implementation source. Budget is characters,
    not a claimed tokenizer/model context count.
    """
    if budget < 100:
        raise ValueError("context budget must be at least 100 characters")
    entries = RULES if rules is None else rules
    terms = set(query.lower().replace(",", " ").split())
    ranked = []
    for identifier, entry in entries.items():
        haystack = " ".join((identifier, entry["signature"], entry["contract"], *entry["tags"])).lower()
        score = sum(term in haystack for term in terms)
        if score:
            ranked.append((-score, identifier))
    selected, rejected, rendered = {}, [], ""
    def collect(identifier, visiting=None):
        visiting = set() if visiting is None else visiting
        if identifier in visiting:
            raise ValueError(f"cyclic rule dependency: {identifier}")
        entry = entries[identifier]
        found = {}
        for dep in entry["dependencies"]:
            found.update(collect(dep, visiting | {identifier}))
        found[identifier] = entry
        return found
    for _, identifier in sorted(ranked):
        proposal = {**selected, **collect(identifier)}
        candidate = "\n\n".join(f"{e['id']}: {e['signature']}\n{e['contract']}\n"
                                  f"Dependencies: {', '.join(e['dependencies']) or 'none'}"
                                  for e in proposal.values())
        if len(candidate) <= budget:
            selected, rendered = proposal, candidate
        else:
            rejected.append(identifier)
    return {"query": query, "budget_characters": budget, "characters": len(rendered),
            "catalog_entries": len(entries), "selected": list(selected),
            "omitted_for_budget": rejected, "context": rendered}


if __name__ == "__main__":
    from . import language  # register the installed modules
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="agreement complement reference")
    parser.add_argument("--budget", type=int, default=6000)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    # Under -m the decorator modules import the canonical module, not __main__.
    from .catalog import RULES as installed, context as retrieve
    print(json.dumps(list(installed.values()) if args.list else retrieve(args.query, budget=args.budget), indent=2))
