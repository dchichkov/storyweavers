#!/usr/bin/env python3
"""
Story world: coffin yelp surprise curiosity moral value comedy.

A small, self-contained simulation about a curious kid, an unexpected coffin
prop, a startled yelp, and a funny moral-value lesson about honesty and
thoughtfulness.
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
# Core domain data
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the costume room"
    affordance: str = "hide and seek"


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    surprise: str
    kind: str = "coffin"


@dataclass
class StoryParams:
    place: str
    prop: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    "attic": Setting(place="the attic", affordance="dusty dress-up games"),
    "basement": Setting(place="the basement", affordance="pretend treasure hunts"),
    "playroom": Setting(place="the playroom", affordance="hide and seek"),
}

PROPS = {
    "toy_coffin": Prop(
        id="toy_coffin",
        label="toy coffin",
        phrase="a tiny black toy coffin with shiny silver paint",
        surprise="looked spooky but was only pretend",
        kind="coffin",
    ),
    "cardboard_coffin": Prop(
        id="cardboard_coffin",
        label="cardboard coffin",
        phrase="a cardboard coffin for a school puppet show",
        surprise="was a silly prop for the puppet stage",
        kind="coffin",
    ),
}

NAMES = ["Mia", "Nora", "Theo", "Ben", "Ava", "Leo", "Zoe", "Milo"]
TRAITS = ["curious", "cheerful", "silly", "playful", "brave"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world with coffin, yelp, surprise, curiosity, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def _valid_combo(place: str, prop: str) -> bool:
    return place in SETTINGS and prop in PROPS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    prop = args.prop or rng.choice(list(PROPS))
    if not _valid_combo(place, prop):
        raise StoryError("No valid story matches those choices.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, prop=prop, hero_name=name, hero_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    prop = PROPS[params.prop]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="parent"))
    item = world.add(Entity(id="prop", kind="thing", type=prop.kind, label=prop.label, phrase=prop.phrase, owner=hero.id))

    # Story state
    hero.memes["curiosity"] = 1.0
    hero.memes["surprise"] = 1.0
    parent.memes["moral_value"] = 1.0
    item.meters["stage"] = 1.0

    world.say(
        f"{hero.id} was a {rng_trait(params)} child who loved {setting.affordance} in {setting.place}."
    )
    world.say(
        f"One day, {hero.id} found {item.phrase}. It {prop.surprise}, and {hero.id} gave a tiny yelp."
    )

    world.para()
    world.say(
        f"{hero.id} peeked closer instead of running away, because curiosity tickled harder than fear."
    )
    world.say(
        f"{hero.id}'s {parent.label} came over, smiled, and said the coffin was only a prop for pretend play."
    )

    world.para()
    world.say(
        f"{hero.id} laughed at the silly mix-up. Then {hero.id} told the truth about the yelp and helped carry the prop back."
    )
    world.say(
        f"That made the room feel calmer, and everyone remembered that honesty can turn a surprise into a joke."
    )

    world.facts.update(hero=hero, parent=parent, item=item, setting=setting, prop=prop)
    story = world.render()

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def rng_trait(params: StoryParams) -> str:
    return "curious"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prop = f["prop"]
    return [
        f'Write a funny story for a small child about {hero.id} discovering {prop.label}.',
        f"Tell a comedy story where a kid gets a yelp from a surprise in the room, then learns a moral value lesson.",
        f'Write a gentle story that includes the words "coffin" and "yelp" and ends with kindness and honesty.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {prop.phrase}. It was a coffin prop, not something scary for real.",
        ),
        QAItem(
            question=f"Why did {hero.id} yelp?",
            answer=f"{hero.id} yelped because the coffin looked surprising at first, before the grown-up explained it was only pretend.",
        ),
        QAItem(
            question=f"What moral value did {parent.label} show?",
            answer=f"{parent.label.capitalize()} showed honesty and calm kindness by explaining the surprise and helping {hero.id} understand it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What does a yelp usually sound like?",
            answer="A yelp is a quick little cry of surprise, like when someone gets startled for a moment.",
        ),
        QAItem(
            question="Why can honesty be a good moral value?",
            answer="Honesty helps people trust each other and makes it easier to fix a misunderstanding kindly.",
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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(attic). place(basement). place(playroom).
prop(toy_coffin). prop(cardboard_coffin).
valid(P,L) :- place(P), prop(L).
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {(p, l) for p in SETTINGS for l in PROPS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for p, l in combos:
            print(f"  {p:10} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="attic", prop="toy_coffin", hero_name="Mia", hero_type="girl", parent_type="mother"),
            StoryParams(place="basement", prop="cardboard_coffin", hero_name="Theo", hero_type="boy", parent_type="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
