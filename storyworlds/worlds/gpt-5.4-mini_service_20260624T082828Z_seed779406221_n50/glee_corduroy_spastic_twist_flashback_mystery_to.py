#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/glee_corduroy_spastic_twist_flashback_mystery_to.py
==========================================================================================================================

A tiny superhero storyworld built from the seed words glee, corduroy, and
spastic, with a Twist, a Flashback, and a Mystery to Solve.

The world is a small, state-driven comic-book domain:
- a young hero wears a corduroy suit
- a mystery object goes missing
- a spastic little drone/helper shakes clues loose
- a flashback reveals what was forgotten
- a final twist shows the "lost" thing was safe all along

The story is generated from world state, not from a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue_kind: str
    location_hint: str
    can_flashback: bool = True


@dataclass
class Gadget:
    id: str
    label: str
    effect: str
    clue_kind: str
    move: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_kind: str
    sidekick: str
    mystery: str
    gadget: str
    seed: Optional[int] = None


PLACES = {
    "roof": Place(name="the city roof", indoors=False, affords={"search", "flashback", "twist"}),
    "lab": Place(name="the moonlit lab", indoors=True, affords={"search", "flashback", "twist"}),
    "museum": Place(name="the museum hall", indoors=True, affords={"search", "flashback", "twist"}),
}

HEROES = [
    ("Nova", "heroine"),
    ("Jet", "hero"),
    ("Mira", "heroine"),
    ("Pax", "hero"),
]

SIDEKICKS = [
    "glee-bat", "spark drone", "cloud cub", "mini mask", "signal cat"
]

MYSTERIES = {
    "missing_medal": Mystery(
        id="missing_medal",
        label="missing medal",
        phrase="a polished medal with a star on it",
        clue_kind="shiny",
        location_hint="the hero's corduroy pocket",
    ),
    "lost_map": Mystery(
        id="lost_map",
        label="lost map",
        phrase="a folded map with a red X",
        clue_kind="paper",
        location_hint="under a display case",
    ),
    "quiet_key": Mystery(
        id="quiet_key",
        label="quiet key",
        phrase="a tiny brass key",
        clue_kind="metal",
        location_hint="inside the corduroy cape lining",
    ),
}

GADGETS = {
    "magnifier": Gadget(
        id="magnifier",
        label="a magnifier",
        effect="spot tiny clues",
        clue_kind="shiny",
        move="shined",
    ),
    "scanner": Gadget(
        id="scanner",
        label="a pocket scanner",
        effect="find hidden marks",
        clue_kind="paper",
        move="beeped",
    ),
    "rattle": Gadget(
        id="rattle",
        label="a clue rattle",
        effect="shake loose what was stuck",
        clue_kind="metal",
        move="rattled",
    ),
}


