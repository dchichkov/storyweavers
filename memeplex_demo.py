#!/usr/bin/env python3
"""
memeplex_demo.py - A working Listen / Purr memeplex transmission on gen6.

Demonstrates that the `story.py` north-star algebra runs on the gen6 world model:

  * Listen / Purr move *Story* / *Love* / *We* magnitudes between physical
    carriers, attention-diluted exactly like story.py (`animal.Story += Content/10`,
    `other.Love += cat.I/10`). The dilution is done with ordinary arithmetic in
    the kernel body; the engine records each as a meme effect on the carrier.
  * The transmitted memeplex state is visible in the World (`generate_world`) and
    influences later narration (`HappyEnd` reads accumulated Love).
  * An AST rewrite reframes `Tell(speaker, listener, content)` as
    `Listen(listener, speaker, content)` -- the rewrite layer carrying the same
    idea (story.py: "Tell calls Listen").

This module is a DEMO: it is not auto-loaded by `gen6registry`, so it has no
effect on coverage or the production engine unless you run/import it.

Run:  python memeplex_demo.py
"""

from __future__ import annotations

from typing import Any

from gen6registry import REGISTRY  # noqa: F401  (loads the full engine + packs)
from gen6 import (
    World,
    Character,
    Actor,
    Rewrite,
    NLGUtils,
    to_phrase,
    generate,
    generate_world,
)


def _content(content: Any) -> str:
    return to_phrase(content) or "stories"


def _embody(ent: Any) -> None:
    """A physical carrier has a unit of self-identity (`I`) once embodied, so the
    attention-diluted transmissions (`cat.I / 10`, ...) carry real weight."""
    if isinstance(ent, World):  # guard against misuse
        return
    if ent is not None and ent.meme("I") == 0:
        ent.add_meme("I", 1.0)


@REGISTRY.kernel("Listen")
def ListenMemeplex(ctx: World, listener: Character, speaker: Character, content: Any) -> str:
    """A listener absorbs a fraction of `content` (a memeplex) from a speaker.

    story.py:  animal.Story += Content / 10 ;  animal.We += other.We / 100
    Narration is *driven by accumulated state*: a listener who already carries
    other stories absorbs this one differently.
    """
    ctx.actor = listener
    _embody(listener); _embody(speaker)
    carried = len(listener.links.get("Story", []))             # READ accumulated state
    listener.add_meme("Story", speaker.meme("I") / 10)         # absorb a fraction (Content / 10)
    listener.add_link("Story", content)                        # ...of *this* content
    listener.add_meme("We", speaker.meme("We") / 100 + 0.2)    # weak group-identity merge
    listener.add_link("We", speaker)
    if carried == 0:
        return f"{ctx.say(listener)} listened closely to {speaker}'s story about {_content(content)}."
    return (f"{ctx.say(listener)} listened again, adding {speaker}'s tale of "
            f"{_content(content)} to the {carried + 1} stories {listener.pronoun('subject')} now carried.")


@REGISTRY.kernel("Purr")
def Purr(ctx: World, cat: Actor, other: Character = None) -> str:
    """A cat purrs; the physical vibration carries love + stories weakly to `other`.

    story.py:  other.Love += cat.I / 10 ;  other.Story += cat.Story / 100
    Narration is *driven by how much love `other` has already accumulated*.
    """
    ctx.actor = cat
    _embody(cat)
    cat.fact("action", "purring")                              # physical embedding of the purr
    cat.add_meme("Love", cat.meme("I") / 100 + 0.05)           # self-soothing (cat.I / 100)
    if other is None:
        return f"{ctx.say(cat)} purred softly to itself."
    _embody(other)
    prev = other.meme("Love")                                  # READ accumulated weight
    other.add_meme("Love", cat.meme("I") / 10 + 0.15)          # love carried by the vibration
    other.add_meme("Story", cat.meme("Story") / 100)           # weak story transmission
    for s in cat.links.get("Story", []):
        other.add_link("Story", s)
    other.add_link("Love", cat)
    # The prose escalates with the love `other` has already accumulated.
    if prev < 0.5:
        return f"{ctx.say(cat)} purred softly, and {other} felt the warm rumble and grew calm."
    if prev < 1.5:
        return f"{ctx.say(cat)} purred again, and {other}, already warmed, leaned in closer."
    return f"{ctx.say(cat)} purred once more; by now {other} could not imagine a day without {cat}."


@REGISTRY.kernel("Closeness")
def Closeness(ctx: World, a: Character, b: Character) -> str:
    """A closing reader whose text is chosen entirely from accumulated state: the
    total Love between the pair and the *shared* Story memeplexes they carry."""
    love = a.meme("Love") + b.meme("Love")
    shared = sorted(set(a.links.get("Story", [])) & set(b.links.get("Story", [])))
    if love >= 3.0 and shared:
        topic = NLGUtils.join_list([_content(s) for s in shared])
        return f"Bound by the story of {topic}, {a} and {b} had become inseparable."
    if love >= 1.0:
        return f"{a} and {b} had grown very close."
    return f"{a} and {b} stayed good friends."


# The 3-arg memeplex Listen and the generic intransitive Listen (gen6k03) both
# bind 3 args and tie; the dispatcher breaks ties by registration order, so move
# ours to the front of the Listen variant list to win the 3-arg shape.
_listen_variants = REGISTRY.kernels["Listen"]
_listen_variants.insert(0, _listen_variants.pop())

# AST rewrite: telling is the other listening (story.py: Tell calls Listen).
MEMEPLEX_RULES = [
    Rewrite(pattern_src="Tell(__S, __L, __C)", output_src="Listen(__L, __S, __C)"),
]


def _demo() -> None:
    head = "Spot(Character, cat, Loyal)\nLily(Character, girl, Curious)\n"
    light = head + "Listen(Spot, Lily, Treasure)\nPurr(Spot, Lily)\nCloseness(Spot, Lily)"
    heavy = head + "Listen(Spot, Lily, Treasure)\n" + "Purr(Spot, Lily)\n" * 8 + "Closeness(Spot, Lily)"

    print("=== ACCUMULATED WEIGHTS DRIVE THE NARRATION ===")
    print("--- light (1 purr) ---")
    print(generate(light))
    print("--- heavy (8 purrs: Love accumulates -> different prose AND ending) ---")
    print(generate(heavy))

    print("\n=== WORLD-MODEL EFFECTS (transmitted memeplex magnitudes / links) ===")
    print(generate_world(light).state())

    print("\n=== AST REWRITE: Tell(speaker, listener, content) -> Listen(listener, speaker, content) ===")
    tell = "Spot(Character, cat)\nLily(Character, girl)\nTell(Lily, Spot, Treasure)"
    print("without rule:", generate(tell).split(". ", 2)[-1])
    print("with rule   :", generate(tell, rules=MEMEPLEX_RULES).split(". ", 2)[-1])


if __name__ == "__main__":
    _demo()
