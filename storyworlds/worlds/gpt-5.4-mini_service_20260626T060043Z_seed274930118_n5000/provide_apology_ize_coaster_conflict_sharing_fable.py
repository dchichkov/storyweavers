#!/usr/bin/env python3
"""
storyworlds/worlds/provide_apology_ize_coaster_conflict_sharing_fable.py
=======================================================================

A small fable-style storyworld about kindness, apology, and sharing.

Seed tale:
---
A squirrel had one round wooden coaster for a warm berry cup. A mouse wanted to
share the cup, but the squirrel kept the coaster close and snapped that it was
his. The cup could leave rings on the table, so the old owl said to provide a
second coaster from bark and to apology-ize. The squirrel did, the mouse shared
the drink, and the table stayed smooth.

World shape:
- A little woodland setting with a stump-table and a shared drink.
- Conflict comes from hoarding the coaster instead of sharing it.
- Resolution comes from providing another coaster and apology-izing.
- The ending proves the change with a calm shared cup and a clean table.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"squirrel", "fox", "owl", "rabbit", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the oak glade"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone


SETTING = Setting(place="the oak glade", affords={"share_tea"})

ACTIVITY = Activity(
    id="share_tea",
    verb="share the berry tea",
    gerund="sharing berry tea",
    rush="snatch the coaster back",
    mess="wet",
    soil="ringed and damp",
    zone={"table"},
    keyword="coaster",
    tags={"sharing", "coaster"},
)

PRIZE = Prize(
    label="table",
    phrase="a smooth stump table",
    type="table",
    region="table",
)

GEAR = Gear(
    id="extra_coaster",
    label="a second coaster",
    covers={"table"},
    guards={"wet"},
    prep="provide a second coaster",
    tail="set the second coaster beside the first",
)

GIRL_NAMES = ["Mira", "Tessa", "Luna"]
BOY_NAMES = ["Pip", "Robin", "Finn"]
TRAITS = ["kind", "proud", "gentle", "stubborn", "helpful"]


@dataclass
class StoryParams:
    name: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about sharing, conflict, and apology-ize.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--friend", choices=["mouse", "rabbit"])
    ap.add_argument("--elder", choices=["owl", "fox"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice(["mouse", "rabbit"])
    elder = args.elder or rng.choice(["owl", "fox"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, friend=friend, elder=elder, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend:
        raise StoryError("The hero and friend must be different characters.")
    if params.trait not in TRAITS:
        raise StoryError("Unknown trait.")


def predict_ring(world: World, actor: Entity) -> bool:
    sim = world.copy()
    _share(sim, sim.get(actor.id), narrate=False)
    table = sim.get("table")
    return table.meters.get("dirty", 0.0) >= THRESHOLD


def _share(world: World, actor: Entity, narrate: bool = True) -> None:
    if ACTIVITY.id not in world.setting.affords:
        return
    world.zone = set(ACTIVITY.zone)
    actor.meters[ACTIVITY.mess] = actor.meters.get(ACTIVITY.mess, 0.0) + 1
    if narrate:
        pass
    table = world.get("table")
    table.meters["dirty"] = table.meters.get("dirty", 0.0) + 1


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type="squirrel", label=params.name, traits=[params.trait, "small"]))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend, label=params.friend))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=params.elder))
    table = world.add(Entity(id="table", type="table", label="table", phrase=PRIZE.phrase))
    coaster = world.add(Entity(id="coaster", type="coaster", label="coaster", phrase="a round wooden coaster", owner=hero.id, caretaker=elder.id))
    tea = world.add(Entity(id="tea", type="drink", label="berry tea", phrase="a warm cup of berry tea", owner=hero.id))

    hero.memes["pride"] = 1.0
    hero.memes["sharing"] = 0.0
    friend.memes["desire"] = 1.0

    world.say(f"In {world.setting.place}, {hero.label} the squirrel kept {coaster.label} beside {tea.label}.")
    world.say(f"{friend.label.capitalize()} the {friend.type} came to share the tea, because one cup tastes sweeter with company.")
    world.para()
    world.say(f"{hero.label.capitalize()} wanted to keep the {coaster.label} close, so {friend.label} had no place to set a cup.")
    world.say(f"{friend.label.capitalize()} frowned. The stump table could get a wet ring, and that was no fair way to treat a guest.")
    world.say(f"The old {elder.label} listened and said, \"Please provide a second coaster, and apology-ize before the tea cools.\"")
    world.para()

    if predict_ring(world, hero):
        hero.memes["conflict"] = 1.0
        friend.memes["hurt"] = 1.0
        world.say(f"{hero.label.capitalize()} heard the warning and felt the sting of being selfish.")
        world.say(f"{hero.label.capitalize()} reached for the bark and made a second coaster at once.")
        world.say(f"Then {hero.label.lower()} apology-ized, saying, \"I was wrong. We can share.\"")
        hero.memes["sharing"] = 1.0
        hero.memes["conflict"] = 0.0
        friend.memes["trust"] = 1.0
        coaster.meters["provided"] = 1.0
        table.meters["dirty"] = 0.0
        world.say(f"{elder.label.capitalize()} smiled as {hero.label.lower()} placed one coaster under each cup.")
        world.say(f"At last, {hero.label} and {friend.label} shared the berry tea, and the stump table stayed smooth.")
    else:
        world.say(f"But the tea was gentle, and the story found no honest problem to solve.")

    world.facts.update(hero=hero, friend=friend, elder=elder, coaster=coaster, table=table, tea=tea)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short fable about {hero.label} the squirrel, a shared cup, and the word "coaster".',
        f"Tell a child-friendly story where {hero.label} learns to provide instead of hoard and then apology-ize.",
        f"Write a gentle woodland tale about conflict turning into sharing around a small table.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, elder = f["hero"], f["friend"], f["elder"]
    return [
        QAItem(
            question=f"Who first kept the coaster too close?",
            answer=f"{hero.label} the squirrel kept the coaster close at first, which made sharing hard.",
        ),
        QAItem(
            question=f"What did the old {elder.label} tell them to do?",
            answer=f"The old {elder.label} told {hero.label} to provide a second coaster and apology-ize.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {friend.label}?",
            answer=f"They shared the berry tea together, and the stump table stayed smooth and clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coaster for?",
            answer="A coaster is a small pad or disk you set under a cup to help protect a table from wet rings.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use, have, or enjoy something with you.",
        ),
        QAItem(
            question="What does apology-ize mean in this story?",
            answer="Apology-ize means to say sorry in a playful, storybook way.",
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
holds(have_coaster) :- coaster.
conflict(hero, friend) :- wants_share(friend), hoards(hero).
resolved :- provide_second_coaster, apology_ize(hero), share(hero, friend).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("coaster"),
        asp.fact("want_share", "friend"),
        asp.fact("hero"),
        asp.fact("friend"),
        asp.fact("provide_action"),
        asp.fact("apology_action"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


CURATED = [
    StoryParams(name="Mira", friend="mouse", elder="owl", trait="kind"),
    StoryParams(name="Pip", friend="rabbit", elder="fox", trait="stubborn"),
    StoryParams(name="Luna", friend="mouse", elder="owl", trait="helpful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: conflict, apology-ize, share.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.friend} / {p.elder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
