#!/usr/bin/env python3
"""
storyworlds/worlds/pastry_trench_pocket_mystery_to_solve_bedtime.py
====================================================================

A tiny bedtime-story world about a pastry, a trench coat, and a pocket-shaped
mystery that gets solved before sleep.

Seed premise:
---
A child is getting ready for bed when a pastry goes missing. A trench coat by
the door has a pocket that looks a little too full. The child and a grown-up
follow the clue, solve the mystery, and end the night calm and cozy.

World shape:
- physical meters: crumbs, fullness, tidiness, sleepiness, worry
- emotional memes: curiosity, relief, affection, surprise

The domain is intentionally small and constraint-checked:
- pastry + trench coat + pocket must form a sensible mystery
- explicit invalid combinations raise StoryError
- ASP facts/rules mirror the Python reasonableness gate
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    solved_by: str
    reveal: str
    mislead: str = ""


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"bedtime"}),
    "hallway": Setting(place="the hallway", indoor=True, affords={"bedtime"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"bedtime"}),
    "reading_nook": Setting(place="the reading nook", indoor=True, affords={"bedtime"}),
}

MYSTERIES = {
    "pastry_in_pocket": Mystery(
        id="pastry_in_pocket",
        clue="the pocket feels round and crumbly",
        solved_by="checking the trench coat pocket",
        reveal="a small pastry tucked safely inside the pocket",
        mislead="the child first wonders if the pastry ran away",
    ),
    "crumb_trail": Mystery(
        id="crumb_trail",
        clue="tiny crumbs lead from the table to the coat",
        solved_by="following the crumbs to the trench coat pocket",
        reveal="the pastry was hidden to keep it for breakfast",
        mislead="the child first thinks a mouse visited the room",
    ),
    "missing_sweet": Mystery(
        id="missing_sweet",
        clue="the plate is empty and the coat pocket looks puffy",
        solved_by="looking in the trench coat pocket before bed",
        reveal="the missing pastry is resting in a napkin in the pocket",
        mislead="the grown-up first checks under the pillow",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Ruby", "Zoe"]
BOY_NAMES = ["Finn", "Noah", "Theo", "Leo", "Ben", "Max", "Eli"]
TRAITS = ["curious", "gentle", "sleepy", "bright-eyed", "patient"]


def reasonableness_gate(place: str, mystery: str) -> bool:
    return place in SETTINGS and mystery in MYSTERIES


def explain_rejection(place: str, mystery: str) -> str:
    if place not in SETTINGS:
        return "(No story: the bedtime mystery needs a real room where the clue can be found.)"
    if mystery not in MYSTERIES:
        return "(No story: that mystery is not part of this little bedtime world.)"
    return "(No story: the chosen story ingredients do not fit together.)"


def aspire_facts() -> str:
    import asp  # lazy

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("solves", mid, m.solved_by))
        lines.append(asp.fact("reveals", mid, m.reveal))
    lines.append(asp.fact("thing", "pastry"))
    lines.append(asp.fact("thing", "trench"))
    lines.append(asp.fact("thing", "pocket"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, M) :- setting(P), mystery(M), affords(P, bedtime).
needs_pocket(M) :- mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{aspire_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m) for p in SETTINGS for m in MYSTERIES if reasonableness_gate(p, m)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery storyworld with a pastry, a trench coat, and a pocket.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.mystery and not reasonableness_gate(args.place, args.mystery):
        raise StoryError(explain_rejection(args.place, args.mystery))
    places = [p for p in SETTINGS if args.place is None or p == args.place]
    mysteries = [m for m in MYSTERIES if args.mystery is None or m == args.mystery]
    combos = [(p, m) for p in places for m in mysteries if reasonableness_gate(p, m)]
    if not combos:
        raise StoryError("(No valid bedtime mystery matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"sleepiness": 0.2}, memes={"curiosity": 0.3}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", meters={"sleepiness": 0.1}, memes={"warmth": 0.4}))
    pastry = world.add(Entity(id="pastry", type="pastry", label="pastry", phrase="a little pastry", owner=child.id, caretakers=[parent.id], carried_by=child.id, meters={"crumbs": 0.0, "freshness": 1.0}, memes={"value": 0.6}))
    trench = world.add(Entity(id="trench", type="trench", label="trench coat", phrase="a hanging trench coat", owner=parent.id, caretakers=[parent.id], worn_by=None, meters={"pockets": 1.0}, memes={"mystery": 0.6}))
    pocket = world.add(Entity(id="pocket", type="pocket", label="pocket", phrase="the trench coat pocket", owner="trench", meters={"fullness": 0.0, "crumbs": 0.0}, memes={"secrecy": 0.5}))
    mystery = MYSTERIES[params.mystery]
    world.facts.update(params=params, child=child, parent=parent, pastry=pastry, trench=trench, pocket=pocket, mystery=mystery)
    return world


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    pastry: Entity = f["pastry"]
    trench: Entity = f["trench"]
    pocket: Entity = f["pocket"]
    mystery: Mystery = f["mystery"]

    child.memes["curiosity"] += 0.8
    pastry.meters["crumbs"] += 0.2
    pocket.meters["fullness"] += 0.8
    pocket.meters["crumbs"] += 0.4
    trench.memes["mystery"] += 0.2

    world.say(
        f"At bedtime, {child.id} was still wide awake, even though the room had gone soft and quiet. "
        f"On the small plate there should have been a pastry, but now there was only a sweet smell and a few crumbs."
    )
    world.say(
        f"Near the door, a trench coat hung still. One pocket looked a little too round, and that was the first clue."
    )
    world.para()
    child.memes["worry"] = 0.5
    parent.memes["warmth"] += 0.4
    world.say(
        f'"Maybe the pastry is hiding," {child.id} whispered. {mystery.mislead or "The grown-up looked around the room."}'
    )
    world.say(
        f"{parent.pronoun().capitalize()} smiled and said, 'Let's solve the mystery together, one calm step at a time.'"
    )
    world.say(
        f"They followed {mystery.clue}, and soon {mystery.solved_by} made the answer feel close enough to touch."
    )
    world.para()
    child.memes["curiosity"] -= 0.1
    child.memes["relief"] = 1.0
    parent.memes["relief"] = 1.0
    pocket.meters["fullness"] = 0.0
    pastry.carried_by = child.id
    pastry.meters["crumbs"] = 0.0
    trench.memes["mystery"] = 0.0
    world.say(
        f"Inside the pocket, they found {mystery.reveal}. It had been tucked there so it would stay safe until morning."
    )
    world.say(
        f"{child.id} gave a small sleepy grin and held the pastry with both hands. {parent.pronoun().capitalize()} "
        f"laid the trench coat straight and neat by the door, and the room felt cozy again."
    )
    world.say(
        f"So the mystery was solved, the pastry was safe, and bedtime could finally be quiet and sweet."
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a gentle bedtime mystery story for a young child named {child.id} that includes a pastry, a trench coat, and a pocket.',
        f'Write a short bedtime story where {child.id} notices a pastry is missing and solves the mystery by looking in the trench coat pocket.',
        f'Write a cozy story about a child who follows crumbs, finds a clue in a pocket, and ends the night feeling relieved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"What was {child.id} trying to figure out at bedtime?",
            answer=f"{child.id} was trying to solve the mystery of where the pastry went.",
        ),
        QAItem(
            question=f"What clue made the trench coat seem important?",
            answer=f"The pocket looked round and crumbly, which made the trench coat seem like part of the mystery.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.pronoun('object')} solve the mystery?",
            answer=f"They solved it by checking the trench coat pocket and following the clue until the pastry was found.",
        ),
        QAItem(
            question=f"What was inside the pocket at the end?",
            answer=f"Inside the pocket was a small pastry tucked safely away.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the mystery solved, the pastry safe, and bedtime feeling cozy and quiet.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pastry?",
            answer="A pastry is a sweet baked food like a bun, tart, or little cake.",
        ),
        QAItem(
            question="What is a trench coat?",
            answer="A trench coat is a long coat with pockets that people wear over clothes.",
        ),
        QAItem(
            question="What is a pocket for?",
            answer="A pocket is a small space in clothing for holding little things safely.",
        ),
        QAItem(
            question="Why do people solve mysteries?",
            answer="People solve mysteries to find out what happened and make confusing things clear.",
        ),
    ]


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(place="bedroom", mystery="pastry_in_pocket", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="kitchen", mystery="crumb_trail", name="Finn", gender="boy", parent="father"),
    StoryParams(place="reading_nook", mystery="missing_sweet", name="Nora", gender="girl", parent="mother"),
]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible bedtime mystery stories:\n")
        for place, mystery in combos:
            print(f"  {place:12} {mystery}")
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and not reasonableness_gate(args.place, args.mystery):
        raise StoryError(explain_rejection(args.place, args.mystery))

    combos = [
        (p, m)
        for p in SETTINGS
        for m in MYSTERIES
        if (args.place is None or p == args.place)
        and (args.mystery is None or m == args.mystery)
        and reasonableness_gate(p, m)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        f'Write a cozy bedtime mystery about {child.id}, a pastry, a trench coat, and a pocket.',
        f'Write a short story where a child named {child.id} solves a missing-pastry mystery before sleep.',
        f'Write a gentle bedtime tale with a clue in a trench coat pocket and a calm happy ending.',
    ]


def asp_program(show: str) -> str:
    return f"{aspire_facts()}\n{ASP_RULES}\n{show}\n"


if __name__ == "__main__":
    main()
