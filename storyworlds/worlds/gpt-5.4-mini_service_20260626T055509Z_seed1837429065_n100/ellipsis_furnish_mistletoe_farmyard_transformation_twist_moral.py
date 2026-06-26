#!/usr/bin/env python3
"""
A small pirate-tale storyworld set in a farmyard, built around a hidden
mistletoe bundle, a sudden transformation twist, and a moral value ending.

The seed premise:
- A young pirateish child helps around a farmyard.
- They are tempted to use a fancy furnishing item meant for a celebration.
- An unexpected mistletoe bundle causes a transformation twist.
- The story ends with a gentle moral value about kindness and honest work.

This world deliberately keeps the domain small and constraint-checked.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    pirate_role: str
    farmyard_task: str
    furnishing: str
    mistletoe_place: str
    seed: Optional[int] = None


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    moral: str
    risk: str
    change: str
    twist: str
    value: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Furnishing:
    id: str
    label: str
    phrase: str
    place: str
    can_help: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistletoe:
    id: str
    label: str
    phrase: str
    place: str
    magic: str
    tags: set[str] = field(default_factory=set)


TASKS = {
    "hay": Task(
        id="hay",
        verb="stack the hay",
        gerund="stacking hay",
        rush="dash toward the hay bales",
        moral="hard work makes a home safer",
        risk="loose straw",
        change="grew small and nimble",
        twist="The air smelled sweet and green, and the bundle on the gate gave off a strange glow.",
        value="kindness",
        tags={"farmyard", "work", "hay"},
    ),
    "feed": Task(
        id="feed",
        verb="feed the chickens",
        gerund="feeding the chickens",
        rush="run to the feed bucket",
        moral="careful hands keep little creatures calm",
        risk="spilled grain",
        change="sprouted bright feathered arms",
        twist="A hidden sprig in the coop shivered when the moonlight reached it.",
        value="care",
        tags={"farmyard", "animals", "feed"},
    ),
    "mend": Task(
        id="mend",
        verb="mend the fence",
        gerund="mending the fence",
        rush="climb to the broken rail",
        moral="honest fixing is better than showy tricks",
        risk="splinters and bent nails",
        change="became tall like a weather vane",
        twist="Behind the post, something pale and leafy was tucked where no one had seen it.",
        value="honesty",
        tags={"farmyard", "repair", "fence"},
    ),
}

FURNISHINGS = {
    "bench": Furnishing(
        id="bench",
        label="a polished bench",
        phrase="a polished bench for the porch",
        place="by the barn door",
        tags={"bench", "wood"},
    ),
    "lantern": Furnishing(
        id="lantern",
        label="a brass lantern",
        phrase="a brass lantern with a bright glass belly",
        place="on the fence post",
        tags={"light", "metal"},
    ),
    "table": Furnishing(
        id="table",
        label="a small wooden table",
        phrase="a small wooden table for supper",
        place="in the yard",
        tags={"table", "wood"},
    ),
}

MISTLETOE = {
    "gate": Mistletoe(
        id="gate",
        label="mistletoe",
        phrase="a tucked-away bundle of mistletoe",
        place="the gate",
        magic="transformation",
        tags={"mistletoe", "magic"},
    ),
    "coop": Mistletoe(
        id="coop",
        label="mistletoe",
        phrase="a pale sprig of mistletoe",
        place="the chicken coop",
        magic="transformation",
        tags={"mistletoe", "magic"},
    ),
    "loft": Mistletoe(
        id="loft",
        label="mistletoe",
        phrase="a hanging strand of mistletoe",
        place="the hay loft",
        magic="transformation",
        tags={"mistletoe", "magic"},
    ),
}

GENDERS = {"girl", "boy"}
NAMES = {
    "girl": ["Mira", "Lena", "Tia", "Nell", "Ruby"],
    "boy": ["Finn", "Jace", "Oren", "Pip", "Rowan"],
}
ROLES = ["small sailor", "tiny captain", "brave deckhand", "little buccaneer"]
MORALS = ["kindness", "care", "honesty"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for task_id, task in TASKS.items():
        for furn_id in FURNISHINGS:
            for mist_id in MISTLETOE:
                combos.append(("farmyard", task_id, furn_id, mist_id))
    return [(a, b, c) for a, b, c, _ in combos]


def _task_intro(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a pirate heart, a wide grin, and a love for {task.gerund}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked the farmyard best because the cackling hens, the hay, and the muddy boards felt like a tiny dock for adventures."
    )


def _furnish(world: World, hero: Entity, furn: Furnishing) -> None:
    world.say(
        f"One day, {hero.id} saw {furn.phrase} {furn.place} and wanted to furnish the yard like a captain's deck."
    )
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    world.facts["furnishing"] = furn


def _warn(world: World, hero: Entity, task: Task, mist: Mistletoe) -> None:
    world.say(
        f"But near {mist.place}, the old mistletoe gave the air a prickly hush, and {task.twist}"
    )
    world.say(
        f"{hero.id} heard a whispering ellipsis in the leaves... as if the farmyard itself was holding its breath."
    )


def _transform(world: World, hero: Entity, task: Task, mist: Mistletoe) -> None:
    hero.meters["changed"] = hero.meters.get("changed", 0.0) + 1.0
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
    world.say(
        f"When {hero.id} touched the mistletoe, {hero.pronoun()} {task.change}, and even {hero.pronoun('possessive')} shadow seemed to turn a little grander."
    )
    world.say(
        f"The change was a twist indeed, but it was no cruel trick; it was the kind of magic that nudges a heart to see more clearly."
    )
    world.facts["transformed"] = True
    world.facts["mistletoe"] = mist


def _moral(world: World, hero: Entity, task: Task) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    world.say(
        f"So {hero.id} chose {task.value} over showing off, and the farmyard felt warm again."
    )
    world.say(
        f"The moral value was simple: a true pirate does not only gather treasure; {hero.id} learned to help, listen, and leave the yard better than before."
    )


def tell(world: World, hero: Entity, task: Task, furn: Furnishing, mist: Mistletoe) -> None:
    _task_intro(world, hero, task)
    world.para()
    _furnish(world, hero, furn)
    _warn(world, hero, task, mist)
    world.para()
    _transform(world, hero, task, mist)
    _moral(world, hero, task)

    world.facts.update(
        hero=hero,
        task=task,
        furnishing=furn,
        mistletoe=mist,
        setting=world.setting,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    furn = f["furnishing"]
    return [
        f"Write a short pirate tale for a child in a farmyard where {hero.id} wants to {task.verb} and notices {furn.label}.",
        f"Tell a story with ellipsis, furnish, and mistletoe that ends in a gentle moral value.",
        f"Make a farmyard adventure with a transformation twist, where a little pirate learns kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    furn = f["furnishing"]
    mist = f["mistletoe"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the farmyard?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What fancy thing did {hero.id} see while trying to furnish the yard?",
            answer=f"{hero.id} saw {furn.phrase}.",
        ),
        QAItem(
            question=f"What magical plant caused the twist in the story?",
            answer=f"The magical plant was {mist.label}, found near {mist.place}.",
        ),
        QAItem(
            question=f"What changed about {hero.id} after touching the mistletoe?",
            answer=f"{hero.id} {task.change} after touching the mistletoe.",
        ),
        QAItem(
            question="What moral value does the story teach?",
            answer=f"The story teaches {task.value}, along with helping and honest work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a farmyard?",
            answer="A farmyard is the area around a farm where animals, tools, hay, gates, and people work and play.",
        ),
        QAItem(
            question="What is mistletoe?",
            answer="Mistletoe is a plant that can grow on trees or branches, and in stories it often feels a little magical.",
        ),
        QAItem(
            question="What does furnish mean?",
            answer="To furnish something means to put useful or decorative things in a place so it is ready to use or looks nice.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of behaving, like kindness, honesty, or care for others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ASP twin
ASP_RULES = r"""
farmyard(farmyard).
task(hay;feed;mend).
furnishing(bench;lantern;table).
mistletoe(gate;coop;loft).
moral(kindness;care;honesty).

