#!/usr/bin/env python3
"""
cell_magic_fairy_tale.py
========================

A small fairy-tale storyworld about a child, a cell, and a bit of magic.

Premise:
- A child finds or visits a tiny cell in a castle tower.
- A worried guardian fears the child will lose something precious or get stuck.
- A magical helper or object offers a safe, kind way through.
- The story ends with a concrete changed state: the cell is opened, brightened,
  or turned into a safe room, and the child leaves with something restored.

The world keeps a tiny simulation with physical meters and emotional memes.
It is intentionally small and constraint-checked: only reasonable combinations
are generated, and explicit invalid choices raise StoryError.

Style: fairy tale.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Ensure `results` can be imported when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"bright": 0.0, "locked": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "joy": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "witch"}
        male = {"boy", "prince", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    kind: str = "castle_cell"  # "castle_cell" | "tower_room" | "garden"
    stone: bool = True
    magic: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    noun_phrase: str
    power: str
    verb: str
    helps: set[str] = field(default_factory=set)
    safe_for: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    kind: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "tower_cell": Place(name="the tower cell", kind="castle_cell", stone=True, magic=True, affordances={"glow", "unlock"}),
    "garden_cell": Place(name="the garden cell", kind="garden_cell", stone=False, magic=True, affordances={"glow", "unlock"}),
}

CHILD_NAMES = ["Lina", "Mira", "Nia", "Owen", "Finn", "Elin", "Toby", "Rose"]
PARENT_TYPES = ["queen", "king", "witch", "wizard"]
TRAITS = ["brave", "gentle", "curious", "kind", "bright"]

CHARMS = {
    "moon_key": Charm(
        id="moon_key",
        label="moon key",
        noun_phrase="a silver moon key",
        power="unlocks old locks",
        verb="turn the moon key",
        helps={"unlock"},
        safe_for={"cell"},
    ),
    "lamp_spell": Charm(
        id="lamp_spell",
        label="lamp spell",
        noun_phrase="a warm lamp spell",
        power="makes dark corners glow",
        verb="speak the lamp spell",
        helps={"glow"},
        safe_for={"cell"},
    ),
    "rose_ward": Charm(
        id="rose_ward",
        label="rose ward",
        noun_phrase="a rose ward of soft light",
        power="keeps fear from growing",
        verb="trace the rose ward",
        helps={"calm"},
        safe_for={"cell"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        region="hand",
        kind="lantern",
    ),
    "cloak": Prize(
        id="cloak",
        label="cloak",
        phrase="a blue velvet cloak",
        region="torso",
        kind="cloak",
    ),
    "crown": Prize(
        id="crown",
        label="crown",
        phrase="a tiny gold crown",
        region="head",
        kind="crown",
    ),
}


@dataclass
class StoryParams:
    place: str
    charm: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def is_reasonable(place: Place, charm: Charm, prize: Prize) -> bool:
    if "cell" not in prize.id and place.kind == "castle_cell":
        return True
    if prize.region == "head" and "unlock" in charm.helps:
        return False
    if "unlock" in charm.helps and place.kind != "castle_cell":
        return False
    if "glow" in charm.helps and "cell" not in place.kind:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for cid, charm in CHARMS.items():
            for prid, prize in PRIZES.items():
                if is_reasonable(place, charm, prize):
                    out.append((pid, cid, prid))
    return out


def explain_rejection(place: Place, charm: Charm, prize: Prize) -> str:
    if "unlock" in charm.helps and prize.region == "head":
        return "(No story: a moon key cannot reasonably help with a crown on a head. Try a lantern or cloak instead.)"
    if "unlock" in charm.helps and place.kind != "castle_cell":
        return "(No story: the moon key only fits a locked cell, and this place is not a locked cell.)"
    if "glow" in charm.helps and "cell" not in place.kind:
        return "(No story: the lamp spell belongs in a cell or other dark stone room.)"
    return "(No story: that combination does not make a fairy-tale problem and fix.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not restricted by gender here; try {ok}.)"


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    charm = CHARMS[params.charm]
    prize = PRIZES[params.prize]

    world = World(place)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(id=prize.id, type=prize.kind, label=prize.label, phrase=prize.phrase, caretaker=guardian.id))
    item.meters["locked"] = 1.0

    # Act I: setup
    world.say(f"Once upon a time, {child.label} was a {params.trait} little {params.gender} who lived near {place.name}.")
    world.say(f"{child.label} loved {charm.noun_phrase} because {charm.power}.")
    world.say(f"One evening, {guardian.label} brought home {prize.phrase}, and {child.label} treasured it at once.")

    # Act II: tension
    world.para()
    world.say(f"At the end of a long day, {child.label} found a small cell in the old stone place.")
    world.say(f"{child.pronoun().capitalize()} wanted to go inside and {charm.verb}, but the cell door was locked tight.")
    child.memes["worry"] += 1
    guardian.memes["worry"] += 1
    world.say(f"{guardian.label} worried that the {prize.label} would be lost or dulled in the dark.")

    # Act III: turn and resolution
    world.para()
    if charm.verb == "turn the moon key":
        child.meters["bright"] += 1
        item.meters["locked"] = 0.0
        item.meters["clean"] += 1
        child.memes["hope"] += 1
        world.say(f"Then {child.label} lifted the moon key, whispered a tiny rhyme, and turned it in the lock.")
        world.say("The cell door opened with a soft click, and silver light spilled over the floor.")
    elif charm.verb == "speak the lamp spell":
        child.meters["bright"] += 1
        item.meters["clean"] += 1
        child.memes["hope"] += 1
        world.say(f"Then {child.label} spoke the lamp spell, and a warm glow rose around the cell door.")
        world.say("The dark corners softened, and the little room looked gentle instead of grim.")
    else:
        child.memes["fear"] = 0.0
        child.memes["joy"] += 1
        world.say(f"Then {child.label} traced the rose ward in the air, and fear shrank like mist in sunbeams.")
        world.say("The cell felt safe at last, and the child could stand near the prize without trembling.")

    guardian.memes["worry"] = 0.0
    guardian.memes["joy"] += 1
    world.say(f"In the end, {child.label} left the cell smiling, and {guardian.label} smiled too.")
    world.say(f"The {prize.label} stayed bright and safe, like treasure in a tale that had chosen kindness.")

    world.facts.update(
        child=child,
        guardian=guardian,
        prize=item,
        place=place,
        charm=charm,
        prize_cfg=prize,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    charm = f["charm"]
    prize = f["prize_cfg"]
    place = f["place"]
    return [
        f'Write a short fairy tale about {child.label}, a cell, and {charm.label}.',
        f"Tell a gentle story where a little {child.type} uses {charm.noun_phrase} in {place.name} and keeps {prize.phrase} safe.",
        f"Write a child-friendly tale that includes a locked cell and ends with a bright, happy change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    prize = f["prize_cfg"]
    charm = f["charm"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about near {place.name}?",
            answer=f"It was about {child.label}, a {child.pronoun('subject')} who lived near {place.name} with {guardian.label}.",
        ),
        QAItem(
            question=f"What did {child.label} use to change the locked cell?",
            answer=f"{child.label} used {charm.noun_phrase} to change the locked cell in a gentle way.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer=f"The {prize.label} stayed safe and bright, so the treasure could be kept without fear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cell in a fairy tale?",
            answer="A cell is a small room, often made of stone, that can be locked until a key or spell opens it.",
        ),
        QAItem(
            question="What does magic do in a fairy tale?",
            answer="Magic can change a locked door, brighten a dark room, or help a hero solve a hard problem kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(tower_cell).
place(garden_cell).

kind(tower_cell, castle_cell).
kind(garden_cell, garden_cell).

charm(moon_key).
charm(lamp_spell).
charm(rose_ward).

helps(moon_key, unlock).
helps(lamp_spell, glow).
helps(rose_ward, calm).

prize(lantern).
prize(cloak).
prize(crown).

region(lantern, hand).
region(cloak, torso).
region(crown, head).

valid(P, C, R) :- kind(P, castle_cell), helps(C, unlock), region(R, hand).
valid(P, C, R) :- kind(P, castle_cell), helps(C, glow), region(R, hand).
valid(P, C, R) :- kind(P, garden_cell), helps(C, calm), prize(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("kind", pid, p.kind))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("region", rid, r.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale storyworld about a cell and a little magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["queen", "king", "witch", "wizard"])
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
    if args.place and args.charm and args.prize:
        place, charm, prize = SETTINGS[args.place], CHARMS[args.charm], PRIZES[args.prize]
        if not is_reasonable(place, charm, prize):
            raise StoryError(explain_rejection(place, charm, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.charm is None or c[1] == args.charm)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, charm, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, charm=charm, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(place="tower_cell", charm="moon_key", prize="lantern", name="Lina", gender="girl", parent="queen", trait="brave"),
    StoryParams(place="tower_cell", charm="lamp_spell", prize="cloak", name="Owen", gender="boy", parent="king", trait="curious"),
    StoryParams(place="garden_cell", charm="rose_ward", prize="crown", name="Mira", gender="girl", parent="witch", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.name}: {p.charm} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
