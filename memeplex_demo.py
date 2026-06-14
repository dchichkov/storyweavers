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
    to_phrase,
    generate,
    generate_world,
)


def _content(content: Any) -> str:
    return to_phrase(content) or "stories"


@REGISTRY.kernel("Listen")
def ListenMemeplex(ctx: World, listener: Character, speaker: Character, content: Any) -> str:
    """A listener absorbs a fraction of `content` (a memeplex) from a speaker.

    story.py:  animal.Story += Content / 10 ;  animal.We += other.We / 100
    """
    ctx.actor = listener
    listener.add_meme("Story", 0.1)                            # absorb a fraction (Content / 10)
    listener.add_link("Story", content)                        # ...of *this* content
    listener.add_meme("We", speaker.meme("We") / 100 + 0.1)    # weak group-identity merge
    listener.add_link("We", speaker)
    return f"{ctx.say(listener)} listened closely to {speaker}'s story about {_content(content)}."


@REGISTRY.kernel("Purr")
def Purr(ctx: World, cat: Actor, other: Character = None) -> str:
    """A cat purrs; the physical vibration carries love + stories weakly to `other`.

    story.py:  other.Love += cat.I / 10 ;  other.Story += cat.Story / 100
    """
    ctx.actor = cat
    cat.fact("action", "purring")                              # physical embedding of the purr
    cat.add_meme("Love", cat.meme("I") / 100 + 0.1)            # self-soothing (cat.I / 100)
    if other is not None:
        other.add_meme("Love", cat.meme("I") / 10 + 0.4)       # love carried by the vibration
        other.add_meme("Story", cat.meme("Story") / 100)       # weak story transmission
        for s in cat.links.get("Story", []):
            other.add_link("Story", s)
        other.add_link("Love", cat)
        return f"{ctx.say(cat)} purred softly, and {other} felt the warm rumble and grew calm."
    return f"{ctx.say(cat)} purred softly to itself."


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
    story = (
        "Spot(Character, cat, Loyal)\n"
        "Lily(Character, girl, Curious)\n"
        "Listen(Spot, Lily, Treasure)\n"   # Spot absorbs Lily's story about treasure
        "Purr(Spot, Lily)\n"               # Spot purrs -> transmits love + story to Lily
        "HappyEnd()"
    )
    print("=== NARRATION ===")
    print(generate(story))

    print("\n=== WORLD-MODEL EFFECTS (transmitted memeplex magnitudes / links) ===")
    print(generate_world(story).state())

    print("\n=== AST REWRITE: Tell(speaker, listener, content) -> Listen(listener, speaker, content) ===")
    tell = (
        "Spot(Character, cat)\n"
        "Lily(Character, girl)\n"
        "Tell(Lily, Spot, Treasure)"
    )
    print("without rule:", generate(tell).split(". ", 2)[-1])
    print("with rule   :", generate(tell, rules=MEMEPLEX_RULES).split(". ", 2)[-1])


if __name__ == "__main__":
    _demo()
