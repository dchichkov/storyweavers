#!/usr/bin/env python3
"""
storyworlds/worlds/curdle_kindness_nursery_rhyme.py
====================================================

A tiny nursery-rhyme storyworld about a cozy kitchen, a spilled cup, and
kindness that smooths the day back out.

Seed-tale sketch:
---
On a little hill, in a little house, a child named Pippa helped their Nan make
warm milk for a sleepy kitten. But the milk got too cold and curdled in the bowl.
Pippa frowned and almost cried. Nan sang a soft rhyme about stirring gently,
warming kindly, and sharing the last spoon of honey. Together they cleaned the
bowl, fed the kitten a safer treat, and the room felt bright again.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
CURDLE_KEYS = {"curdled", "spilled", "cold"}
RHYME_ENDINGS = {
    "hill": "on a little hill",
    "house": "in a little house",
    "kitchen": "in the kitchen bright",
    "garden": "in the garden light",
}

NAMES = ["Pippa", "Milo", "Tilly", "Nora", "Bram", "Luna", "Elsie", "Otis"]
NAN_NAMES = ["Nan", "Gran", "Nana", "Granny"]
PETS = ["kitten", "duckling", "puppy", "bunny"]
ACTIVITIES = ["warm milk", "stir the bowl", "carry the spoon", "sing a soft rhyme"]
PLACES = ["kitchen", "little house", "cottage", "garden"]
HUMORS = ["careful", "cheerful", "gentle", "patient", "kind"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    feels: str = "cozy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Potion:
    label: str
    phrase: str
    region: str = "hands"
    fragile: bool = True


@dataclass
class Comfort:
    id: str
    label: str
    action: str
    guard: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.weather = self.weather
        return c

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_curdle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("milk", 0) < THRESHOLD:
            continue
        if ent.meters.get("cold", 0) < THRESHOLD:
            continue
        sig = ("curdle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["curdled"] = ent.meters.get("curdled", 0) + 1
        out.append(f"The milk in the bowl curdled.")
    return out


def _r_sadness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.children():
        if ent.meters.get("curdled", 0) < THRESHOLD:
            continue
        sig = ("sad", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["sad"] = ent.memes.get("sad", 0) + 1
        out.append(f"{ent.id} felt a tear come quick.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.children():
        if ent.memes.get("kindness", 0) < THRESHOLD:
            continue
        if ent.meters.get("curdled", 0) < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["curdled"] = 0
        ent.memes["sad"] = 0
        ent.memes["glow"] = ent.memes.get("glow", 0) + 1
        out.append(f"Kind words made the room feel warm.")
    return out


CAUSAL_RULES = [
    Rule("curdle", _r_curdle),
    Rule("sadness", _r_sadness),
    Rule("kindness", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def detect_curdle(world: World, bowl: Entity) -> bool:
    return bowl.meters.get("curdled", 0) >= THRESHOLD


def can_fix(world: World, comfort: Comfort) -> bool:
    return comfort.guard == "curdled"


def _warm_and_calm(world: World, child: Entity, bowl: Entity, comfort: Comfort) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    world.say(f"{child.id} tried to {comfort.action}, softly and slow.")
    world.say(f"Then {comfort.prep}, and {comfort.tail}.")
    propagate(world, narrate=True)


def tell(setting: Setting, hero_name: str, nan_name: str, pet: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if hero_name in {"Pippa", "Tilly", "Nora", "Luna", "Elsie"} else "boy",
        traits=["small", "kind", "careful"],
    ))
    nan = world.add(Entity(
        id=nan_name,
        kind="character",
        type="grandmother",
        label=nan_name,
        traits=["gentle", "singing"],
    ))
    kitten = world.add(Entity(
        id=pet,
        kind="character",
        type=pet,
        traits=["sleepy", "tiny"],
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label="a little bowl",
        phrase="a little bowl of warm milk",
        caretaker=nan.id,
    ))
    spoon = world.add(Entity(
        id="spoon",
        type="spoon",
        label="spoon",
        phrase="a small silver spoon",
        caretaker=nan.id,
    ))

    world.say(f"{hero_name} lived {RHYME_ENDINGS.get(setting.place, 'in a cozy place')}.")
    world.say(f"{hero_name} helped {nan_name} with a song, and liked to be polite.")
    world.say(f"One night {hero_name} made {pet} a treat, as nice as nice could be.")
    world.para()

    bowl.meters["milk"] = 1
    world.say(f"{hero_name} carried the bowl with {spoon.label} held tight.")
    world.say(f"But the room grew chilly, and the milk lost its light.")
    bowl.meters["cold"] = 1
    propagate(world, narrate=True)

    world.para()
    if detect_curdle(world, bowl):
        child.memes["sad"] = child.memes.get("sad", 0) + 1
        world.say(f"{hero_name} saw the milk had curdled, and {hero_name} made a small sad face.")
        world.say(f"{nan_name} said, 'A kind heart stays bright; let's mend this little place.'")
        comfort = Comfort(
            id="honey_rhyme",
            label="a spoon of honey",
            action="stir the bowl with kind hands",
            guard="curdled",
            prep="Nan warmed the bowl and added a spoon of honey",
            tail="the milk grew smooth again, with a soft sweet glow",
        )
        if can_fix(world, comfort):
            _warm_and_calm(world, child, bowl, comfort)
            world.say(f"{pet} got a safer snack, and licked its paws in delight.")
            world.say(f"{hero_name} laughed, because the night turned cozy and right.")
    else:
        world.say(f"The milk stayed smooth, and the little room glowed.")

    world.facts.update(
        child=child,
        nan=nan,
        pet=kitten,
        bowl=bowl,
        spoon=spoon,
        comfort="honey_rhyme",
        setting=setting,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", feels="cozy", affords={"milk", "stir"}),
    "house": Setting(place="the little house", feels="warm", affords={"milk", "stir"}),
    "cottage": Setting(place="the cottage", feels="bright", affords={"milk", "stir"}),
    "garden": Setting(place="the garden", feels="soft", affords={"stir"}),
}

COMFORTS = {
    "honey": Comfort(
        id="honey",
        label="a spoon of honey",
        action="stir the bowl with kind hands",
        guard="curdled",
        prep="Nan warmed the bowl and added a spoon of honey",
        tail="the milk grew smooth again, with a soft sweet glow",
    )
}


@dataclass
class StoryParams:
    place: str
    child: str
    nan: str
    pet: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about curdled milk and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--nan", choices=NAN_NAMES)
    ap.add_argument("--pet", choices=PETS)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    nan = args.nan or rng.choice(NAN_NAMES)
    pet = args.pet or rng.choice(PETS)
    return StoryParams(place=place, child=name, nan=nan, pet=pet)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short nursery rhyme about a child, a sleepy pet, and curdled milk.",
        f"Tell a gentle rhyme where {f['child'].id} helps {f['nan'].label} in the {world.setting.place}.",
        "Make the ending bright with kindness, honey, and a bowl that turns smooth again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, nan, pet, bowl = f["child"], f["nan"], f["pet"], f["bowl"]
    return [
        QAItem(
            question=f"What went wrong with the milk in the story?",
            answer=f"The milk got cold and curdled in the little bowl, which made {child.id} feel sad.",
        ),
        QAItem(
            question=f"Who helped make things better for {pet.id}?",
            answer=f"{nan.label} helped {child.id} make the room warm again, and they used kind words and honey.",
        ),
        QAItem(
            question=f"What did {child.id} do with {nan.label} at the end?",
            answer=f"{child.id} helped stir gently, and the bowl turned smooth while {pet.id} got a safer treat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curdled milk look like?",
            answer="Curdled milk has small lumps and does not look smooth anymore.",
        ),
        QAItem(
            question="What does kindness do in a story?",
            answer="Kindness helps people feel safe, calm, and ready to try again.",
        ),
        QAItem(
            question="Why do people warm milk for a sleepy pet?",
            answer="Warm milk can be comforting, but it should be safe and given the right way.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
curdled(B) :- bowl(B), has_milk(B), has_cold(B).
sad(C) :- child(C), sees_curdled(B), curdled(B).
fixed(C) :- child(C), kindness(C), curdled(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for n in NAMES:
        lines.append(asp.fact("child_name", n))
    for n in NAN_NAMES:
        lines.append(asp.fact("nan_name", n))
    for p in PETS:
        lines.append(asp.fact("pet", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.child, params.nan, params.pet)
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
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show curdled/1.\n#show fixed/1."))
    shown = {str(a) for a in model}
    if shown:
        print("OK: ASP program loaded.")
        return 0
    print("ASP program returned no model.")
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for name in NAMES:
            for nan in NAN_NAMES:
                for pet in PETS:
                    combos.append((place, name, pet))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show curdled/1.\n#show fixed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="kitchen", child="Pippa", nan="Nan", pet="kitten"),
            StoryParams(place="house", child="Milo", nan="Gran", pet="duckling"),
            StoryParams(place="cottage", child="Tilly", nan="Nana", pet="bunny"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
