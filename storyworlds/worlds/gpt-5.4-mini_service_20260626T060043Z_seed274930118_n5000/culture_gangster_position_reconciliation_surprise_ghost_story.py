#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-style reconciliation tale with a surprise
turn. The seed words are culture, gangster, and position; the world model
centers on a local haunt, a feared gangster, a standing/position in the room,
and a later reconciliation that changes the mood.

The simulation is intentionally small and classical:
- a child or young person explores a moonlit place
- a local gangster figure is tied to a cultural gathering spot
- a ghostly surprise reveals a misunderstanding
- reconciliation changes fear into respect and peace
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | spirit | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    position: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "hope": 0.0, "trust": 0.0, "grief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    culture: str
    haunted: bool = True
    position: str = "center"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "alley": Place(id="alley", label="the candlelit alley", culture="street music", haunted=True, position="center"),
    "courtyard": Place(id="courtyard", label="the old courtyard", culture="night drums", haunted=True, position="edge"),
    "market": Place(id="market", label="the sleepy night market", culture="lantern stories", haunted=True, position="stall"),
    "dock": Place(id="dock", label="the foggy dock", culture="salt songs", haunted=True, position="pier"),
}

GANGSTERS = {
    "boss": {"type": "man", "label": "the gangster boss", "phrase": "a feared gangster with a soft voice", "position": "corner"},
    "runner": {"type": "man", "label": "the runner", "phrase": "a quick gangster lookout", "position": "doorway"},
    "aunt": {"type": "woman", "label": "Auntie Mara", "phrase": "a neighborhood elder who knew every story", "position": "bench"},
}

GHOSTS = {
    "child_ghost": {"type": "spirit", "label": "the little ghost", "phrase": "a pale ghost child with a lantern", "position": "stairs"},
    "grand_ghost": {"type": "spirit", "label": "Grandmother Ghost", "phrase": "a warm old ghost with silver hair", "position": "window"},
}

HEROES = {
    "girl": {"type": "girl", "label": "Mina", "phrase": "a curious girl who liked midnight stories"},
    "boy": {"type": "boy", "label": "Noah", "phrase": "a careful boy who listened before speaking"},
}

