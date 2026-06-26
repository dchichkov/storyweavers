#!/usr/bin/env python3
"""
storyworlds/worlds/cheep_flashback_heartwarming.py
===================================================

A small heartwarming story world about a child, a cheeping chick, and a gentle
flashback that helps them do the caring thing.

Premise:
- A child hears a soft cheep.
- The cheep brings back a flashback about finding a tiny chick before.
- The child and parent use a simple caring plan to keep the chick warm and safe.
- The ending proves the chick is no longer lonely or cold.

The simulated world tracks physical meters and emotional memes:
- physical: cold, warm, safe, tired, full
- emotional: worry, care, joy, relief, tenderness

The flashback is part of the story action: a remembered earlier moment explains
why the current choice matters and how the child learned to help.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class CareMove:
    id: str
    verb: str
    gerund: str
    cue: str
    fix: str
    helps: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "garden": Setting(place="the garden", affords={"cheep"}),
    "porch": Setting(place="the porch", affords={"cheep"}),
    "barn": Setting(place="the barn", affords={"cheep"}),
}

MOVES = {
    "cheep": CareMove(
        id="cheep",
        verb="follow the cheep",
        gerund="following the cheep",
        cue="a soft cheep by the fence",
        fix="warm the chick in a scarf-lined basket",
        helps={"warm", "safe"},
        tags={"bird", "care", "warm"},
    ),
}

PRIZES = {
    "scarf": Prize(
        id="scarf",
        label="scarf",
        phrase="a soft little scarf",
        region="torso",
        genders={"girl", "boy"},
    ),
    "basket": Prize(
        id="basket",
        label="basket",
        phrase="a small woven basket",
        region="hands",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="basket_wrap",
        label="a scarf-lined basket",
        covers={"hands", "torso"},
        guards={"cold"},
        prep="put the chick in a scarf-lined basket",
        tail="carried the basket back inside",
    ),
    Gear(
        id="warm_hands",
        label="warm hands",
        covers={"hands"},
        guards={"cold"},
        prep="cup the chick in warm hands",
        tail="held the chick close until it stopped shivering",
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ruby"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Ben", "Owen"]


@dataclass
class StoryParams:
    place: str
    move: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


ASP_RULES = r"""
place(garden). place(porch). place(barn).
move(cheep).
prize(scarf). prize(basket).
gender(girl). gender(boy).
affords(garden,cheep). affords(porch,cheep). affords(barn,cheep).
worn_on(scarf,torso). worn_on(basket,hands).
gear(basket_wrap). gear(warm_hands).
covers(basket_wrap,hands). covers(basket_wrap,torso).
covers(warm_hands,hands).
guards(basket_wrap,cold). guards(warm_hands,cold).

valid(Place,Move,Prize,Gender) :- affords(Place,Move), prize(Prize), gender(Gender),
                                  worn_on(Prize,R), covers(_,R), guards(_,cold).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for mv in sorted(s.affords):
            lines.append(asp.fact("affords", pid, mv))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for move in MOVES:
            for prize in PRIZES:
                if move == "cheep":
                    combos.append((place, move, prize))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming cheep story world with a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def reason_check(args: argparse.Namespace) -> None:
    if args.move and args.move != "cheep":
        raise StoryError("This world only supports the soft cheep story.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize does not fit that child in this world.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reason_check(args)
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.move is None or c[1] == args.move)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, move, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, move=move, prize=prize, name=name, gender=gender, parent=parent)


def _do_cheep(world: World, child: Entity) -> None:
    child.memes["tenderness"] = child.memes.get("tenderness", 0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.meters["listening"] = child.meters.get("listening", 0) + 1


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    chick = world.add(Entity(id="Chick", kind="character", type="bird", label="tiny chick"))
    basket = world.add(Entity(id=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    basket.worn_by = child.id

    world.say(f"{child.id} was in {world.setting.place} when a soft cheep floated from the fence.")
    _do_cheep(world, child)
    world.say(f"The sound made {child.id} stop and listen. {child.pronoun().capitalize()} had heard that same cheep before.")

    world.para()
    world.say(
        f"The cheep brought a flashback: on another day, {child.id} had found a tiny chick "
        f"shivering under a leaf. {child.pronoun().capitalize()} had cupped {chick.pronoun('object')} "
        f"in {child.pronoun('possessive')} hands until {chick.pronoun()} cheeped again."
    )
    child.memes["care"] = child.memes.get("care", 0) + 1
    chick.meters["cold"] = 1.0
    chick.memes["worry"] = 1.0

    world.para()
    world.say(
        f"Now the chick was back, and it looked cold again. {child.id} wanted to help right away, "
        f"but {child.pronoun('possessive')} {params.parent} worried the little bird might be too cold to stay outside."
    )
    world.say(
        f'{child.id} remembered the old feeling and said, "We can keep it warm first."'
    )

    gear = GEAR[0] if params.prize == "basket" else GEAR[1]
    world.para()
    world.say(
        f'{params.parent.capitalize()} nodded and helped with {gear.label}. Together they {gear.prep}, '
        f"then walked slowly toward the nest."
    )
    chick.meters["warm"] = 1.0
    chick.meters["safe"] = 1.0
    chick.meters["cold"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1

    world.say(
        f"At the nest, the chick hopped in and gave a bright cheep. {child.id} smiled because the tiny bird "
        f"was safe, warm, and no longer alone."
    )
    world.facts.update(child=child, parent=parent, chick=chick, basket=basket, gear=gear, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a short heartwarming story for a young child that includes the word "cheep" and a flashback.',
        f"Tell a gentle story about {p.name} in {world.setting.place} who hears a cheep, remembers an earlier moment, and helps a tiny chick.",
        "Write a simple story where a remembered cheep helps someone choose the caring thing to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    chick = f["chick"]
    params = f["params"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {child.id} hear in {world.setting.place}?",
            answer=f"{child.id} heard a soft cheep from the fence.",
        ),
        QAItem(
            question=f"What did the cheep make {child.id} remember?",
            answer=f"It made {child.id} remember finding the tiny chick on another day and warming it with careful hands.",
        ),
        QAItem(
            question=f"Why did {params.parent} worry before they helped the chick?",
            answer=f"{params.parent.capitalize()} worried the little bird was cold and needed to be kept warm before it went back to the nest.",
        ),
        QAItem(
            question=f"How did {child.id} and {params.parent} help the chick?",
            answer=f"They used {gear.label} and carried the chick back to its nest so it could stay warm and safe.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and relieved when the chick cheeped brightly from its nest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a cheep sound like?",
            answer="A cheep is a small, soft bird sound, like a tiny call from a chick.",
        ),
        QAItem(
            question="What do baby birds often need?",
            answer="Baby birds often need warmth, care, and a safe place near their nest.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(place="garden", move="cheep", prize="basket", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="porch", move="cheep", prize="scarf", name="Leo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:")
        for t in combos:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
