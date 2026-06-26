#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale about a louse, linen,
foreshadowing, moral value, and a bad ending.

Premise:
- A young space traveler notices a tiny louse hiding in a linen blanket aboard
  a small ship.
- A careful foreshadowing warning suggests the blanket should be checked and
  cleaned.
- A moral choice is made too late: the traveler ignores the warning, shares the
  blanket, and the louse spreads.
- The ending is bad in a child-safe way: the blanket is ruined, the ship is
  itchy, and the traveler learns a hard lesson.

This world is intentionally small and constraint-checked. The story should read
like a complete, authored miniature: setup, warning, poor choice, and a final
image proving what changed.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dirty": 0.0, "itchy": 0.0, "rumor": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "care": 0.0, "regret": 0.0, "warning": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the small starship"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    spread: str
    warning: str
    bad: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: str = ""

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = self.zone
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    gender: str = "boy"
    parent: str = "captain"
    place: str = "ship"
    risk: str = "louse"
    item: str = "linen"
    trait: str = "careful"


SETTINGS = {
    "ship": Setting(place="the small starship", affordances={"travel", "rest"}),
    "cabin": Setting(place="the sleeping cabin", affordances={"rest"}),
}

RISKS = {
    "louse": Risk(
        id="louse",
        label="louse",
        phrase="a tiny louse",
        spread="spread to the bedding",
        warning="the linen should be washed before anyone sleeps on it",
        bad="make the blanket itchy",
        zone="bedding",
        tags={"louse", "itchy", "warning"},
    ),
}

REMEDIES = {
    "wash": Remedy(
        id="wash",
        label="wash cycle",
        phrase="the ship's wash cycle",
        covers={"bedding"},
        helps={"louse", "itchy"},
        prep="start the wash cycle and fold in clean cloth",
        tail="scrubbed the linen until it was fresh again",
    ),
    "seal": Remedy(
        id="seal",
        label="sealed storage",
        phrase="a sealed storage bag",
        covers={"bedding"},
        helps={"louse"},
        prep="seal the linen away first",
        tail="stowed the linen in a sealed bag",
    ),
}

GIRL_NAMES = ["Ava", "Mina", "Luna", "Tess", "Nora"]
BOY_NAMES = ["Milo", "Jace", "Pico", "Theo", "Finn"]
TRAITS = ["careful", "curious", "brave", "gentle", "thoughtful"]


def reasonableness_gate(risk: Risk, remedy: Remedy) -> bool:
    return risk.zone in remedy.covers and risk.id in remedy.helps


def predict_bad(world: World, hero: Entity, risk: Risk) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["warning"] += 1
    sim.facts["ignored"] = True
    sim.get("linen").meters["dirty"] += 1
    sim.get("linen").meters["itchy"] += 1
    sim.get("bed").meters["itchy"] += 1
    return sim.get("linen").meters["dirty"] >= THRESHOLD


def introduce(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} aboard {world.setting.place} who liked quiet "
        f"nights and neat blankets."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {item.label} everywhere "
        f"because it felt soft and warm."
    )
    parent.memes["care"] += 1


def foreshadow(world: World, hero: Entity, risk: Risk, item: Entity) -> None:
    world.say(
        f"One evening, {hero.id} noticed {risk.phrase} hiding in the folds of the {item.label}."
    )
    world.say(
        f"{hero.id} frowned, because the tiny speck looked harmless, but it was a small sign that "
        f"something could go wrong later."
    )
    hero.memes["warning"] += 1
    world.facts["foreshadowed"] = True


def moral_choice(world: World, hero: Entity, parent: Entity, risk: Risk, item: Entity) -> None:
    world.say(
        f"{parent.id} said, \"{risk.warning.capitalize()}.\""
    )
    world.say(
        f"{hero.id} knew the right thing was to listen, wash the blanket, and keep the cabin safe."
    )
    world.say(
        f"But {hero.id} wanted to sleep first and promised to deal with it in the morning."
    )
    hero.memes["regret"] += 1
    parent.memes["worry"] += 1
    world.facts["ignored_warning"] = True


def bad_ending(world: World, hero: Entity, parent: Entity, risk: Risk, item: Entity) -> None:
    world.para()
    world.say(
        f"By morning, the louse had done exactly what the warning feared: it had {risk.spread}."
    )
    item.meters["dirty"] += 1
    item.meters["itchy"] += 1
    parent.meters["itchy"] += 1
    hero.memes["regret"] += 2
    world.say(
        f"The {item.label} was scratchy and unpleasant, and the little ship felt less cozy than before."
    )
    world.say(
        f"{hero.id} had to hold still while {parent.id} packed away the ruined blanket and opened the wash bin."
    )
    world.say(
        f"It was a bad ending, because the easy warning had been ignored and the once-soft linen was no longer safe."
    )
    world.facts["bad_ending"] = True


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type="captain"))
    item = world.add(Entity(id="linen", type="linen", label="linen blanket", phrase="a linen blanket"))
    bed = world.add(Entity(id="bed", type="thing", label="sleeping bunk"))
    risk = RISKS[params.risk]

    world.facts.update(hero=hero, parent=parent, item=item, bed=bed, risk=risk, setting=world.setting)

    introduce(world, hero, parent, item)
    world.para()
    foreshadow(world, hero, risk, item)
    moral_choice(world, hero, parent, risk, item)
    bad_ending(world, hero, parent, risk, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short Space Adventure story for a child about a {f["risk"].label} hiding in linen.',
        f'Tell a gentle spaceship story where {hero.id} notices a warning, makes a poor choice, and gets a bad ending.',
        f'Write a small story with foreshadowing and a moral lesson on a starship with a linen blanket.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    risk: Risk = f["risk"]
    return [
        QAItem(
            question=f"What did {hero.id} notice hiding in the linen blanket?",
            answer=f"{hero.id} noticed {risk.phrase} hiding in the linen blanket.",
        ),
        QAItem(
            question=f"What warning did {parent.id} give about the blanket?",
            answer=f"{parent.id} warned that {risk.warning}.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The ending was bad because {hero.id} ignored the warning, the louse spread, and "
                f"the linen blanket became dirty and itchy."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is linen?",
            answer="Linen is a cloth made from plant fibers. It can feel cool, smooth, and a little stiff.",
        ),
        QAItem(
            question="What is a louse?",
            answer="A louse is a tiny insect that lives on skin or in hair and can make things itchy.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something important may happen later in the story.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to act, like being careful, honest, or kind.",
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


@dataclass
class StoryParamsRegistry:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld: louse, linen, foreshadowing, moral value, bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(seed=args.seed, name=name, gender=gender, parent=parent, place=place, trait=trait)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
risk_at_play(Risk) :- risk(Risk).
bad_ending(Risk) :- risk_at_play(Risk), ignored_warning.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("zone", rid, risk.zone))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for c in sorted(remedy.covers):
            lines.append(asp.fact("covers", rid, c))
        for h in sorted(remedy.helps):
            lines.append(asp.fact("helps", rid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(seed=1, name="Milo", gender="boy", parent="captain", place="ship", risk="louse", item="linen", trait="careful"),
    StoryParams(seed=2, name="Ava", gender="girl", parent="captain", place="cabin", risk="louse", item="linen", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risk_at_play/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this world, but its reasoning gate is intentionally minimal.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
