#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/groom_bunny_uppie_repetition_ghost_story.py
=============================================================================================================

A small standalone storyworld: a ghost-story-shaped tale about a groom,
a bunny, and the repeated little word "uppie".

The core premise is simple and child-facing:
- A groom is getting ready for a quiet evening in an old chapel.
- A bunny keeps repeating "uppie" from the dark loft.
- The repetition sounds spooky at first, but the world model shows it is
  actually a request for help.
- The turn comes when the groom uses repetition back, calmly and gently,
  and the bunny finally gets lifted to the moonlit window.

The story is built from simulated state:
- meters track physical position, distance, and effort
- memes track fear, comfort, relief, trust, and resolve
- repetition is not just a writing style; it is a causal feature that
  changes fear into comfort as the characters echo each other.

The seed words are included by design: groom, bunny, uppie.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"groom", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    eerie: bool = True
    moonlit: bool = False
    has_loft: bool = False
    has_window: bool = False


@dataclass
class StoryParams:
    place: str = "chapel"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def char(self, kind: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == kind]


# ---------------------------------------------------------------------------
# Story settings
# ---------------------------------------------------------------------------
PLACES = {
    "chapel": Place(id="chapel", label="the old chapel", eerie=True, moonlit=True, has_loft=True, has_window=True),
    "barn": Place(id="barn", label="the old barn", eerie=True, moonlit=True, has_loft=True, has_window=False),
    "attic": Place(id="attic", label="the attic room", eerie=True, moonlit=False, has_loft=False, has_window=True),
}


# ---------------------------------------------------------------------------
# World-model rules: repetition turns fear into recognition.
# ---------------------------------------------------------------------------
def _f_spook(world: World) -> None:
    groom = world.get("groom")
    bunny = world.get("bunny")
    if groom.memes.get("unease", 0) >= 1 and bunny.meters.get("repeat", 0) >= 2 and "spook" not in world.fired:
        world.fired.add("spook")
        groom.memes["fear"] = groom.memes.get("fear", 0) + 1
        bunny.memes["alone"] = bunny.memes.get("alone", 0) + 1
        world.say("The repeated little sound made the dark feel bigger for a moment.")


def _f_recognize(world: World) -> None:
    groom = world.get("groom")
    bunny = world.get("bunny")
    if bunny.meters.get("repeat", 0) >= 3 and groom.memes.get("fear", 0) >= 1 and "recognize" not in world.fired:
        world.fired.add("recognize")
        groom.memes["curiosity"] = groom.memes.get("curiosity", 0) + 1
        groom.memes["fear"] = max(0, groom.memes.get("fear", 0) - 1)
        world.say("The groom listened again and began to hear a request, not a threat.")


def _f_comfort(world: World) -> None:
    groom = world.get("groom")
    bunny = world.get("bunny")
    if bunny.meters.get("lifted", 0) >= 1 and "comfort" not in world.fired:
        world.fired.add("comfort")
        bunny.memes["relief"] = bunny.memes.get("relief", 0) + 1
        groom.memes["kindness"] = groom.memes.get("kindness", 0) + 1
        world.say("Being lifted made the bunny feel safe at last.")


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.lines)
        _f_spook(world)
        _f_recognize(world)
        _f_comfort(world)
        changed = len(world.lines) != before


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def tell(place: Place) -> World:
    world = World(place)
    groom = world.add(Entity(
        id="groom", kind="character", type="groom",
        label="the groom",
        meters={"steps": 0, "listening": 0},
        memes={"calm": 0, "unease": 0, "fear": 0, "curiosity": 0, "kindness": 0},
    ))
    bunny = world.add(Entity(
        id="bunny", kind="character", type="bunny",
        label="the bunny",
        meters={"repeat": 0, "lifted": 0, "height": 0},
        memes={"alone": 0, "trust": 0, "relief": 0},
    ))
    uppie = world.add(Entity(
        id="uppie", kind="thing", type="word",
        label="uppie",
        phrase="the little word uppie",
    ))

    # Act 1: the quiet setup.
    world.say(f"In {place.label}, the groom walked softly past the candles.")
    world.say(f"Near the shadowy loft, the bunny waited with {uppie.phrase} tucked in its tiny voice.")
    world.say("The room felt still, and the stillness made every small sound matter.")

    # Act 2: repetition raises the eerie feeling.
    world.say("Then came the whisper: 'uppie, uppie.'")
    bunny.meters["repeat"] += 2
    bunny.memes["trust"] += 1
    groom.memes["unease"] += 1
    propagate(world)

    world.say("The groom stopped. He listened. 'Uppie?' he asked, and the bunny answered, 'uppie, uppie.'")
    bunny.meters["repeat"] += 1
    groom.meters["listening"] += 1
    propagate(world)

    # Turn: repetition becomes understanding.
    world.say("The groom repeated it back in a soft voice. 'Uppie, little bunny. Uppie.'")
    groom.memes["calm"] += 1
    bunny.memes["trust"] += 1
    bunny.meters["repeat"] += 1
    propagate(world)

    # Act 3: the lift and the moonlit ending.
    if place.has_loft or place.has_window:
        world.say("At last he reached up, one careful lift, and the bunny came up, uppie, uppie.")
        bunny.meters["lifted"] += 1
        bunny.meters["height"] += 1
        groom.meters["steps"] += 1
        propagate(world)

    if place.moonlit and place.has_window:
        world.say("There at the window, the bunny could see the moon, and the dark no longer felt so large.")
    else:
        world.say("The bunny settled close beside him, and the room felt warm enough to end the spooky feeling.")

    world.facts.update(
        place=place,
        groom=groom,
        bunny=bunny,
        uppie=uppie,
        repeated=bunny.meters["repeat"],
        lifted=bunny.meters["lifted"] >= 1,
        resolved=bunny.memes.get("relief", 0) >= 1,
    )
    return world