TRAITS = ["curious", "brave", "quiet", "gentle", "restless"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    gangster: str
    ghost: str
    hero: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def valid_combo(place: Place, gangster: str, ghost: str) -> bool:
    return place.haunted and gangster in GANGSTERS and ghost in GHOSTS


def explain_invalid(place: Optional[str], gangster: Optional[str], ghost: Optional[str]) -> str:
    if place and place in PLACES and not PLACES[place].haunted:
        return "(No story: this world only tells haunted-night stories, so the place must feel haunted.)"
    return "(No story: the chosen pieces do not fit this ghost-story world.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(alley). place(courtyard). place(market). place(dock).
haunted(alley). haunted(courtyard). haunted(market). haunted(dock).

gangster(boss). gangster(runner). gangster(aunt).
ghost(child_ghost). ghost(grand_ghost).

valid(P,G,H) :- place(P), haunted(P), gangster(G), ghost(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].haunted:
            lines.append(asp.fact("haunted", pid))
    for gid in GANGSTERS:
        lines.append(asp.fact("gangster", gid))
    for hid in GHOSTS:
        lines.append(asp.fact("ghost", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, g, h) for p in PLACES for g in GANGSTERS for h in GHOSTS if valid_combo(PLACES[p], g, h)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero_info = HEROES[params.hero]
    hero = world.add(Entity(
        id=hero_info["label"], kind="character", type=hero_info["type"],
        label=hero_info["label"], phrase=hero_info["phrase"], position="threshold",
        memes={"fear": 0.0, "curiosity": 1.0, "hope": 0.0, "trust": 0.0, "grief": 0.0},
    ))

    gangster_info = GANGSTERS[params.gangster]
    gangster = world.add(Entity(
        id=gangster_info["label"], kind="character", type=gangster_info["type"],
        label=gangster_info["label"], phrase=gangster_info["phrase"], position=gangster_info["position"],
        memes={"fear": 0.0, "curiosity": 0.0, "hope": 0.0, "trust": 0.0, "grief": 1.0},
    ))

    ghost_info = GHOSTS[params.ghost]
    ghost = world.add(Entity(
        id=ghost_info["label"], kind="spirit", type="spirit",
        label=ghost_info["label"], phrase=ghost_info["phrase"], position=ghost_info["position"],
        memes={"fear": 0.0, "curiosity": 0.0, "hope": 0.0, "trust": 0.0, "grief": 1.0},
    ))

    # Setup
    world.say(f"At {place.label}, the night held its breath over {place.culture}.")
    world.say(f"{hero.id} was {params.trait} and wandered toward the center of the dark place.")
    world.say(f"There, {hero.pronoun()} noticed {gangster.id}, who stood near the {gangster.position} like a shadow with a secret.")
    world.say(f"Everyone whispered that the gangster belonged to the old stories of the neighborhood.")

    # Tension
    world.para()
    hero.memes["fear"] += 1.0
    hero.memes["curiosity"] += 1.0
    world.say(f"Then a ghostly shape drifted out of the dark: {ghost.id}, {ghost.phrase}.")
    world.say(f"{hero.id} stepped back, because the air felt colder and the position of the lantern made the shadows jump.")
    world.say(f"{gangster.id} lowered {gangster.pronoun('possessive')} voice and warned {hero.id} not to go closer.")

    # Surprise turn
    world.para()
    world.say(f"But the ghost did not come to frighten them.")
    ghost.memes["hope"] += 1.0
    world.say(f"{ghost.id} floated beside {gangster.id} and pointed to a faded mark on the wall.")
    world.say(f"It was the sign of a lost family song, part of the culture that both the living and the dead remembered.")
    world.say(f"The gangster had been guarding the place, not to rule it, but to keep the children from getting hurt at night.")
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["hope"] += 1.0

    # Reconciliation
    world.para()
    gangster.memes["trust"] += 1.0
    hero.memes["trust"] += 1.0
    ghost.memes["trust"] += 1.0
    world.say(f"{hero.id} took a careful position beside the gangster and listened to the old song.")
    world.say(f"At last, {hero.id} understood that the feared figure had been lonely, not cruel.")
    world.say(f"{hero.id} smiled, thanked {gangster.id}, and promised to bring the song back in the morning.")
    world.say(f"The ghost drifted higher, peaceful now, as if the story had finally found the right ending.")

    world.facts.update(
        place=params.place,
        gangster=params.gangster,
        ghost=params.ghost,
        hero=params.hero,
        trait=params.trait,
        reconciled=True,
        surprised=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    return [
        f"Write a short ghost story about {world.facts['hero']} at {world.place.label} with a surprise and reconciliation.",
        f"Tell a child-friendly spooky story where a gangster and a ghost help a curious child understand a place and its culture.",
        f"Write a gentle haunted-night tale that ends with peace after fear turns into understanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    gangster = world.facts["gangster"]
    ghost = world.facts["ghost"]
    place = world.place.label
    return [
        QAItem(
            question=f"Where did {hero} go in the story?",
            answer=f"{hero} went to {place}, which was a haunted place full of shadows and old stories.",
        ),
        QAItem(
            question=f"Why did {hero} first feel scared of {gangster}?",
            answer=f"{hero} thought {gangster} was dangerous because {gangster} stood like a shadow at the edge of the dark place.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that the ghost came to explain the truth, and the gangster was protecting children instead of causing harm.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with reconciliation: {hero} thanked {gangster}, the ghost grew peaceful, and the night felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about something spooky or mysterious, often with a haunted place, shadows, and a surprise reveal.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset or afraid come to understand each other and make peace.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a change the reader does not expect, like finding out someone was helping instead of causing trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.position:
            bits.append(f"position={e.position}")
        lines.append(f"  {e.id:20} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="alley", gangster="boss", ghost="child_ghost", hero="girl", trait="curious"),
    StoryParams(place="market", gangster="runner", ghost="grand_ghost", hero="boy", trait="gentle"),
    StoryParams(place="courtyard", gangster="aunt", ghost="child_ghost", hero="girl", trait="quiet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with surprise and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gangster", choices=GANGSTERS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [
        (p, g, h)
        for p in PLACES
        for g in GANGSTERS
        for h in GHOSTS
        if valid_combo(PLACES[p], g, h)
        and (args.place is None or args.place == p)
        and (args.gangster is None or args.gangster == g)
        and (args.ghost is None or args.ghost == h)
    ]
    if not combos:
        raise StoryError(explain_invalid(args.place, args.gangster, args.ghost))
    place, gangster, ghost = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(list(HEROES))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, gangster=gangster, ghost=ghost, hero=hero, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, gangster, ghost) combos:\n")
        for p, g, h in combos:
            print(f"  {p:10} {g:10} {h:14}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.gangster} at {p.place} with {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