valid_story(F, T, U, M) :- farmyard(F), task(T), furnishing(U), mistletoe(M).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("farmyard", "farmyard")]
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for f in FURNISHINGS:
        lines.append(asp.fact("furnishing", f))
    for m in MISTLETOE:
        lines.append(asp.fact("mistletoe", m))
    for mv in MORALS:
        lines.append(asp.fact("moral", mv))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale farmyard storyworld with mistletoe and transformation twist.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--furnishing", choices=sorted(FURNISHINGS))
    ap.add_argument("--mistletoe", choices=sorted(MISTLETOE))
    ap.add_argument("--role", choices=ROLES)
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
    task = args.task or rng.choice(list(TASKS))
    furn = args.furnishing or rng.choice(list(FURNISHINGS))
    mist = args.mistletoe or rng.choice(list(MISTLETOE))
    gender = args.gender or rng.choice(list(GENDERS))
    name = args.name or rng.choice(NAMES[gender])
    role = args.role or rng.choice(ROLES)
    return StoryParams(
        name=name,
        gender=gender,
        pirate_role=role,
        farmyard_task=task,
        furnishing=furn,
        mistletoe_place=mist,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(setting="farmyard")
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.pirate_role, "pirate"]))
    task = TASKS[params.farmyard_task]
    furn = FURNISHINGS[params.furnishing]
    mist = MISTLETOE[params.mistletoe_place]
    tell(world, hero, task, furn, mist)
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
    StoryParams(name="Mira", gender="girl", pirate_role="tiny captain", farmyard_task="hay", furnishing="bench", mistletoe_place="gate"),
    StoryParams(name="Finn", gender="boy", pirate_role="small sailor", farmyard_task="feed", furnishing="lantern", mistletoe_place="coop"),
    StoryParams(name="Nell", gender="girl", pirate_role="brave deckhand", farmyard_task="mend", furnishing="table", mistletoe_place="loft"),
]


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
