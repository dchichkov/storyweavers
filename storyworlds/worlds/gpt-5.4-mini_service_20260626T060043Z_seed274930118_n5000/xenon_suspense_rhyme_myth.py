#!/usr/bin/env python3
"""
storyworlds/worlds/xenon_suspense_rhyme_myth.py
===============================================

A small mythic story world about a keeper, a glowing xenon lamp, and a tense
choice that ends in a safer light.

Premise seed:
---
A young temple keeper finds an old lamp that shines with xenon-blue light.
The lamp is beautiful, but it only burns safely in a sealed glass shrine.
When a storm shakes the shrine, the keeper wants to carry the lamp to the
village hall. The elder warns that the bright gas-light is too fragile to bear.
The keeper hesitates, then chooses a clever safer path that keeps the glow and
protects everyone.

Narrative instruments:
- Suspense: a warning, a trembling risk, a near-mistake, and a reveal.
- Rhyme: a repeated, child-friendly cadence in a few key lines.
- Myth: an old, elevated tone with a simple moral ending.

World model:
- Physical meters: glow, tremble, damp, safe, open, sealed.
- Emotional memes: awe, fear, hope, patience, pride, relief.
- State changes drive the story, which is generated from a small causal model.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the shrine"
    mythic: str = "an old stone shrine on a hill"
    affords: set[str] = field(default_factory=set)


@dataclass
class Lamp:
    id: str
    label: str
    phrase: str
    glow: str
    risk: str
    needs: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    phrase: str
    protects: set[str]
    supports: set[str]


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def get_m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def add_m(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = get_m(e, key) + delta


def get_mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_mem(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = get_mem(e, key) + delta


def _rule_damp(world: World) -> list[str]:
    out = []
    keeper = world.get("Keeper")
    if get_m(keeper, "open") >= THRESHOLD and get_m(keeper, "damp") < THRESHOLD:
        add_m(keeper, "damp", 1)
        add_mem(keeper, "fear", 1)
        out.append("The storm-touched air made the keeper’s sleeves damp.")
    return out


def _rule_risk(world: World) -> list[str]:
    out = []
    lamp = world.get("Lamp")
    shrine = world.get("Shrine")
    if get_m(shrine, "sealed") < THRESHOLD and get_m(lamp, "glow") >= THRESHOLD:
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            add_mem(lamp, "danger", 1)
            out.append("The xenon lamp shone bravely, yet its bright breath begged for a sealed glass home.")
    return out


def _rule_relief(world: World) -> list[str]:
    keeper = world.get("Keeper")
    lamp = world.get("Lamp")
    shrine = world.get("Shrine")
    if get_m(shrine, "sealed") >= THRESHOLD and get_m(lamp, "glow") >= THRESHOLD and get_mem(keeper, "hope") >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            add_mem(keeper, "relief", 1)
            add_mem(keeper, "pride", 1)
            return ["The keeper’s heart eased, for the glow could be kept without any harm."]
    return []


RULES = [_rule_damp, _rule_risk, _rule_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mythic_opening(setting: Setting, hero: Entity, lamp: Entity) -> str:
    return (
        f"Long ago, at {setting.mythic}, there lived a young keeper named {hero.id}. "
        f"{hero.pronoun().capitalize()} guarded {lamp.phrase}, a relic with a xenon-blue glow."
    )


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, bright and grand; {b}, held by hand."


def tell(setting: Setting, hero_name: str = "Mira", hero_type: str = "girl") -> World:
    world = World(setting)
    world.add(Entity(id="Keeper", kind="character", type=hero_type, label=hero_name))
    world.add(Entity(id="Elder", kind="character", type="elder", label="the elder"))
    world.add(Entity(id="Lamp", type="lamp", label="xenon lamp", phrase="a xenon lamp", owner="Keeper"))
    world.add(Entity(id="Shrine", type="shrine", label="shrine", phrase="the sealed glass shrine"))
    world.add(Entity(id="Hall", type="hall", label="village hall", phrase="the village hall"))

    keeper = world.get("Keeper")
    lamp = world.get("Lamp")
    shrine = world.get("Shrine")
    elder = world.get("Elder")

    keeper.meters["glow"] = 0
    lamp.meters["glow"] = 1
    shrine.meters["sealed"] = 1

    add_mem(keeper, "awe", 1)
    add_mem(keeper, "hope", 1)

    world.say(mythic_opening(setting, keeper, lamp))
    world.say("Its light was like a little star trapped in clear stone, and the keeper loved it dearly.")
    world.say(rhyme_line("Blue flame, low flame", "safe remains, the old name"))

    world.para()
    world.say("Then a storm came over the hill and tapped hard at the shrine doors.")
    add_m(keeper, "open", 1)
    add_mem(keeper, "fear", 1)
    propagate(world)
    world.say("The keeper looked toward the village hall and wanted to carry the lamp there at once.")

    world.para()
    world.say("But the elder lifted a hand and spoke with a careful voice:")
    world.say('"If the lamp leaves its glass home, the bright breath may spill and falter."')
    add_mem(keeper, "patience", 1)
    add_mem(keeper, "fear", 1)
    world.say("For a moment, the keeper stood still, listening to the rain and the hush between heartbeats.")
    world.say("The suspense hung there like a thread of gold.")

    world.para()
    world.say("At last, the keeper noticed the old lantern cart by the wall.")
    world.say("It had a fitted glass hood and a latch that could keep the flame steady in the wind.")
    add_m(shrine, "sealed", 1)
    add_mem(keeper, "hope", 1)
    world.say("So the keeper placed the xenon lamp inside the cart, shut the hood, and rolled it slowly to the hall.")
    propagate(world)

    world.para()
    add_m(keeper, "safe", 1)
    world.say("There, the blue light rose softly above the people like a moon found in a jar.")
    world.say("The villagers sang, and the keeper smiled, proud not for the speed of the journey, but for its wisdom.")
    world.say("Blue in the glass, calm at last;")
    world.say("What was meant to last, did last.")
    world.facts.update(hero=keeper, elder=elder, lamp=lamp, shrine=shrine, setting=setting)
    return world


SETTING_REGISTRY = {
    "shrine": Setting(place="the shrine", mythic="an old stone shrine on a hill", affords={"guard", "carry", "seal"}),
    "library": Setting(place="the lantern library", mythic="a lantern library built in a canyon", affords={"guard", "carry", "seal"}),
    "harbor": Setting(place="the harbor shrine", mythic="a harbor shrine where bells sang to fog", affords={"guard", "carry", "seal"}),
}

HERO_NAMES = ["Mira", "Lina", "Arin", "Nora", "Sera", "Ivo"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["steadfast", "curious", "gentle", "bold", "patient"]

LAMP_REGISTRY = {
    "xenon": Lamp(
        id="xenon",
        label="xenon lamp",
        phrase="a xenon lamp",
        glow="xenon-blue",
        risk="fragile",
        needs={"sealed"},
    ),
    "star": Lamp(
        id="star",
        label="star lantern",
        phrase="a star lantern",
        glow="white-gold",
        risk="bright",
        needs={"sealed"},
    ),
}

COVER_REGISTRY = {
    "cart": Cover(
        id="cart",
        label="glass cart",
        phrase="a lantern cart with a fitted glass hood",
        protects={"sealed"},
        supports={"carry"},
    ),
    "hood": Cover(
        id="hood",
        label="glass hood",
        phrase="a fitted glass hood",
        protects={"sealed"},
        supports={"seal"},
    ),
}

@dataclass
class StoryParams:
    place: str = "shrine"
    lamp: str = "xenon"
    name: str = "Mira"
    gender: str = "girl"
    trait: str = "steadfast"
    seed: Optional[int] = None


def valid_places() -> list[str]:
    return sorted(SETTING_REGISTRY)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    lamp = world.facts["lamp"]
    setting = world.facts["setting"]
    return [
        f"Write a short myth for a child about {hero.label} and a {lamp.label} at {setting.place}.",
        f"Tell a suspenseful story with a soft rhyme where {hero.label} protects a xenon glow.",
        "Write a gentle myth about choosing the safer path when a bright lamp is too precious to risk.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    lamp = world.facts["lamp"]
    shrine = world.facts["shrine"]
    qa = [
        QAItem(
            question=f"Who guarded the {lamp.label}?",
            answer=f"{hero.label} guarded the {lamp.label} at the shrine.",
        ),
        QAItem(
            question=f"Why was the {lamp.label} risky in the storm?",
            answer=f"It was risky because it needed a sealed place, and the storm made the shrine feel open and unsafe.",
        ),
        QAItem(
            question="What did the keeper use instead of carrying the lamp bare-handed into danger?",
            answer="The keeper used the lantern cart with its glass hood, which let the light travel safely.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the lamp stayed bright, the shrine was sealed again, and the keeper felt proud and relieved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is xenon?",
            answer="Xenon is a gas. People can use it in bright lamps that make a steady glow.",
        ),
        QAItem(
            question="What is a sealed glass hood for?",
            answer="A sealed glass hood helps protect a flame or lamp from wind and keeps it steady and safe.",
        ),
        QAItem(
            question="Why can storms make a light harder to carry?",
            answer="Storms bring wind and rain, and those can shake, wet, or blow out a light that is not protected.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic xenon story world with suspense and rhyme.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--lamp", choices=sorted(LAMP_REGISTRY))
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    place = args.place or rng.choice(valid_places())
    lamp = args.lamp or "xenon"
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, lamp=lamp, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTING_REGISTRY[params.place]
    world = tell(setting, hero_name=params.name, hero_type=params.gender)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
place(shrine). place(library). place(harbor).
lamp(xenon). lamp(star).
needs(xenon,sealed). needs(star,sealed).
hero(girl). hero(boy).

valid(Place,Lamp,Hero) :- place(Place), lamp(Lamp), hero(Hero), needs(Lamp,sealed).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTING_REGISTRY:
        lines.append(asp.fact("place", place))
    for lid, lamp in LAMP_REGISTRY.items():
        lines.append(asp.fact("lamp", lid))
        for need in sorted(lamp.needs):
            lines.append(asp.fact("needs", lid, need))
    for g in HERO_TYPES:
        lines.append(asp.fact("hero", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_valid = sorted(set(asp.atoms(model, "valid")))
    py_valid = sorted((p, l, g) for p in valid_places() for l in LAMP_REGISTRY for g in HERO_TYPES)
    if set(asp_valid) == set(py_valid):
        print(f"OK: clingo gate matches Python registry ({len(py_valid)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("clingo:", asp_valid)
    print("python:", py_valid)
    return 1


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(valid_places()):
            params = StoryParams(place=place, lamp="xenon", name=HERO_NAMES[i % len(HERO_NAMES)],
                                 gender=HERO_TYPES[i % len(HERO_TYPES)], trait=TRAITS[i % len(TRAITS)],
                                 seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
