#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/nummy_catalogue_tartar_happy_ending_space_adventure.py
===============================================================================================================

A small space-adventure storyworld built from the seed words:
nummy, catalogue, tartar.

Premise:
- A child on a tiny space station loves browsing a snack catalogue.
- A crunchy tartar-like space snack can leave sticky bits on teeth.
- A wise parent/companion worries about the mess and the later clean-up.

Turn:
- The child wants the nummy snack right away.
- The companion points out that the snack would leave tartar on the teeth.
- The child feels disappointed, then a safer snack plan appears.

Resolution:
- They choose a gentler space snack and a tooth-cleaning routine.
- The ending stays happy: the child still gets something nummy, and the station remains tidy.

This file is self-contained and uses only stdlib plus the shared Storyweavers
results container. ASP helpers are imported lazily only inside ASP functions.
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
    caretaker: Optional[str] = None
    eaten_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    offworld: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    nummy: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTING = Setting(place="the Moon Station", offworld=True, affords={"catalogue"})
CHARACTERS = {
    "child": ("girl", "boy"),
}

SNACKS = {
    "tartar": Snack(
        id="tartar",
        label="tartar crisps",
        phrase="a tin of nummy tartar crisps",
        nummy="nummy",
        mess="crumbly",
        risk="teeth",
        tags={"tartar", "catalogue", "nummy"},
        requires={"catalogue"},
    ),
    "comet_cookies": Snack(
        id="comet_cookies",
        label="comet cookies",
        phrase="a box of nummy comet cookies",
        nummy="nummy",
        mess="crumbly",
        risk="teeth",
        tags={"catalogue", "nummy"},
        requires={"catalogue"},
    ),
    "moon_milk": Snack(
        id="moon_milk",
        label="moon milk",
        phrase="a cold cup of moon milk",
        nummy="mild",
        mess="clean",
        risk="none",
        tags={"catalogue"},
        requires={"catalogue"},
    ),
    "star_pear": Snack(
        id="star pear",
        label="star pear slices",
        phrase="a little bowl of star pear slices",
        nummy="fresh",
        mess="clean",
        risk="none",
        tags={"catalogue"},
        requires={"catalogue"},
    ),
}

FIXES = [
    Fix(
        id="brush",
        label="toothbrush",
        phrase="the tiny ship toothbrush",
        guards={"teeth"},
        prep="brush their teeth first",
        tail="brushed their teeth and rinsed the crumbs away",
        tags={"catalogue"},
    ),
    Fix(
        id="napkin",
        label="napkin",
        phrase="a napkin",
        guards={"crumbly"},
        prep="open a napkin under the snack",
        tail="kept a napkin ready for the crumbs",
        tags={"catalogue"},
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nia", "Rosa"]
BOY_NAMES = ["Kai", "Ezra", "Noah", "Ivo", "Milo"]
TRAITS = ["brave", "curious", "bright", "cheerful", "spunky"]


def valid_combos() -> list[tuple[str, str]]:
    return [("moon_station", sid) for sid, snack in SNACKS.items() if "catalogue" in snack.requires]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "moon_station"), asp.fact("affords", "moon_station", "catalogue")]
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("nummy", sid, snack.nummy))
        lines.append(asp.fact("mess", sid, snack.mess))
        lines.append(asp.fact("risk", sid, snack.risk))
        for t in sorted(snack.tags):
            lines.append(asp.fact("tagged", sid, t))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Snack) :- setting(S), affords(S, catalogue), snack(Snack), tagged(Snack, catalogue).
needs_fix(Snack) :- risk(Snack, teeth), mess(Snack, crumbly).
safe_fix(Fix, Snack) :- fix(Fix), needs_fix(Snack), guards(Fix, teeth).
compatible(S, Snack) :- valid(S, Snack), (not needs_fix(Snack); safe_fix(_, Snack)).
#show valid/2.
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def story_valid_combos() -> list[tuple]:
    return [("moon_station", sid) for sid in SNACKS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld: nummy catalogue tartar and a happy ending.")
    ap.add_argument("--place", choices=["moon_station"], default="moon_station")
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    gender: str
    trait: str
    parent: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    snack = args.snack or rng.choice(list(SNACKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place="moon_station", snack=snack, name=name, gender=gender, trait=trait, parent=parent)


def predict_tartar(world: World, child: Entity, snack: Snack) -> bool:
    sim = world.copy()
    sim.get(child.id).meters["crumbs"] = sim.get(child.id).meters.get("crumbs", 0) + (1 if snack.mess == "crumbly" else 0)
    return snack.risk == "teeth" and sim.get(child.id).meters["crumbs"] >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    snack = SNACKS[params.snack]
    world.facts.update(child=child, parent=parent, snack=snack, params=params)

    world.say(f"On the Moon Station, {child.id} was a {params.trait} little {child.type} who loved the snack catalogue.")
    world.say(f"{child.pronoun().capitalize()} could point to the pictures and whisper that every page looked nummy.")
    world.say(f"One day, {child.id} found {snack.phrase} in the catalogue and wanted it right away.")

    world.para()
    if predict_tartar(world, child, snack):
        child.memes["want"] = 1
        world.say(f'{parent.pronoun().capitalize()} smiled, but said, "That snack could leave tartar on your teeth."')
        world.say(f"{child.id} frowned and looked at the shiny page again, wishing the nummy bits could jump into the bowl safely.")
        if "brush" in {fx.id for fx in FIXES}:
            fix = FIXES[0]
            world.say(f'"First, let us {fix.prep}," said {parent.pronoun("possessive")} {params.parent}.')
            world.say(f"They {fix.tail}, then opened the catalogue and chose moon milk too.")
            child.memes["joy"] = 1
            world.say(f"In the end, {child.id} sipped the moon milk, kept the snack, and had a happy ending with a clean smile.")
            world.facts["resolved"] = True
            world.facts["fix"] = fix
    else:
        world.say(f"{parent.pronoun().capitalize()} said the snack was just fine, and the two of them shared it under the window.")
        world.say(f"{child.id} finished it with a grin and there was no tartar trouble at all.")
        world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    snack = world.facts["snack"]
    return [
        f"Write a short space adventure for a young child about {p.name} and a nummy catalogue on a moon station.",
        f"Tell a child-friendly story where {p.name} wants {snack.phrase} but a parent worries about tartar on the teeth.",
        f"Create a happy-ending space tale that includes the words nummy, catalogue, and tartar.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    snack = world.facts["snack"]
    return [
        QAItem(question=f"What did {p.name} find in the catalogue?", answer=f"{p.name} found {snack.phrase} in the catalogue."),
        QAItem(question=f"Why did the parent worry about the snack?", answer=f"The parent worried because {snack.label} could leave tartar on the child's teeth."),
        QAItem(question="What made the ending happy?", answer=f"They chose a safer plan, kept the snack, and ended with a clean smile and moon milk."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a catalogue?", answer="A catalogue is a book or list that shows things you can choose, order, or buy."),
        QAItem(question="What is tartar on teeth?", answer="Tartar is a hard, sticky buildup that can collect on teeth if they are not cleaned well."),
        QAItem(question="Why is moon milk a gentle choice?", answer="Moon milk is a gentle choice because it is soft, drinkable, and does not leave crumbs on teeth."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_station", "tartar", "Mina", "girl", "curious", "mother"),
    StoryParams("moon_station", "comet_cookies", "Kai", "boy", "cheerful", "father"),
]


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
    a = set(asp_valid_combos())
    b = set(story_valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(a - b))
    print("Only in Python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2.\n#show compatible/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
