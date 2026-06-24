#!/usr/bin/env python3
"""
A standalone superhero story world about a small city, a mysterious gourd,
a transformation, a suspenseful choice, and a happy ending.

This world keeps the prose child-facing while the simulated state drives the
narration. The seed words are incorporated as a theme prompt and as world
knowledge topics where reasonable. The story stays away from any explicit
sexual content; if a user explicitly requests an unsafe interpretation of a
seed word, the world simply does not model that premise.

Story shape:
- A young hero notices an unusual gourd.
- A strange glow causes a transformation.
- Suspense rises while the hero must choose how to help.
- The hero uses the new form to save the day.
- The ending proves what changed.

The script follows the Storyweavers contract:
- StoryParams plus standard CLI support
- generate/emit/main
- QA generation
- lazy ASP helper import
- inline ASP_RULES twin and verify mode
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    name: str
    transform: str
    telltale: str
    strength_gain: int
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    owner_kind: str
    risk_if_unhandled: str
    from_power: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "city": Setting(place="the city", indoors=False, affords={"street", "rooftop", "park"}),
    "lab": Setting(place="the bright lab", indoors=True, affords={"lab"}),
    "market": Setting(place="the market", indoors=False, affords={"street", "market"}),
}

POWERS = {
    "gourd": Power(
        id="gourd",
        name="gourd glow",
        transform="turns brave and bright",
        telltale="the gourd hummed with green light",
        strength_gain=2,
        risk="the gourd might crack if dropped",
        keyword="gourd",
        tags={"gourd", "glow", "transformation", "suspense"},
    ),
    "explanatory": Power(
        id="explanatory",
        name="clear explanation",
        transform="speaks in careful steps",
        telltale="the hero understood the plan",
        strength_gain=1,
        risk="confusion could slow the rescue",
        keyword="explanatory",
        tags={"explanatory"},
    ),
}

ARTIFACTS = {
    "gourd": Artifact(
        id="gourd",
        label="gourd",
        phrase="a small green gourd with a silver vine",
        owner_kind="hero",
        risk_if_unhandled="it could be smashed in the crowd",
        from_power="gourd",
    ),
    "mask": Artifact(
        id="mask",
        label="mask",
        phrase="a shiny hero mask",
        owner_kind="hero",
        risk_if_unhandled="it might hide the hero's face",
    ),
}

HERO_NAMES = ["Mina", "Leo", "Nia", "Toby", "Ari", "Zoe"]
VILLAIN_NAMES = ["Cinder", "Murk", "Rattle", "Shade", "Grin"]
TRAITS = ["curious", "kind", "brave", "quick", "gentle"]


@dataclass
class StoryParams:
    place: str
    power: str
    hero_name: str
    hero_gender: str
    villain_name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="city", power="gourd", hero_name="Mina", hero_gender="girl", villain_name="Shade", trait="curious"),
    StoryParams(place="market", power="gourd", hero_name="Leo", hero_gender="boy", villain_name="Murk", trait="brave"),
    StoryParams(place="lab", power="explanatory", hero_name="Nia", hero_gender="girl", villain_name="Cinder", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world with transformation, suspense, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--villain-name")
    ap.add_argument("--trait", choices=TRAITS)
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


def _valid_combo(place: str, power: str) -> bool:
    return place in SETTINGS and power in POWERS and power in SETTINGS[place].affords | {"gourd", "explanatory"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    power = args.power or rng.choice(list(POWERS))
    if not _valid_combo(place, power):
        raise StoryError("No valid combination matches the given options.")
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    villain_name = args.villain_name or rng.choice(VILLAIN_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, power=power, hero_name=hero_name, hero_gender=gender, villain_name=villain_name, trait=trait)


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id="hero", kind="character", type=_hero_type(params.hero_gender), label=params.hero_name, traits=["young", params.trait]))
    villain = world.add(Entity(id="villain", kind="character", type="woman", label=params.villain_name))
    power = POWERS[params.power]
    gourd = world.add(Entity(id="gourd", type="artifact", label="gourd", phrase=ARTIFACTS["gourd"].phrase, owner=hero.id))
    mask = world.add(Entity(id="mask", type="artifact", label="mask", phrase=ARTIFACTS["mask"].phrase, owner=hero.id))

    world.say(f"{hero.label} was a {params.trait} young hero who lived in {world.setting.place}.")
    world.say(f"{hero.label} carried {gourd.phrase}, and {power.telltale}.")
    world.say(f"That made {hero.label} wonder if something magical was about to happen.")

    world.para()
    world.say(f"One evening, {villain.label} made trouble at {world.setting.place} and grabbed the glowing gourd.")
    world.say(f"{hero.label} rushed after {villain.label}, and the air felt full of suspense.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["suspense"] = 1
    villain.meters["danger"] = 1

    world.para()
    hero.memes["transformation"] = 1
    hero.meters["strength"] = power.strength_gain
    hero.meters["bravery"] = 1
    world.say(f"Then the gourd flashed, and {hero.label} changed in a surprising way.")
    world.say(f"{hero.label} {power.transform}, and {hero.pronoun().capitalize()} felt stronger than before.")
    if params.power == "gourd":
        world.say(f"{hero.label} lifted the gourd carefully because {power.risk}.")
    else:
        world.say(f"{hero.label} explained the plan out loud so everyone could stay calm.")

    world.para()
    world.say(f"{villain.label} tried to run away, but {hero.label} used the new power to stop the trouble.")
    world.say(f"{hero.label} protected the {gourd.label}, wore the {mask.label}, and helped the crowd step back safely.")
    world.say(f"At last, {villain.label} dropped the gourd and ran off without harming anyone.")

    world.para()
    hero.memes["joy"] = 1
    hero.memes["suspense"] = 0
    world.say(f"In the happy ending, {hero.label} placed the gourd on a safe shelf and smiled at the quiet street.")
    world.say(f"{hero.label} was still the same kind kid, but now everyone knew {hero.pronoun('subject')} could be a true hero.")
    world.facts.update(hero=hero, villain=villain, power=power, gourd=gourd, mask=mask, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    return [
        f"Write a short superhero story about {hero.label}, the seed word '{p.power}', and a mysterious gourd.",
        f"Tell a suspenseful but child-friendly story where {hero.label} transforms and saves the day in {world.setting.place}.",
        f"Write a happy-ending superhero tale that uses the words explanatory and gourd.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    villain = world.facts["villain"]
    power = world.facts["power"]
    params = world.facts["params"]
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {hero.label}, a {params.trait} young hero who lived in {world.setting.place}.",
        ),
        QAItem(
            question=f"What caused the big transformation in the story?",
            answer=f"The glowing gourd caused the transformation when it flashed and changed {hero.label} in a surprising way.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because {villain.label} grabbed the gourd and tried to run away before {hero.label} could stop the trouble.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily because {hero.label} saved the gourd, stopped the trouble, and left the street calm again.",
        ),
        QAItem(
            question=f"What kind of power did {hero.label} use?",
            answer=f"{hero.label} used the {power.name}, which helped with the rescue and led to a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gourd?",
            answer="A gourd is a hard fruit with a thick skin. People can carry it, decorate it, or use it like a small pumpkin-shaped thing.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a big change in how someone or something looks or acts.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important might happen soon, so you want to know what will happen next.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish the story feeling safe or glad.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_changed(H) :- has_gourd(H), flash(G), owns(H,G).
suspense(H) :- villain_grabs(V,G), owns(H,G), villain(V).
happy_ending(H) :- hero_changed(H), stops_trouble(H), gourd_safe(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for pid in POWERS:
        lines.append(asp.fact("power", pid))
    lines.append(asp.fact("theme", "explanatory"))
    lines.append(asp.fact("theme", "rapist"))
    lines.append(asp.fact("theme", "gourd"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    _ = asp.one_model(asp_program("#show hero_changed/1."))
    print("OK: ASP rules loaded.")
    return 0


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(World(SETTINGS[params.place]), params)
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
        print(asp_program("#show hero_changed/1.\n#show suspense/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world is primarily designed for prose generation.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
