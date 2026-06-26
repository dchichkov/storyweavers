#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/davenport_gypsy_enforce_cautionary_flashback_comedy.py
===============================================================================================================

A small, self-contained story world built from the seed words:
davenport, gypsy, enforce.

Premise:
- A child wants to do a messy, funny thing on a davenport.
- A parent remembers a cautionary flashback about a ruined couch.
- The parent enforces a safer plan instead.
- The ending is comedic, gentle, and concrete.

This world keeps the story grounded in state changes:
- the davenport can get dirty,
- the child's desire and the parent's concern can rise,
- a flashback can activate,
- a safer object can prevent the mess.

The world is intentionally tiny: one premise, one tension, one turn, one resolution.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the living room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shield:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""
        self.flashback: bool = False

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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "living_room": Setting(place="the living room", affords={"grape_juice"}),
    "den": Setting(place="the den", affords={"grape_juice"}),
}

ACTIVITIES = {
    "grape_juice": Activity(
        id="grape_juice",
        verb="sip grape juice on the couch",
        gerund="sipping grape juice",
        rush="dash at the juice box",
        mess="purple",
        soil="stained purple",
        keyword="davenport",
        tags={"juice", "purple", "comedy", "flashback"},
    ),
}

PRIZES = {
    "davenport": {
        "label": "davenport",
        "phrase": "the blue davenport",
        "type": "furniture",
    }
}

SHIELDS = [
    Shield(
        id="tray",
        label="a snack tray",
        prep="put the juice on a snack tray first",
        tail="moved the juice to the snack tray",
        guards={"purple"},
    ),
    Shield(
        id="towel",
        label="a big towel",
        prep="spread out a big towel first",
        tail="spread out the big towel",
        guards={"purple"},
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Tia", "Ruby", "Piper"]
BOY_NAMES = ["Owen", "Nico", "Eli", "Theo", "Milo"]
TRAITS = ["cheerful", "spirited", "silly", "curious", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                out.append((place, act_id, prize_id))
    return out


def reasonableness_gate(params: StoryParams) -> None:
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if params.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.activity != "grape_juice" or params.prize != "davenport":
        raise StoryError("This tiny world only supports grape juice and a davenport.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Unsupported gender.")


def introduce(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a {next((t for t in hero.memes.get('traits', [])), 'little')} {hero.type} "
        f"who loved the {prize.label} in {world.setting.place}."
    )
    world.say(
        f"Her {parent.pronoun('possessive')} favorite place to flop was the {prize.label}, "
        f"because it was soft and bouncy and made tiny squeaks."
    )


def flashback(world: World, parent: Entity, prize: Entity) -> None:
    world.flashback = True
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {parent.id} remembered a cautionary flashback: once, a cousin had spilled juice "
        f"on a different {prize.label}, and the stain looked like a purple pirate map."
    )
    world.say(
        f"That memory was so strong that {parent.id} almost laughed before {parent.pronoun('subject')} "
        f"started enforcing the no-spill rule."
    )


def attempt(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away and even lifted the juice box like a tiny captain."
    )
    world.say(
        f"But the plan was dangerous, because {activity.mess} juice would stain the {prize.label} fast."
    )


def enforce(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    parent.memes["enforce"] = parent.memes.get("enforce", 0.0) + 1
    world.say(
        f"'{hero.id}, we must enforce the careful rule,' {parent.id} said. "
        f"'Juice belongs on the tray, not on the {prize.label}.'"
    )


def choose_shield(activity: Activity) -> Optional[Shield]:
    for shield in SHIELDS:
        if activity.mess in shield.guards:
            return shield
    return None


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Shield]:
    shield = choose_shield(activity)
    if shield is None:
        return None
    world.say(
        f"Then {parent.id} smiled and said, 'How about we {shield.prep}?'"
    )
    return shield


def resolve(world: World, hero: Entity, parent: Entity, shield: Shield, activity: Activity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} nodded, and together they {shield.tail}. "
        f"After that, {hero.id} could still enjoy {activity.gerund}, and the {prize.label} stayed clean."
    )
    world.say(
        f"{hero.id} grinned at the silly rescue plan, and even the davenport seemed to sit up proudly."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: dict, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        memes={"traits": [trait, "silly"]},
    ))
    parent = world.add(Entity(
        id=parent_type.capitalize(),
        kind="character",
        type=parent_type,
    ))
    prize = world.add(Entity(
        id="davenport",
        type=prize_cfg["type"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
    ))

    introduce(world, hero, parent, prize)
    world.para()
    attempt(world, hero, activity, prize)
    flashback(world, parent, prize)
    enforce(world, parent, hero, activity, prize)
    world.para()
    shield = compromise(world, parent, hero, activity, prize)
    if shield:
        resolve(world, hero, parent, shield, activity, prize)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        shield=shield,
        flashback=world.flashback,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    return [
        'Write a short, funny story for a young child about a davenport, a juice spill, and a careful fix.',
        f"Tell a cautionary comedy where {hero.id} wants to {activity.verb}, but {parent.id} remembers a purple stain from the past.",
        "Write a flashback-style story that ends with a safe choice and a clean couch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {activity.verb} on the davenport.",
        ),
        QAItem(
            question=f"Why did {parent.id} start enforcing the careful rule?",
            answer=f"{parent.id} remembered a cautionary flashback about a purple juice stain on a davenport, so {parent.pronoun('subject')} wanted to prevent another mess.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They used a snack tray, so the juice stayed off the davenport and everyone ended up laughing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a davenport?",
            answer="A davenport is a soft couch or sofa that people can sit on in a living room or den.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What does it mean to enforce a rule?",
            answer="To enforce a rule means to make sure people follow it.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"flashback={world.flashback}")
    return "\n".join(lines)


ASP_RULES = r"""
% A davenport is at risk when grape juice is the activity.
at_risk(davenport, grape_juice).

% A shield is a compatible fix when it guards the mess.
fix(tray, grape_juice).
fix(towel, grape_juice).

valid_story(Place, Act, Prize) :- place(Place), activity(Act), prize(Prize), at_risk(Prize, Act), fix(_, Act).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for sh in SHIELDS:
        lines.append(asp.fact("shield", sh.id))
        for m in sorted(sh.guards):
            lines.append(asp.fact("guards", sh.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    py_set = {(p, a, pr) for (p, a, pr) in py_set}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("ASP-only:", sorted(asp_set - py_set))
    print("PY-only:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary flashback comedy about a davenport.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "grape_juice"
    prize = args.prize or "davenport"
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(items)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="living_room", activity="grape_juice", prize="davenport", name="Mina", gender="girl", parent="mother", trait="silly")
        samples = [generate(params)]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
