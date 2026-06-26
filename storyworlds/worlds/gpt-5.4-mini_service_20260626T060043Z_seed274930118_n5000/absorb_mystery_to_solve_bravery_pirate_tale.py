#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a crew, a mystery, and a brave choice.

Seed premise:
- A small crew hears a strange clue at sea.
- One pirate is afraid at first, then chooses bravery.
- The mystery is solved by observing, testing, and absorbing clues from the world.
- The ending proves something changed: the crew understands the secret and moves on.
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the harbor"
    waterway: bool = True
    hides_clues: bool = True


@dataclass
class Mystery:
    id: str
    clue: str
    hiding_place: str
    revealed_by: str
    solved_by: str
    absorb_word: str = "absorb"


@dataclass
class Ship:
    id: str
    label: str
    crew_spot: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", waterway=True, hides_clues=True),
    "island": Setting(place="a small island cove", waterway=True, hides_clues=True),
    "lagoon": Setting(place="a quiet lagoon", waterway=True, hides_clues=True),
}

MYSTERIES = {
    "whispering_map": Mystery(
        id="whispering_map",
        clue="a damp scrap of map that kept turning in the wind",
        hiding_place="inside a bottle floating near the dock",
        revealed_by="watching the bottle bump against the pier",
        solved_by="matching the torn corner to the captain's chart",
    ),
    "singing_shell": Mystery(
        id="singing_shell",
        clue="a shell that sang whenever the tide rose",
        hiding_place="under a pile of seaweed",
        revealed_by="listening for the little song",
        solved_by="following the tune to the hidden shell",
    ),
    "glimmer_coin": Mystery(
        id="glimmer_coin",
        clue="a gold coin that flashed only when the moon hit the water",
        hiding_place="in a crack between two rocks",
        revealed_by="waiting for the moonlight to move",
        solved_by="finding the shine and prying the coin free",
    ),
}

SHIPS = {
    "sloop": Ship(id="sloop", label="a little sloop", crew_spot="deck"),
    "cutter": Ship(id="cutter", label="a fast cutter", crew_spot="deck"),
    "skiff": Ship(id="skiff", label="a narrow skiff", crew_spot="bench"),
}

CREW_NAMES = ["Nell", "Milo", "Rae", "Toby", "June", "Ivy", "Finn", "Sana"]
CAPTAIN_NAMES = ["Captain Peg", "Captain Harlow", "Captain Mira"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    ship: str
    hero: str
    captain: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solvable when the place hides clues, the clue exists, and bravery
% helps the hero keep looking instead of turning away.
solvable(M) :- mystery(M), clue(M,_), hides_clues(P), at_place(M,P), brave(hero), can_absorb(M).

can_absorb(M) :- mystery(M), absorb_word(M,_).

valid_story(Place, Mystery, Ship) :- setting(Place), mystery(Mystery), ship(Ship),
                                     at_place(Mystery, Place), fits_ship(Ship, Place),
                                     solvable(Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.hides_clues:
            lines.append(asp.fact("hides_clues", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("at_place", mid, "harbor" if mid == "whispering_map" else ("island" if mid == "singing_shell" else "lagoon")))
        lines.append(asp.fact("absorb_word", mid, m.absorb_word))
    for sid, sh in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        lines.append(asp.fact("fits_ship", sid, "harbor"))
        lines.append(asp.fact("fits_ship", sid, "island"))
        lines.append(asp.fact("fits_ship", sid, "lagoon"))
    lines.append(asp.fact("brave", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    # Python gate and ASP gate both rely on the same constraint set here.
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    mapped = {(p, m, s) for (p, m, s) in cl}
    if py == mapped:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if mapped - py:
        print("  only in clingo:", sorted(mapped - py))
    if py - mapped:
        print("  only in python:", sorted(py - mapped))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            for ship in SHIPS:
                combos.append((place, mystery, ship))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.ship:
        combos = [c for c in combos if c[2] == args.ship]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery, ship = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(CREW_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    return StoryParams(place=place, mystery=mystery, ship=ship, hero=hero, captain=captain)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    ship = SHIPS[params.ship]
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type="pirate", label=params.hero))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))
    vessel = world.add(Entity(id=ship.id, type="ship", label=ship.label, phrase=ship.label))

    hero.memes["curiosity"] = 1
    hero.memes["fear"] = 1 if params.mystery == "whispering_map" else 0
    hero.memes["bravery"] = 0
    captain.memes["trust"] = 1

    world.facts.update(
        hero=hero,
        captain=captain,
        ship=vessel,
        mystery=mystery,
        setting=setting,
        params=params,
    )

    world.say(
        f"{hero.id} was a little pirate on {vessel.label}, always watching the water."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved a good mystery, but {hero.pronoun('possessive')} knees went wobbly when the sea got strange."
    )
    world.para()
    world.say(
        f"One day at {setting.place}, {hero.id} found {mystery.clue}."
    )
    world.say(
        f"It led to {mystery.hiding_place}, and nobody could tell what the clue meant yet."
    )
    world.para()
    world.say(
        f"{params.captain} said, \"We have to solve this, matey. Keep looking and let the clue soak into your head.\""
    )
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a deep breath and chose bravery instead of turning away."
    )
    world.say(
        f"{hero.id} kept {mystery.revealed_by}, even when the spray and shadows made the deck feel spooky."
    )
    world.para()
    world.say(
        f"At last, {hero.id} {mystery.solved_by}."
    )
    world.say(
        f"The mystery was solved, and the crew cheered as the sea looked ordinary again."
    )
    world.say(
        f"{hero.id} stood taller on the deck, proud that {hero.pronoun()} had absorbed the clue and found the answer."
    )

    world.facts["resolved"] = True
    world.facts["brave"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a short pirate tale for a young child that includes the word "absorb" and a mystery to solve.',
        f"Tell a gentle pirate story where {hero.id} must be brave enough to solve the {mystery.id.replace('_', ' ')}.",
        f"Write a tiny sea adventure about a pirate crew, a strange clue, and a brave choice that leads to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    mystery = f["mystery"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who was the brave pirate in the story?",
            answer=f"The brave pirate was {hero.id}. {hero.id} chose bravery and kept looking until the mystery was solved.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find?",
            answer=f"{hero.id} found {mystery.clue}. That clue led the crew toward the answer.",
        ),
        QAItem(
            question=f"Why did {captain.id} tell the crew to keep looking?",
            answer=f"{captain.id} wanted the crew to solve the mystery at {params.place}, so the pirate could absorb the clue and understand what it meant.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"At the end, {hero.id} solved the mystery, and the crew cheered because the strange sea puzzle finally made sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be brave?",
            answer="Being brave means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand right away.",
        ),
        QAItem(
            question="What does absorb mean?",
            answer="To absorb means to take something in and hold it, like a sponge taking in water or a mind taking in a clue.",
        ),
        QAItem(
            question="Why do sailors watch the sea carefully?",
            answer="Sailors watch the sea carefully because waves, weather, and hidden things can change quickly and give important clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="harbor", mystery="whispering_map", ship="sloop", hero="Nell", captain="Captain Peg"),
    StoryParams(place="island", mystery="singing_shell", ship="cutter", hero="Milo", captain="Captain Harlow"),
    StoryParams(place="lagoon", mystery="glimmer_coin", ship="skiff", hero="Rae", captain="Captain Mira"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale storyworld with mystery and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--hero")
    ap.add_argument("--captain")
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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for s in stories:
            print(s)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
