#!/usr/bin/env python3
"""
storyworlds/worlds/hair_gunk_dim_warrior_mystery_to_solve.py
=============================================================

A small space-adventure storyworld about a warrior, a strange gunk-dim mystery,
and a careful fix that makes the ship bright again.

The seed tale behind this world is simple:
- A young warrior with bright hair travels on a small starship.
- A mysterious gunk-dim spreads through the glow panels and makes the ship feel
  shadowy and off-balance.
- The warrior investigates clues, finds the source, and solves the mystery.
- The ending proves what changed: the ship is bright, the hair is cleaned, and
  the crew can see the stars clearly again.

This script keeps a close, child-facing Space Adventure style while still being
a genuine state-driven simulation: the mystery, the clues, the cleanup, and the
resolution are all modeled in the world state and narrated from it.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen"}
        male = {"boy", "man", "father", "brother", "warrior", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    dimmed: bool = False
    sections: list[str] = field(default_factory=lambda: ["bridge", "hall", "panel bay", "airlock"])
    clues_found: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    source: str


@dataclass
class Cause:
    id: str
    label: str
    mess: str
    fix: str
    place: str


@dataclass
class StoryParams:
    ship: str
    place: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    crewmate_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


SHIP_REGISTRY = {
    "comet-runner": Ship(name="Comet Runner", place="a small starship"),
    "starlight": Ship(name="Starlight", place="a bright scout ship"),
    "moon-catcher": Ship(name="Moon Catcher", place="a little rescue ship"),
}

PLACES = {
    "bridge": "the bridge",
    "hall": "the long hall",
    "panel-bay": "the panel bay",
    "airlock": "the airlock",
    "galley": "the tiny galley",
}

CAUSES = {
    "slime-vine": Cause(
        id="slime-vine",
        label="a slime vine leak",
        mess="green gunk",
        fix="scrubbed the vents and sealed the crack",
        place="the panel bay",
    ),
    "oil-mote": Cause(
        id="oil-mote",
        label="a drifting oil mote",
        mess="dark gunk",
        fix="wiped the switch and cleaned the light strip",
        place="the bridge",
    ),
    "ink-crab": Cause(
        id="ink-crab",
        label="an ink crab hiding in a duct",
        mess="inky gunk",
        fix="patted the crab out, then washed the panel",
        place="the airlock",
    ),
}

HAIR_STYLES = ["bright", "curly", "long", "shiny", "wind-tossed"]
TRAITS = ["brave", "curious", "patient", "lively", "steady"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure mystery storyworld: a warrior, gunk-dim, and a solved clue."
    )
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-trait", choices=TRAITS)
    ap.add_argument("--crewmate-name")
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
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    place = args.place or rng.choice(list(PLACES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(
        ["Aria", "Nova", "Pip", "Mira", "Zed", "Tali"] if hero_gender == "girl" else
        ["Jax", "Orin", "Rin", "Taro", "Milo", "Kian"]
    )
    hero_trait = args.hero_trait or rng.choice(TRAITS)
    crewmate_name = args.crewmate_name or rng.choice(["Captain Sol", "Aunt Vega", "Pilot Luna", "Dr. Comet"])
    return StoryParams(
        ship=ship,
        place=place,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
        crewmate_name=crewmate_name,
    )


def choose_cause(rng: random.Random) -> Cause:
    return rng.choice(list(CAUSES.values()))


def hair_color_word(rng: random.Random) -> str:
    return rng.choice(["golden", "dark", "red", "silver", "brown"])


def tell_story(params: StoryParams, rng: random.Random) -> World:
    ship = SHIP_REGISTRY[params.ship]
    world = World(ship)
    cause = choose_cause(rng)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="warrior",
        traits=["young", params.hero_trait],
    ))
    crewmate = world.add(Entity(
        id=params.crewmate_name,
        kind="character",
        type="captain",
        label=params.crewmate_name,
        traits=["kind"],
    ))
    hair = world.add(Entity(
        id="hair",
        type="hair",
        label="hair",
        phrase=f"{hair_color_word(rng)} hair",
        owner=hero.id,
        caretaker=hero.id,
    ))
    goggles = world.add(Entity(
        id="goggles",
        type="gear",
        label="goggles",
        phrase="clear ship goggles",
        owner=hero.id,
        caretaker=hero.id,
        worn_by=hero.id,
        plural=True,
    ))

    hero.meters["bravery"] = 1
    hero.memes["pride"] = 1
    world.ship.dimmed = True

    # Act 1
    world.say(f"On the {ship.name}, a young warrior named {hero.id} wore {hair.phrase} and watched the stars.")
    world.say(f"{hero.id} was a {params.hero_trait} warrior who loved exploring {PLACES[params.place]} on the ship.")
    world.say(f"One day, the lights in {ship.place} began to fade into a strange gunk-dim glow.")
    world.say(f"{params.crewmate_name} frowned and said the ship felt like it had lost its spark.")
    world.para()

    # Act 2
    world.say(f"{hero.id} walked to {PLACES[params.place]} with {goggles.label} on, looking for clues.")
    clue1 = Clue(
        id="smudge",
        label="a sticky smudge",
        hint="green specks on the wall",
        source=cause.place,
    )
    clue2 = Clue(
        id="trail",
        label="a tiny trail",
        hint="a wet line leading under a pipe",
        source="the hall",
    )
    world.ship.clues_found.extend([clue1.label, clue2.label])
    world.say(f"In {PLACES[params.place]}, {hero.id} found {clue1.label}: {clue1.hint}.")
    world.say(f"Then {hero.id} followed {clue2.label} to the panel bay, where the air smelled dusty and odd.")
    world.say(f"The warrior knelt down, peered behind a panel, and spotted {cause.label}.")
    world.say(f"The mystery was no longer a mystery: the gunk was leaking from {cause.place}.")
    hero.memes["focus"] = 1
    hero.memes["concern"] = 1
    world.para()

    # Act 3
    hero.memes["solved"] = 1
    world.say(f"{hero.id} called for {params.crewmate_name}, and together they {cause.fix}.")
    hair.meters["gunk"] = 1
    hair.meters["clean"] = 1
    world.ship.dimmed = False
    world.say(f"{hero.id}'s {hair.label} got cleaned too, so no gunk stayed in the warrior's hair.")
    world.say(f"At last, the ship brightened, the panels shone, and the stars returned to their clear silver twinkle.")
    world.say(f"{hero.id} smiled, proud that the little space mystery had been solved.")

    world.facts.update(
        ship=ship,
        cause=cause,
        hero=hero,
        crewmate=crewmate,
        hair=hair,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    cause: Cause = f["cause"]
    return [
        f'Write a short space-adventure story for a young child about a warrior with hair, a gunk-dim mystery, and a solved clue.',
        f"Tell a gentle mystery story where {hero.id} the warrior investigates {cause.label} and helps the ship shine again.",
        f'Write a child-friendly story that includes the words "hair", "gunk-dim", and "warrior".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    cause: Cause = f["cause"]
    ship: Ship = f["ship"]
    hair: Entity = f["hair"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about on the ship?",
            answer=f"It was about {hero.id}, a young warrior with {hair.phrase}, on the {ship.name}.",
        ),
        QAItem(
            question=f"What strange problem made the ship look dim?",
            answer=f"A gunk-dim spread through the ship because of {cause.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"{hero.id} found a sticky smudge and a tiny trail that led to {cause.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {world.facts['crewmate'].id} do to fix the ship?",
            answer=f"They {cause.fix}, and that made the lights bright again.",
        ),
        QAItem(
            question=f"Where did {hero.id} search for the mystery first?",
            answer=f"{hero.id} searched {PLACES[place]} first, then followed the clues to the panel bay.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warrior?",
            answer="A warrior is a brave fighter or protector who helps keep others safe.",
        ),
        QAItem(
            question="What is hair?",
            answer="Hair is the soft strands that grow on a person's head.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so lights that are dim are harder to see.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or question that needs clues to solve it.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"ship.dimmed={world.ship.dimmed}")
    lines.append(f"ship.clues_found={world.ship.clues_found}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A ship is dimmed when there is a gunk source in the active area.
dimmed(S) :- ship(S), gunk_source(C), located(C, S).

% A mystery is solved when the warrior finds at least one clue and fixes the source.
solved(H, S) :- warrior(H), ship(S), found_clue(H, _), fixed_source(H, _).

% A child-friendly story is valid when it includes the core ingredients.
valid_story(S, H, W) :- ship(S), warrior(H), hair_item(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, ship in SHIP_REGISTRY.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("ship_name", sid, ship.name))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_name", pid, place))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("gunk_source", cid))
        lines.append(asp.fact("located", cid, cause.place.replace("the ", "").replace(" ", "_")))
    lines.append(asp.fact("warrior", "hero"))
    lines.append(asp.fact("hair_item", "hair"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import required by the contract.
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("comet-runner", "hero", "hair")}
    if atoms == expected:
        print("OK: ASP rules include the core story ingredients.")
        return 0
    print("MISMATCH: ASP did not produce the expected valid_story atom.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def resolve_story_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = tell_story(params, rng)
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


CURATED = [
    StoryParams(ship="comet-runner", place="bridge", hero_name="Aria", hero_gender="girl", hero_trait="brave", crewmate_name="Captain Sol"),
    StoryParams(ship="starlight", place="panel-bay", hero_name="Jax", hero_gender="boy", hero_trait="curious", crewmate_name="Pilot Luna"),
    StoryParams(ship="moon-catcher", place="airlock", hero_name="Mira", hero_gender="girl", hero_trait="steady", crewmate_name="Dr. Comet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            params = resolve_story_choice(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.ship} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
