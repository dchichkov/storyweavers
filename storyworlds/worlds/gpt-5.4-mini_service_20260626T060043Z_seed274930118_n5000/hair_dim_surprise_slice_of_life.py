#!/usr/bin/env python3
"""
storyworlds/worlds/hair_dim_surprise_slice_of_life.py
=====================================================

A small slice-of-life story world about a gentle surprise around hair:
a child, a parent, a little worry, and a caring reveal that changes how
the morning feels.

The seed premise is a tiny everyday story:
- a child likes their hair a certain way
- someone notices the hair is getting in the way
- a surprise plan makes the child uneasy
- the surprise becomes kind, useful, and nice to look at

The world keeps the prose grounded in physical state:
- hair has a measurable length and style
- a surprise can raise or ease feelings
- objects like clips, ribbons, and a comb matter
- the ending proves what changed

This world is intentionally small and constraint-driven.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    time_of_day: str
    quiet: bool = True


@dataclass
class HairStyle:
    id: str
    label: str
    feel: str
    length: float
    surprise_fit: str
    kind: str = "hair_style"


@dataclass
class SurpriseItem:
    id: str
    label: str
    role: str
    effect: str
    kind: str = "surprise_item"


@dataclass
class StoryParams:
    style: str
    surprise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_sense_surprise(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    surprise = world.entities.get("surprise")
    if not child or not surprise:
        return out
    if child.memes.get("worry", 0) >= THRESHOLD and surprise.memes.get("revealed", 0) >= THRESHOLD:
        sig = ("sense_surprise",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["surprise"] = child.memes.get("surprise", 0) + 1
        out.append("The surprise made the room feel bright again.")
    return out


def _r_hair_settles(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    clip = world.entities.get("clip")
    if not child:
        return out
    if child.meters.get("hair_length", 0) <= 5.0:
        sig = ("hair_settles",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["ease"] = child.memes.get("ease", 0) + 1
        if clip:
            clip.meters["shine"] = clip.meters.get("shine", 0) + 1
        out.append("Her hair stopped falling into her eyes.")
    return out


CAUSAL_RULES = [
    Rule("sense_surprise", _r_sense_surprise),
    Rule("hair_settles", _r_hair_settles),
]


def propagate(world: World) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
                for line in lines:
                    world.say(line)
    return produced


SETTING = Setting(place="the apartment kitchen", time_of_day="morning", quiet=True)

HAIR_STYLES = {
    "bangs": HairStyle(
        id="bangs",
        label="soft bangs",
        feel="fuzzy",
        length=7.0,
        surprise_fit="bangs",
    ),
    "pony": HairStyle(
        id="pony",
        label="a neat ponytail",
        feel="swishy",
        length=10.0,
        surprise_fit="pony",
    ),
    "bob": HairStyle(
        id="bob",
        label="a tidy bob",
        feel="light",
        length=5.0,
        surprise_fit="bob",
    ),
}

SURPRISE_ITEMS = {
    "clip": SurpriseItem(
        id="clip",
        label="a star clip",
        role="hair clip",
        effect="holds the front pieces back",
    ),
    "ribbon": SurpriseItem(
        id="ribbon",
        label="a red ribbon",
        role="ribbon",
        effect="ties the hair neatly",
    ),
    "spritz": SurpriseItem(
        id="spritz",
        label="a little water spritz",
        role="spritz bottle",
        effect="tames flyaways",
    ),
}

NAMES_GIRL = ["Mina", "Leah", "Nora", "Ivy", "Lila", "Sana"]
NAMES_BOY = ["Milo", "Ezra", "Noah", "Owen", "Theo", "Finn"]
TRAITS = ["curious", "gentle", "shy", "playful", "careful", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for style in HAIR_STYLES:
        for surprise in SURPRISE_ITEMS:
            combos.append((style, surprise))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, style in HAIR_STYLES.items():
        lines.append(asp.fact("style", sid))
        lines.append(asp.fact("hair_length", sid, int(style.length)))
    for iid, item in SURPRISE_ITEMS.items():
        lines.append(asp.fact("surprise_item", iid))
        lines.append(asp.fact("helpful", iid))
    return "\n".join(lines)


ASP_RULES = r"""
possible(S, I) :- style(S), surprise_item(I), helpful(I).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show possible/2."))
    return sorted(set(asp.atoms(model, "possible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def introduce(world: World, child: Entity, parent: Entity, style: HairStyle) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} {child.type} with {style.label} that felt {style.feel} to touch."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} liked the way {child.pronoun('possessive')} hair moved when {child.pronoun('subject')} walked."
    )
    world.say(
        f"Each morning, {child.id} and {parent.label} got ready in {world.setting.place} while the day was still quiet."
    )


def worry(world: World, child: Entity, parent: Entity, style: HairStyle) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} had been brushing {child.pronoun('possessive')} hair aside all week, because the front pieces kept slipping into {child.pronoun('possessive')} eyes."
    )
    world.say(
        f"{parent.label} noticed that too and remembered a small surprise could make the morning easier."
    )