# ---------------------------------------------------------------------------
# Question sets
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    place: Place = world.facts["place"]
    return [
        f"Write a gentle ghost story set in {place.label} that repeats the word 'uppie' in a spooky-but-kind way.",
        "Tell a child-facing story about a groom, a bunny, and a repeated little request that sounds eerie at first.",
        "Write a short story where repetition changes fear into understanding and ends with moonlight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    groom: Entity = world.facts["groom"]
    bunny: Entity = world.facts["bunny"]
    place: Place = world.facts["place"]
    qa = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about a groom and a bunny in {place.label}.",
        ),
        QAItem(
            question="What little word did the bunny keep saying?",
            answer="The bunny kept saying uppie.",
        ),
        QAItem(
            question="Why did the groom feel uneasy at first?",
            answer="He felt uneasy because the repeated uppie sound made the dark seem spooky before he understood it.",
        ),
        QAItem(
            question="What changed the story from spooky to safe?",
            answer="The groom listened closely, repeated the word back, and then lifted the bunny up so it could reach the moonlit window.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="How did the ending prove the bunny was safe?",
                answer="At the end, the bunny was lifted up and could see the moon, so the repeated sound turned out to be a request for help, not a ghostly scare.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying the same word or phrase again and again. It can make a story feel spooky, musical, or important.",
        ),
        QAItem(
            question="Why can moonlight feel calm?",
            answer="Moonlight is soft and pale, so it can make a dark place feel gentle instead of sharp and scary.",
        ),
        QAItem(
            question="Why might a small animal ask to be picked up?",
            answer="A small animal might ask to be picked up to feel safe, see higher, or get help reaching a place it cannot reach alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(chapel).
place(barn).
place(attic).

has_loft(chapel).
has_loft(barn).
has_window(chapel).
has_window(attic).
moonlit(chapel).
moonlit(barn).

requires_help(bunny) :- repeats(bunny, N), N >= 2.
recognizes_request(groom) :- hears(groom, uppie), requires_help(bunny).
safe_ending :- recognizes_request(groom), lifted(bunny).

valid_story(Place) :- place(Place), has_window(Place).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        p = PLACES[pid]
        if p.has_loft:
            lines.append(asp.fact("has_loft", pid))
        if p.has_window:
            lines.append(asp.fact("has_window", pid))
        if p.moonlit:
            lines.append(asp.fact("moonlit", pid))
    lines.append(asp.fact("character", "groom"))
    lines.append(asp.fact("character", "bunny"))
    lines.append(asp.fact("word", "uppie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p,) for p in PLACES if PLACES[p].has_window}
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = tell(place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_places())} valid places:")
        for (p,) in asp_valid_places():
            print(p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            p = StoryParams(place=place, seed=base_seed)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
