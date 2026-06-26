#!/usr/bin/env python3
"""
storyworlds/worlds/vie_drunken_mermaid_flashback_curiosity_mystery.py
======================================================================

A tiny mystery storyworld about a curious mermaid, a drunken stumble, and a
flashback that helps solve the clue.

Seed tale:
---
Vie was a curious mermaid who loved mysteries more than pearls. One evening,
she found a shell lantern bobbing in the dark water, and a drunken seabird
kept bumping into it. Vie followed the bumping lantern to the old reef.

There, she remembered a flashback: earlier that day, her friend Miri had tied
the lantern to a coral post before a storm. The storm had shaken the knot loose.
Vie pieced together the clues, found the lantern, and returned it to Miri.

Narrative instruments:
---
Curiosity: the hero keeps following strange signs instead of turning away.
Flashback: a remembered earlier scene reveals who moved the clue and why.
Mystery style: the story begins with a puzzling sign, gathers clues, and ends
with the answer exposed and the world changed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    bearer: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mermaid", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    murky: bool = False
    holds: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_by: str
    revealed_by: str
    at_place: str
    risky: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.flashback_ready = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "reef": Place(id="reef", label="the old reef", murky=True, holds={"lantern", "stone", "shell"}),
    "cove": Place(id="cove", label="the moon cove", murky=False, holds={"lantern", "shell"}),
    "harbor": Place(id="harbor", label="the quiet harbor", murky=False, holds={"lantern", "rope"}),
}

CLUES = {
    "lantern": Clue(
        id="lantern",
        label="shell lantern",
        phrase="a shell lantern with a silver glow",
        hidden_by="storm",
        revealed_by="memory",
        at_place="reef",
        risky=True,
    ),
    "pearl": Clue(
        id="pearl",
        label="blue pearl",
        phrase="a blue pearl tucked under sea grass",
        hidden_by="sand",
        revealed_by="sifting",
        at_place="cove",
        risky=False,
    ),
    "note": Clue(
        id="note",
        label="reef note",
        phrase="a folded note tied to a coral stem",
        hidden_by="algae",
        revealed_by="curiosity",
        at_place="harbor",
        risky=False,
    ),
}

GIRL_NAMES = ["Vie", "Mira", "Nora", "Lina", "Sela", "Meli"]
BOY_NAMES = ["Tom", "Ben", "Oli"]
REASONS = ["curious", "careful", "brave", "thoughtful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
clue(C) :- clue_fact(C).

mystery(P, C) :- clue_at(C, P), hidden_by(C, storm), murky(P).
solve(P, C) :- mystery(P, C), flashback(C).
valid_story(P, C) :- place(P), clue(C), mystery(P, C), solve(P, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        if p.murky:
            lines.append(asp.fact("murky", pid))
        for h in sorted(p.holds):
            lines.append(asp.fact("holds", pid, h))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        lines.append(asp.fact("clue_at", cid, c.at_place))
        lines.append(asp.fact("hidden_by", cid, c.hidden_by))
        lines.append(asp.fact("revealed_by", cid, c.revealed_by))
    lines.append(asp.fact("flashback", "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/2.\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and python:")
    print(" only in python:", sorted(py - asp_set))
    print(" only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES.values():
        for clue in CLUES.values():
            if clue.at_place == place.id and clue.hidden_by == "storm":
                combos.append((place.id, clue.id))
    return combos


def explain_rejection(place: Place, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} at {place.label} is not a good mystery here. "
        f"Try the clue that was hidden by a storm in a murky place.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="mermaid"))
    item = world.add(Entity(id=clue.id, type="thing", label=clue.label, phrase=clue.phrase, owner=friend.id))
    item.bearer = friend.id

    hero.memes["curiosity"] = 1.0
    hero.memes["mystery"] = 1.0
    friend.memes["worry"] = 1.0
    world.facts.update(hero=hero, friend=friend, clue=clue, item=item, place=place)
    return world


def narrate_story(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]

    world.say(
        f"{hero.id} was a curious mermaid who loved a good mystery."
    )
    world.say(
        f"One dim evening at {place.label}, {hero.id} spotted {clue.phrase} drifting near a stone."
    )
    world.para()
    world.say(
        f"A drunken seabird wobbled by and bumped the water three times, "
        f"making the lantern bob toward the dark edge of the reef."
    )
    hero.memes["curiosity"] += 1
    hero.meters["distance"] = 1.0
    world.say(
        f"{hero.id} did not swim away. She followed the bobbing light, because curiosity made her keep looking."
    )
    world.para()
    world.say(
        f"Then came a flashback: earlier that day, {friend.id} had tied the lantern to a coral post before the storm."
    )
    world.say(
        f"When the storm shook the reef, the knot slipped loose, and the lantern drifted off."
    )
    hero.memes["understanding"] = 1.0
    world.say(
        f"{hero.id} put the clue together. The sea had not stolen the lantern; the storm had simply loosened it."
    )
    world.para()
    world.say(
        f"{hero.id} found {friend.id} waiting by the reef and returned the shell lantern."
    )
    friend.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    world.say(
        f"{friend.id} smiled, and the lantern glowed softly between them, safe again in the calm water."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_story(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short mystery story for a child about {hero.id}, a curious mermaid, and {clue.label}.",
        f"Tell a flashback mystery where {hero.id} follows a clue after seeing a drunken seabird near the reef.",
        f"Write a gentle underwater story with curiosity, a hidden clue, and an ending that explains what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a curious mermaid who kept following the mystery."
        ),
        QAItem(
            question=f"What strange thing did {hero.id} find near {place.label}?",
            answer=f"{hero.id} found {clue.phrase} near {place.label}."
        ),
        QAItem(
            question="What memory helped solve the mystery?",
            answer=(
                f"A flashback helped: {friend.id} had tied the lantern to a coral post before the storm, "
                f"and that made the drifting clue make sense."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} keep looking instead of swimming away?",
            answer=(
                f"{hero.id} kept looking because curiosity made her follow the bobbing light until the answer appeared."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is a part of a story that shows something that happened earlier, before the main scene."
    ),
    QAItem(
        question="What does curiosity mean?",
        answer="Curiosity means wanting to know more, so you keep asking questions and looking for clues."
    ),
    QAItem(
        question="Why do mysteries use clues?",
        answer="Mysteries use clues so the reader can piece together what happened and solve the puzzle."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.bearer:
            bits.append(f"bearer={e.bearer}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about Vie, a drunken clue, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
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
    combos = valid_combos()
    if args.place and args.clue:
        place = PLACES[args.place]
        clue = CLUES[args.clue]
        if (place.id, clue.id) not in combos:
            raise StoryError(explain_rejection(place, clue))
    choices = [c for c in combos if (args.place is None or c[0] == args.place) and (args.clue is None or c[1] == args.clue)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, clue_id = rng.choice(choices)
    hero_name = args.name or "Vie"
    gender = args.gender or "girl"
    friend = args.friend or rng.choice(["Miri", "Coral", "Nina"])
    return StoryParams(place=place_id, clue=clue_id, hero_name=hero_name, hero_type="mermaid" if gender == "girl" else "merman", friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place_id, clue_id in valid_combos():
            params = StoryParams(
                place=place_id,
                clue=clue_id,
                hero_name="Vie",
                hero_type="mermaid",
                friend_name="Miri",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
