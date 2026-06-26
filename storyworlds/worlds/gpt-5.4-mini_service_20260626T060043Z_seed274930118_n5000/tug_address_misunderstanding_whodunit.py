#!/usr/bin/env python3
"""
storyworlds/worlds/tug_address_misunderstanding_whodunit.py
===========================================================

A small whodunit story world about a tug, an address, and a misunderstanding.

Premise:
A child receives a wrapped parcel with a mysterious address tag. A helpful tug
at the ribbon, plus a wrong assumption about the address, sets off a little
mystery. The story resolves when the characters compare clues and deliver the
parcel to the right place.

The world model tracks physical state in meters and emotional state in memes:
- parcels can be tugged, opened, moved, and mislabeled
- characters can be puzzled, suspicious, relieved, and proud
- the final story must prove what changed by showing the corrected address and
  the solved misunderstanding

This world is intentionally narrow: fewer valid combinations, stronger stories.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tugged": 0.0, "moved": 0.0, "opened": 0.0}
        if not self.memes:
            self.memes = {"puzzled": 0.0, "suspicious": 0.0, "relieved": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    afford_address_check: bool = True
    afford_tug: bool = True


@dataclass
class Parcel:
    label: str
    phrase: str
    destination: str
    mistaken_destination: str
    seal: str
    contents: str


@dataclass
class StoryParams:
    place: str
    parcel: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_puzzled(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["puzzled"] < THRESHOLD:
            continue
        sig = ("puzzled", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{e.id} looked puzzled.")
    return out


def _r_suspicious(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    parcel = world.entities.get("parcel")
    if not hero or not parcel:
        return out
    if hero.memes["suspicious"] < THRESHOLD or parcel.meters["tugged"] < THRESHOLD:
        return out
    sig = ("suspicious",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{hero.id} began to suspect the address was wrong.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    parcel = world.entities.get("parcel")
    if not hero or not parcel:
        return out
    if parcel.meters["opened"] < THRESHOLD:
        return out
    if hero.memes["relieved"] >= THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relieved"] += 1
    out.append(f"{hero.id} felt relieved when the clue made sense.")
    return out


CAUSAL_RULES = [_r_puzzled, _r_suspicious, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "porch": Setting(place="the porch"),
    "hall": Setting(place="the front hall"),
    "kitchen": Setting(place="the kitchen"),
}

PARCELS = {
    "box": Parcel(
        label="box",
        phrase="a small cardboard box with a blue ribbon",
        destination="green gate",
        mistaken_destination="grey gate",
        seal="tied ribbon",
        contents="a tiny brass bell",
    ),
    "envelope": Parcel(
        label="envelope",
        phrase="a thick envelope with a wax seal",
        destination="red door",
        mistaken_destination="red postbox",
        seal="wax seal",
        contents="a folded map",
    ),
    "bundle": Parcel(
        label="bundle",
        phrase="a neat bundle wrapped in brown paper",
        destination="clock shop",
        mistaken_destination="dock shop",
        seal="twine knot",
        contents="a silver key",
    ),
}

HEROES = {
    "Mina": "girl",
    "Owen": "boy",
    "Iris": "girl",
    "Theo": "boy",
}

HELPERS = {
    "Mrs. Bell": "woman",
    "Mr. Finch": "man",
    "Aunt June": "woman",
    "Uncle Ray": "man",
}


@dataclass
class StoryParams:
    place: str
    parcel: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: tug, address, misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-kind", choices=["woman", "man"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, parcel) for place in SETTINGS for parcel in PARCELS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.parcel:
        combos = [c for c in combos if c[1] == args.parcel]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, parcel = rng.choice(combos)

    hero = args.hero or rng.choice(list(HEROES))
    hero_kind = args.hero_kind or HEROES.get(hero, rng.choice(["girl", "boy"]))
    helper = args.helper or rng.choice(list(HELPERS))
    helper_kind = args.helper_kind or HELPERS.get(helper, rng.choice(["woman", "man"]))
    return StoryParams(place=place, parcel=parcel, hero=hero, hero_kind=hero_kind, helper=helper, helper_kind=helper_kind)


def introduce(world: World, hero: Entity, helper: Entity, parcel: Entity, parcel_cfg: Parcel) -> None:
    world.say(f"{hero.id} found {parcel.phrase} on {world.setting.place}.")
    world.say(f"On the label was the address for {parcel_cfg.destination}, and that made {hero.id} curious.")
    world.say(f"{helper.id} said the parcel should be handled gently because the address mattered.")


def tug(world: World, hero: Entity, helper: Entity, parcel: Entity) -> None:
    hero.meters["tugged"] += 1
    parcel.meters["tugged"] += 1
    hero.memes["puzzled"] += 1
    helper.memes["puzzled"] += 1
    world.say(f"{hero.id} gave the ribbon a careful tug, and the tag turned just enough to look odd.")
    propagate(world, narrate=True)


def misunderstanding(world: World, hero: Entity, helper: Entity, parcel: Entity, parcel_cfg: Parcel) -> None:
    hero.memes["suspicious"] += 1
    helper.memes["puzzled"] += 1
    world.say(
        f"{hero.id} thought the parcel might belong at {parcel_cfg.mistaken_destination}, "
        f"but {helper.id} noticed the first street number was a clue."
    )
    propagate(world, narrate=True)


def solve_case(world: World, hero: Entity, helper: Entity, parcel: Entity, parcel_cfg: Parcel) -> None:
    parcel.meters["opened"] += 1
    hero.memes["suspicious"] = 0.0
    hero.memes["relieved"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"Together they checked the address again and discovered the parcel was meant for {parcel_cfg.destination}, not {parcel_cfg.mistaken_destination}."
    )
    world.say(
        f"When they opened it, they found {parcel_cfg.contents}, and the little mystery was solved at once."
    )
    world.say(
        f"{hero.id} carried the parcel to the right door, and {helper.id} smiled at the tidy answer hidden inside the address."
    )
    propagate(world, narrate=True)


def tell(setting: Setting, parcel_cfg: Parcel, hero_name: str, hero_kind: str, helper_name: str, helper_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_kind, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_name))
    parcel = world.add(Entity(id="parcel", kind="thing", type=parcel_cfg.label, label=parcel_cfg.label, phrase=parcel_cfg.phrase, owner=helper.id))

    introduce(world, hero, helper, parcel, parcel_cfg)
    world.para()
    tug(world, hero, helper, parcel)
    misunderstanding(world, hero, helper, parcel, parcel_cfg)
    world.para()
    solve_case(world, hero, helper, parcel, parcel_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        parcel=parcel,
        parcel_cfg=parcel_cfg,
        setting=setting,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parcel_cfg = f["parcel_cfg"]
    return [
        f"Write a child-friendly whodunit about a tug, an address, and a misunderstanding.",
        f"Tell a short mystery story where {hero.label} and {helper.label} inspect a parcel addressed to {parcel_cfg.destination}.",
        f"Write a simple story that begins with a careful tug on a parcel and ends with the address being checked again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parcel_cfg = f["parcel_cfg"]
    parcel = f["parcel"]

    return [
        QAItem(
            question=f"What did {hero.label} tug on at {world.setting.place}?",
            answer=f"{hero.label} tugged on {parcel.phrase}. That tug made the address tag turn and caused the misunderstanding.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding about the parcel?",
            answer=f"There was a misunderstanding because the tag looked like it might point to {parcel_cfg.mistaken_destination}, but the real address was {parcel_cfg.destination}.",
        ),
        QAItem(
            question=f"How did they solve the little mystery?",
            answer=f"They checked the address again, opened the parcel, and found {parcel_cfg.contents}. After that, they knew it belonged at {parcel_cfg.destination}.",
        ),
        QAItem(
            question=f"Who helped {hero.label} with the parcel?",
            answer=f"{helper.label} helped {hero.label} notice the clues and keep the parcel safe until the right address was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an address?",
            answer="An address is the set of words and numbers that tells you where a person, house, or parcel should go.",
        ),
        QAItem(
            question="Why do people tug things gently when they are trying to be careful?",
            answer="People tug gently so they can check or move something without breaking it.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first, but later learns the truth.",
        ),
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a tale where the characters look for clues and figure out what really happened.",
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
        lines.append(f"  {e.id:8} ({e.kind:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="porch", parcel="box", hero="Mina", hero_kind="girl", helper="Mrs. Bell", helper_kind="woman"),
    StoryParams(place="hall", parcel="envelope", hero="Owen", hero_kind="boy", helper="Mr. Finch", helper_kind="man"),
    StoryParams(place="kitchen", parcel="bundle", hero="Iris", hero_kind="girl", helper="Aunt June", helper_kind="woman"),
]


ASP_RULES = r"""
% A parcel is interesting when it is tugged and its address is checked.
interesting(parcel) :- tugged(parcel).
misunderstanding(parcel) :- interesting(parcel), address_needs_check(parcel).
solved(parcel) :- misunderstanding(parcel), address_checked(parcel).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for pid, p in PARCELS.items():
        lines.append(asp.fact("parcel", pid))
        lines.append(asp.fact("address_to", pid, p.destination))
        lines.append(asp.fact("mistaken_for", pid, p.mistaken_destination))
        lines.append(asp.fact("contents", pid, p.contents))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.parcel:
        combos = [c for c in combos if c[1] == args.parcel]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, parcel = rng.choice(combos)
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    hero_kind = args.hero_kind or HEROES[hero]
    helper_kind = args.helper_kind or HELPERS[helper]
    return StoryParams(place=place, parcel=parcel, hero=hero, hero_kind=hero_kind, helper=helper, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PARCELS[params.parcel], params.hero, params.hero_kind, params.helper, params.helper_kind)
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
        import storyworlds.asp as asp
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
            header = f"### {p.hero}: {p.parcel} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
