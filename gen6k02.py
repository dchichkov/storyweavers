"""
gen6k02.py - Kernel Pack #02 for the gen6 engine.

Created by following the AGENTS.md gen6 workflow (sample -> study -> implement).

`Visit` - sampled with `python sample.py -k Visit -n 5 --seed 42 --show-source`.
Observed argument shapes in the dataset:
    Visit(Lily, Grandma)            -- visitor visits a person
    Visit(Sam, Tom)                 -- visitor visits a person
    Visit(Lily, park)               -- visitor visits a place
    Visit(zoo, Timmy, Mom, Gorilla) -- place first, then the visitors
    Visit(Lily, Mom, Friend)        -- several visitors
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Character,
    Physical,
    Actor,
    NLGUtils,
    to_phrase,
)


@REGISTRY.kernel("Visit")
def Visit(ctx: World, visitor: Actor, target: Character, **kw: Any) -> str:
    """Visit(visitor, person) -- a character goes to visit another character."""
    visitor.Joy += 0.2
    ctx.actor = visitor
    return f"{ctx.say(visitor)} went to visit {target}."


@REGISTRY.kernel("Visit")
def VisitPlace(ctx: World, visitor: Actor, place: Physical, **kw: Any) -> str:
    """Visit(visitor, place) -- a character visits a place."""
    visitor.Joy += 0.2
    ctx.actor = visitor
    ctx.current_object = place
    return f"{ctx.say(visitor)} visited {place}."


@REGISTRY.kernel("Visit")
def VisitPlaceGroup(ctx: World, place: Physical, *visitors: Character) -> str:
    """Visit(place, *visitors) -- a place visited by one or more characters."""
    ctx.current_object = place
    if visitors:
        ctx.actor = visitors[0]
        visitors[0].Joy += 0.2
    names = NLGUtils.join_list([str(v) for v in visitors]) or "everyone"
    return f"{names} went to {place}."


if __name__ == "__main__":
    from gen6 import generate

    tests = [
        "Lily(Character, girl)\nGrandma(Character, grandmother)\nVisit(Lily, Grandma)",
        "Sam(Character, boy)\nVisit(Sam, park)",
        "Timmy(Character, boy)\nMom(Character, mother)\nGorilla(Character, animal)\nVisit(zoo, Timmy, Mom, Gorilla)",
        "Lily(Character, girl)\nMom(Character, mother)\nFriend(Character, girl)\nVisit(Lily, Mom, Friend)",
    ]
    for i, t in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(t))
        print()