ASP_RULES = r"""
mystery_at_risk(M) :- mystery(M), clue_kind(M, K), gadget(G), matches(G, K).
can_solve(M, G) :- mystery_at_risk(M), gadget(G), matches(G, K), clue_kind(M, K).
valid_story(P, M, G) :- place(P), affords(P, search), mystery(M), gadget(G), can_solve(M, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("matches", gid, g.clue_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for g in GADGETS:
                combos.append((p, m, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.gadget is None or c[2] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, gadget = rng.choice(sorted(combos))
    hero, hero_kind = rng.choice(HEROES)
    if args.name:
        hero = args.name
    sidekick = rng.choice(SIDEKICKS)
    return StoryParams(place=place, hero=hero, hero_kind=hero_kind, sidekick=sidekick, mystery=mystery, gadget=gadget)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_kind, label=params.hero))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="thing", label=params.sidekick))
    mystery = world.add(Entity(id="mystery", type="thing", label=MYSTERIES[params.mystery].label,
                               phrase=MYSTERIES[params.mystery].phrase, caretaker=hero.id))
    gadget = world.add(Entity(id="gadget", type="thing", label=GADGETS[params.gadget].label,
                              phrase=GADGETS[params.gadget].label, owner=hero.id))
    world.facts.update(hero=hero, sidekick=sidekick, mystery=mystery, gadget=gadget, params=params)
    return world


def simulate(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    mystery = world.get("mystery")
    gadget = world.get("gadget")
    p = world.facts["params"]
    mystery_cfg = MYSTERIES[p.mystery]
    gadget_cfg = GADGETS[p.gadget]

    hero.memes["glee"] = 1
    hero.meters["corduroy"] = 1
    world.say(f"{hero.label} was a young {hero.type} in a brown corduroy suit, and {hero.pronoun()} felt glee at the first flash of moonlight.")

    world.say(f"At {world.place.name}, {hero.pronoun()} and {sidekick.label} spotted a mystery: {mystery_cfg.phrase}.")
    hero.memes["curiosity"] = 1
    sidekick.meters["spastic"] = 1
    world.say(f"{sidekick.label} twitched in a spastic little zigzag, and its jittery hops showed {hero.label} where to look next.")

    world.para()
    hero.memes["worry"] = 1
    world.say(f"{hero.label} searched with {gadget_cfg.label}, but the clue still slipped away.")
    world.say(f"Then came the twist: {hero.label} noticed a tiny bump in the corduroy pocket.")

    hero.memes["flashback"] = 1
    world.say(f"A flashback filled {hero.label}'s mind: earlier, {hero.label} had tucked the {mystery_cfg.label} there to keep it safe.")

    world.para()
    world.say(f"{hero.label} laughed with glee, pulled out the {mystery_cfg.label}, and solved the mystery to solve it at last.")
    world.say(f"The city stayed bright, {sidekick.label} spun in happy little hops, and the corduroy suit held the prize all along.")

    world.facts["solved"] = True
    world.facts["twist"] = True
    world.facts["flashback"] = True


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    mystery: Entity = world.facts["mystery"]
    gadget: Entity = world.facts["gadget"]
    return [
        QAItem(
            question=f"What kind of suit did {hero.label} wear during the mystery?",
            answer=f"{hero.label} wore a corduroy suit, which helped make the superhero look brave and bright.",
        ),
        QAItem(
            question=f"What was the story's mystery to solve?",
            answer=f"The mystery was {mystery.label}: {mystery.phrase}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the {mystery.label} was already safe in {hero.label}'s corduroy pocket.",
        ),
        QAItem(
            question=f"How did the flashback help?",
            answer=f"The flashback reminded {hero.label} that {hero.pronoun('subject')} had tucked the {mystery.label} away earlier to keep it safe.",
        ),
        QAItem(
            question=f"How did {gadget.label} help at the museum, roof, or lab?",
            answer=f"{gadget.label.capitalize()} helped {hero.label} search for hidden clues before the twist showed the object had not been lost at all.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something from earlier so the reader can understand what happened before.",
        ),
        QAItem(
            question="What is a mystery in a superhero story?",
            answer="A mystery is a problem or missing thing that the hero has to figure out by following clues.",
        ),
        QAItem(
            question="What does the word glee mean?",
            answer="Glee means bright, happy excitement.",
        ),
        QAItem(
            question="What is corduroy?",
            answer="Corduroy is a fabric with soft ridges that you can feel with your fingers.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    mystery: Entity = world.facts["mystery"]
    return [
        f"Write a short superhero story about {hero.label} in corduroy who solves a {mystery.label} with a flashback and a twist.",
        f"Tell a child-friendly mystery story where glee helps a hero notice a clue and the answer is surprising.",
        f"Write a simple comic-style tale with a spastic sidekick, a hidden clue, and the phrase 'mystery to solve'.",
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="roof", hero="Nova", hero_kind="heroine", sidekick="glee-bat", mystery="missing_medal", gadget="magnifier"),
    StoryParams(place="museum", hero="Jet", hero_kind="hero", sidekick="spark drone", mystery="lost_map", gadget="scanner"),
    StoryParams(place="lab", hero="Mira", hero_kind="heroine", sidekick="signal cat", mystery="quiet_key", gadget="rattle"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, mystery, gadget) combos:\n")
        for t in stories:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
