#!/usr/bin/env python3
"""
cover_fault_row_teamwork_comedy.py
===================================

A small, self-contained storyworld about a teamwork mishap in a row of things:
a cover goes wrong, a fault appears, and everyone has to work together with a
silly, child-friendly comedy turn.

Premise:
- A small group is arranging a neat row of fragile items.
- They have a cover to keep the items safe.
- One wrong move creates a fault in the cover.
- The group must use teamwork to fix the row before the wind makes everything
  even sillier.

The story engine simulates:
- physical meters: wobble, broken, covered, wet, fixed
- emotional memes: worry, blame, teamwork, relief, laughter

The ending always proves change:
- the fault is fixed,
- the row is safe,
- the group laughs together.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    phrase: str
    protects: set[str]
    can_fix: set[str]
    comedy: str
    tail: str
    plural: bool = False


@dataclass
class Fault:
    id: str
    label: str
    phrase: str
    cause: str
    mess: str
    risk: str
    target: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.windy: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.windy = self.windy
        return clone


def _r_cover_slip(world: World) -> list[str]:
    out: list[str] = []
    cover = world.entities.get("cover")
    if not cover:
        return out
    if cover.meters.get("fault", 0.0) < THRESHOLD:
        return out
    sig = ("slip", cover.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cover.meters["wobble"] = cover.meters.get("wobble", 0.0) + 1
    out.append("The cover slipped sideways with a tiny squeak.")
    return out


def _r_row_unsteady(world: World) -> list[str]:
    out: list[str] = []
    row = world.entities.get("row")
    cover = world.entities.get("cover")
    if not row or not cover:
        return out
    if cover.meters.get("fault", 0.0) < THRESHOLD:
        return out
    if row.meters.get("protected", 0.0) >= THRESHOLD:
        return out
    sig = ("unsteady", row.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    row.meters["wobble"] = row.meters.get("wobble", 0.0) + 1
    out.append("The row began to wobble like a line of sleepy ducks.")
    return out


def _r_wind_mess(world: World) -> list[str]:
    out: list[str] = []
    row = world.entities.get("row")
    cover = world.entities.get("cover")
    if not row or not cover:
        return out
    if not world.windy:
        return out
    if cover.meters.get("fixed", 0.0) >= THRESHOLD:
        return out
    sig = ("wind", row.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    row.meters["mess"] = row.meters.get("mess", 0.0) + 1
    out.append("A gust puffed through and made the row look even sillier.")
    return out


CAUSAL_RULES = [
    _r_cover_slip,
    _r_row_unsteady,
    _r_wind_mess,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                lines.extend(sents)
    if narrate:
        for s in lines:
            world.say(s)
    return lines


def team_help(world: World, helpers: list[Entity], cover: Entity, row: Entity) -> None:
    names = ", ".join(h.name for h in helpers[:-1]) + f", and {helpers[-1].name}" if len(helpers) > 2 else " and ".join(h.name for h in helpers)
    world.say(f"{names} leaned in together because this was a teamwork job.")
    for h in helpers:
        h.memes["teamwork"] = h.memes.get("teamwork", 0.0) + 1
    cover.meters["fixed"] = cover.meters.get("fixed", 0.0) + 1
    row.meters["protected"] = row.meters.get("protected", 0.0) + 1
    cover.meters["fault"] = 0.0
    row.meters["wobble"] = 0.0
    propagate(world, narrate=True)


SETTINGS = {
    "hall": Setting(place="the hall", affords={"row"}),
    "classroom": Setting(place="the classroom", affords={"row"}),
    "shed": Setting(place="the shed", affords={"row"}),
}

COVERS = {
    "sheet": Cover(
        id="cover",
        label="sheet cover",
        phrase="a big cloth cover",
        protects={"row"},
        can_fix={"tear"},
        comedy="It flapped like a startled flag.",
        tail="They tugged it smooth again and tucked the corners down.",
    ),
    "lid": Cover(
        id="cover",
        label="plastic cover",
        phrase="a shiny plastic cover",
        protects={"row"},
        can_fix={"crack"},
        comedy="It made a very serious squeak for such a silly-looking thing.",
        tail="They pressed it flat and clapped off the wrinkles.",
    ),
}

FAULTS = {
    "tear": Fault(
        id="fault",
        label="tear",
        phrase="a little tear",
        cause="a loose corner",
        mess="flap",
        risk="the row could get dusty",
        target="row",
    ),
    "crack": Fault(
        id="fault",
        label="crack",
        phrase="a small crack",
        cause="a bump from an elbow",
        mess="tilt",
        risk="the row could get exposed",
        target="row",
    ),
}

PEOPLE = {
    "Ada": ("girl", "curious"),
    "Milo": ("boy", "cheerful"),
    "Nia": ("girl", "quick"),
    "Otto": ("boy", "lively"),
}

TRAITS = ["curious", "cheerful", "quick", "lively", "gentle", "brave"]


@dataclass
class StoryParams:
    place: str
    cover: str
    fault: str
    names: list[str]
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy teamwork story about a cover, a fault, and a row.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--name", action="append")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    cover = args.cover or rng.choice(list(COVERS))
    fault = args.fault or rng.choice(list(FAULTS))
    if fault not in COVERS[cover].can_fix:
        raise StoryError("That cover cannot honestly fix that fault.")
    if place not in SETTINGS or "row" not in SETTINGS[place].affords:
        raise StoryError("This place cannot support the row story.")
    names = args.name or rng.sample(list(PEOPLE), k=3)
    return StoryParams(place=place, cover=cover, fault=fault, names=names[:3])


def _story_setup(world: World, hero: Entity, friends: list[Entity], cover: Entity, row: Entity) -> None:
    world.say(f"{hero.name} loved arranging the row at {world.setting.place}.")
    world.say(f"Beside the row sat {cover.phrase}, which was supposed to keep everything safe.")
    world.say(f"{hero.name} and friends kept the row neat because a tidy row made them grin.")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    for f in friends:
        f.memes["joy"] = f.memes.get("joy", 0.0) + 1


def _story_turn(world: World, hero: Entity, friends: list[Entity], cover: Entity, row: Entity, fault: Fault) -> None:
    world.para()
    world.say(f"Then {fault.cause} made {fault.phrase} appear in the cover.")
    cover.meters["fault"] = 1.0
    cover.memes["worry"] = cover.memes.get("worry", 0.0) + 1
    row.memes["worry"] = row.memes.get("worry", 0.0) + 1
    world.say(f"{cover.comedy}")
    world.windy = True
    propagate(world, narrate=True)
    world.say(f"{hero.name} pointed and said, 'Uh-oh, the cover has a fault!'")
    hero.memes["blame"] = hero.memes.get("blame", 0.0) + 1
    for f in friends:
        f.memes["blame"] = f.memes.get("blame", 0.0) + 0.5
    world.say("Nobody wanted to panic, because panicking does not help a row.")

def _story_fix(world: World, hero: Entity, friends: list[Entity], cover: Entity, row: Entity, fault: Fault) -> None:
    world.para()
    world.say(f"'{fault.risk},' said {friends[0].name}, 'so let's team up!'")
    world.say(f"{friends[1].name} held one side while {hero.name} held the other side.")
    world.say(f"{friends[2].name} found the tiny patch and grinned like a secret hero.")
    team_help(world, [hero] + friends, cover, row)
    world.say(f"{cover.tail}")
    world.say(f"After that, the row stood straight again, and the wind had nothing funny left to do.")
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["laughter"] = hero.memes.get("laughter", 0.0) + 1
    for f in friends:
        f.memes["relief"] = f.memes.get("relief", 0.0) + 1
        f.memes["laughter"] = f.memes.get("laughter", 0.0) + 1


def tell(place: str, cover_key: str, fault_key: str, names: list[str]) -> World:
    world = World(SETTINGS[place])
    cover_def = COVERS[cover_key]
    fault = FAULTS[fault_key]
    hero_name = names[0]
    friend_names = names[1:4]
    hero = world.add(Entity(id=hero_name, kind="character", type=PEOPLE.get(hero_name, ("girl", "curious"))[0], label=hero_name))
    friends = [world.add(Entity(id=n, kind="character", type=PEOPLE.get(n, ("boy", "kind"))[0], label=n)) for n in friend_names]
    cover = world.add(Entity(id="cover", type="cover", label=cover_def.label, phrase=cover_def.phrase))
    row = world.add(Entity(id="row", type="row", label="row", phrase="a neat row"))
    _story_setup(world, hero, friends, cover, row)
    _story_turn(world, hero, friends, cover, row, fault)
    _story_fix(world, hero, friends, cover, row, fault)
    world.facts.update(hero=hero, friends=friends, cover=cover, row=row, fault=fault, cover_def=cover_def, place=place)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for cover_key, cover_def in COVERS.items():
            for fault_key, fault in FAULTS.items():
                if fault_key in cover_def.can_fix:
                    out.append((place, cover_key, fault_key))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child about a cover, a fault, and a row at {f["place"]}.',
        f"Tell a teamwork story where {f['hero'].name} and friends fix a {f['fault'].label} in the {f['cover_def'].label}.",
        "Make the ending funny, safe, and cheerful, with the row standing neat again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friends = f["friends"]
    cover_def = f["cover_def"]
    fault = f["fault"]
    return [
        QAItem(
            question=f"What did {hero.name} and friends want to keep safe at {f['place']}?",
            answer="They wanted to keep the row safe under the cover.",
        ),
        QAItem(
            question=f"What went wrong with the {cover_def.label}?",
            answer=f"A {fault.label} appeared in the cover, and that made the row wobble a little.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They used teamwork: everyone held, patched, and smoothed the cover until the fault was gone.",
        ),
        QAItem(
            question=f"Why was the ending funny?",
            answer="Because the wind tried to help with a silly puff, but the friends fixed everything first and laughed together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other do one job together.",
        ),
        QAItem(
            question="What is a cover?",
            answer="A cover is something you put over another thing to protect it.",
        ),
        QAItem(
            question="What is a fault?",
            answer="A fault is a problem or break that makes something not work quite right.",
        ),
        QAItem(
            question="What is a row?",
            answer="A row is a line of things placed one after another.",
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
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"windy={world.windy}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
compatible(P,C,F) :- affords(P,row), cover(C), fault(F), fixable(C,F).
fixable(C,F) :- can_fix(C,F).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for c, cd in COVERS.items():
        lines.append(asp.fact("cover", c))
        for f in cd.can_fix:
            lines.append(asp.fact("can_fix", c, f))
    for f in FAULTS:
        lines.append(asp.fact("fault", f))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hall", cover="sheet", fault="tear", names=["Ada", "Milo", "Nia"]),
    StoryParams(place="classroom", cover="lid", fault="crack", names=["Nia", "Otto", "Ada"]),
]


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params.place, params.cover, params.fault, params.names)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = build_sample(params)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