def reveal(world: World, parent: Entity, child: Entity, surprise_item: SurpriseItem) -> None:
    surprise = world.add(Entity(
        id="surprise",
        kind="thing",
        type="surprise",
        label=surprise_item.label,
        phrase=surprise_item.effect,
        owner=parent.id,
        meters={"revealed": 1.0},
        memes={"kindness": 1.0},
    ))
    clip = world.add(Entity(
        id="clip",
        kind="thing",
        type="clip",
        label=surprise_item.label if surprise_item.id == "clip" else "hair clip",
        phrase=surprise_item.effect,
        owner=child.id,
        meters={},
        memes={},
    ))
    world.say(
        f"After breakfast, {parent.label} smiled and held out {surprise_item.label} as a surprise."
    )
    world.say(
        f'"I got this for you," {parent.label} said. "It will {surprise_item.effect}."'
    )
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    surprise.memes["revealed"] = 1.0
    clip.meters["shine"] = 1.0
    propagate(world)


def trim_or_tie(world: World, child: Entity, style: HairStyle, surprise_item: SurpriseItem) -> None:
    if style.id == "bob":
        child.meters["hair_length"] = 5.0
        world.say(
            f"{parent_name(world)} gently shaped the ends so {child.id}'s {style.label} sat evenly around {child.pronoun('possessive')} face."
        )
    elif surprise_item.id == "clip":
        world.say(
            f"{parent_name(world)} gathered the loose front pieces and clipped them back, so the hair stopped tickling {child.pronoun('possessive')} eyes."
        )
        child.meters["hair_length"] = 6.0
    elif surprise_item.id == "ribbon":
        world.say(
            f"{parent_name(world)} tied back {child.pronoun('possessive')} hair with the ribbon, and the whole style looked neat at once."
        )
        child.meters["hair_length"] = 6.0
    else:
        world.say(
            f"{parent_name(world)} misted the hair lightly and smoothed it down, which made the little mess settle."
        )
        child.meters["hair_length"] = 6.0
    propagate(world)


def parent_name(world: World) -> str:
    return world.facts["parent"].label


def resolution(world: World, child: Entity, parent: Entity, style: HairStyle, surprise_item: SurpriseItem) -> None:
    child.memes["worry"] = 0.0
    child.memes["ease"] = child.memes.get("ease", 0) + 1
    world.say(
        f"{child.id} blinked in the kitchen light, then smiled when the surprise turned useful."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} looked in the spoon like it was a tiny mirror and liked what {child.pronoun('subject')} saw."
    )
    world.say(
        f"By the time they left the apartment, {child.id}'s hair stayed out of {child.pronoun('possessive')} eyes, and the morning felt easier to carry."
    )


def tell(style: HairStyle, surprise_item: SurpriseItem, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        traits=[trait, "little"],
        meters={"hair_length": style.length},
        memes={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="Mom" if parent_type == "mother" else "Dad",
        traits=["kind"],
    ))
    world.facts["parent"] = parent
    world.facts["child"] = child
    world.facts["style"] = style
    world.facts["surprise_item"] = surprise_item

    introduce(world, child, parent, style)
    world.para()
    worry(world, child, parent, style)
    world.para()
    reveal(world, parent, child, surprise_item)
    trim_or_tie(world, child, style, surprise_item)
    world.para()
    resolution(world, child, parent, style, surprise_item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    style = f["style"]
    surprise_item = f["surprise_item"]
    return [
        f"Write a gentle slice-of-life story about {child.id}'s {style.label} and a small surprise with {surprise_item.label}.",
        f"Tell a short story for a child about a morning surprise that helps {child.id} keep {child.pronoun('possessive')} hair neat.",
        f"Write a warm everyday story where a parent turns a hair problem into a pleasant surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    style = f["style"]
    surprise_item = f["surprise_item"]
    return [
        QAItem(
            question=f"What kind of hair did {child.id} have?",
            answer=f"{child.id} had {style.label} that felt {style.feel} and kept slipping into {child.pronoun('possessive')} eyes before the surprise plan helped.",
        ),
        QAItem(
            question=f"Who brought the surprise in the kitchen?",
            answer=f"{parent.label} brought the surprise and used it to make {child.id}'s hair easier to manage.",
        ),
        QAItem(
            question=f"What did the surprise item do for {child.id}?",
            answer=f"The {surprise_item.label} {surprise_item.effect}, which made {child.id}'s hair look neat and feel better during the morning.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt pleased and calmer, because the surprise solved the little hair problem without making the morning feel heavy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hair clip for?",
            answer="A hair clip helps hold hair in place so it does not fall into your face.",
        ),
        QAItem(
            question="Why do people brush hair?",
            answer="People brush hair to smooth it, untangle it, and make it easier to comb or style.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(style="bangs", surprise="clip", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(style="pony", surprise="ribbon", name="Theo", gender="boy", parent="father", trait="playful"),
    StoryParams(style="bob", surprise="spritz", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not describe a believable small everyday surprise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a slice-of-life hair surprise."
    )
    ap.add_argument("--style", choices=HAIR_STYLES)
    ap.add_argument("--surprise", choices=SURPRISE_ITEMS)
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
    combos = valid_combos()
    if args.style or args.surprise:
        combos = [c for c in combos if (args.style is None or c[0] == args.style)
                  and (args.surprise is None or c[1] == args.surprise)]
    if not combos:
        raise StoryError(explain_rejection())
    style, surprise = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(style=style, surprise=surprise, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        HAIR_STYLES[params.style],
        SURPRISE_ITEMS[params.surprise],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show possible/2."))
    return sorted(set(asp.atoms(model, "possible")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show possible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for style, surprise in combos:
            print(f"  {style:8} {surprise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
