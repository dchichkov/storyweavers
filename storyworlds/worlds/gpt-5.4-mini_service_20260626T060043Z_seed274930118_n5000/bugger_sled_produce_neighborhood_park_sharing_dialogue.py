#!/usr/bin/env python3
"""
A small fable-like story world set in a neighborhood park.

Seeded premise:
- bugger
- sled
- produce

Narrative instruments:
- Sharing
- Dialogue

The story stays child-facing and concrete: a little character wants a sled
ride, the park has produce to carry, and the resolution comes through sharing
and spoken kindness.
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str = "the neighborhood park"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    neighbor: str
    neighbor_type: str
    produce: str
    produce_label: str
    seed: Optional[int] = None


HEROES = [
    ("Bugger", "boy"),
    ("Bugger", "girl"),
    ("Milo", "boy"),
    ("Luna", "girl"),
]

NEIGHBORS = [
    ("Mrs. Reed", "mother"),
    ("Mr. Pike", "father"),
    ("Aunt Jun", "woman"),
    ("Uncle Tom", "man"),
]

PRODUCE = {
    "apples": ("a basket of apples", True),
    "carrots": ("a crate of carrots", False),
    "pears": ("a bag of pears", True),
    "corn": ("a bundle of corn", False),
}

ASP_RULES = r"""
hero(H).
neighbor(N).
produce(P).
valid(H,N,P) :- hero(H), neighbor(N), produce(P).
"""

# ------------------------------------------------------------
# World model
# ------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    neighbor = w.add(Entity(id="neighbor", kind="character", type=params.neighbor_type, label=params.neighbor))
    sled = w.add(Entity(id="sled", type="sled", label="sled"))
    produce = w.add(Entity(
        id="produce",
        type="produce",
        label=params.produce,
        phrase=params.produce_label,
        owner=neighbor.id,
        caretaker=neighbor.id,
        plural=PRODUCE[params.produce][1],
    ))
    sled.carried_by = hero.id

    # Act 1: setup
    w.say(f"In the neighborhood park, {hero.label} was a little bugger with a bright grin.")
    w.say(f"{hero.label.capitalize()} loved the old sled by the hill and wanted to race it down the grass.")
    w.say(f"Near the bench, {neighbor.label} kept {produce.phrase} ready for the shared picnic.")
    w.para()

    # Act 2: conflict through dialogue
    w.say(f"{hero.label.capitalize()} tugged the sled closer and said, “I want the sled all to myself!”")
    w.say(f"{neighbor.label} shook {neighbor.pronoun('possessive')} head and said, “Not today. The park is for sharing, and the produce must stay safe.”")
    hero.memes["want"] = 1
    hero.memes["stingy"] = 1
    produce.meters["at_risk"] = 1
    w.say(f"The wheels bumped the path, and a pear or carrot could have rolled into the dirt.")
    w.para()

    # Act 3: turn and resolution
    w.say(f"{hero.label.capitalize()} looked at the sled, then at the {params.produce}, and became quiet for a moment.")
    w.say(f"“What if we share?” {hero.label} asked. “I can pull the sled, and you can set the produce on top in a careful pile.”")
    w.say(f"{neighbor.label} smiled. “That is a fair plan,” {neighbor.pronoun()} said. “Two helpers are better than one.”")
    hero.memes["generous"] = 1
    hero.memes["joy"] = 1
    produce.carried_by = sled.id
    sled.meters["load"] = 1
    w.say(f"So they tied the basket steady, rode the sled in a slow circle, and carried the produce without dropping a thing.")
    w.say(f"By the time the sun slipped low, {hero.label} had learned that a shared ride can be the happiest ride of all.")

    w.facts.update(hero=hero, neighbor=neighbor, produce=produce, sled=sled)
    return w


# ------------------------------------------------------------
# Narrative registries
# ------------------------------------------------------------
def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    neighbor: Entity = world.facts["neighbor"]
    produce: Entity = world.facts["produce"]
    return [
        QAItem(
            question=f"Why did {hero.label} have to stop and think about the sled?",
            answer=(
                f"{hero.label} wanted the sled all to {hero.pronoun('object')}self, "
                f"but {neighbor.label} reminded {hero.pronoun('object')} that the park was for sharing "
                f"and that the {produce.label} had to stay safe."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} and {neighbor.label} do instead of fighting?",
            answer=(
                f"They shared the sled. {hero.label} pulled it carefully, {neighbor.label} set the {produce.label} on top, "
                f"and they rode together without spilling anything."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} learn by the end?",
            answer=(
                f"{hero.label} learned that sharing can make a day better, because the sled and the {produce.label} were both used well "
                f"and everyone got to smile."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sled for?",
            answer="A sled is a low ride that can slide over snow, grass, or a smooth hill when someone pulls or pushes it.",
        ),
        QAItem(
            question="What is produce?",
            answer="Produce means fruits and vegetables, like apples, carrots, pears, and corn.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something too, so everyone can have a fair turn.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is when characters speak to each other and the story shows their words.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fable-like story for young children set in a neighborhood park about a bugger, a sled, and produce.',
        'Tell a gentle story with dialogue where two neighbors solve a problem by sharing a sled.',
        'Write a short moral tale in which a child learns to share produce and play kindly in the park.',
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


# ------------------------------------------------------------
# ASP twin
# ------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines = []
    for hero, _ in HEROES:
        lines.append(asp.fact("hero", hero))
    for neighbor, _ in NEIGHBORS:
        lines.append(asp.fact("neighbor", neighbor))
    for p in PRODUCE:
        lines.append(asp.fact("produce", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(h, n, p) for h, _ in HEROES for n, _ in NEIGHBORS for p in PRODUCE]


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ------------------------------------------------------------
# Required interface
# ------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like sharing story set in a neighborhood park.")
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"], dest="hero_type")
    ap.add_argument("--neighbor")
    ap.add_argument("--neighbor-type", choices=["mother", "father", "woman", "man"], dest="neighbor_type")
    ap.add_argument("--produce", choices=sorted(PRODUCE))
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
    hero, hero_type = (args.hero, args.hero_type)
    neighbor, neighbor_type = (args.neighbor, args.neighbor_type)
    produce = args.produce

    if hero is None:
        hero, hero_type = rng.choice(HEROES)
    elif hero_type is None:
        hero_type = "boy" if hero == "Bugger" else rng.choice(["boy", "girl"])

    if neighbor is None:
        neighbor, neighbor_type = rng.choice(NEIGHBORS)
    elif neighbor_type is None:
        neighbor_type = "mother"

    if produce is None:
        produce = rng.choice(sorted(PRODUCE))

    if hero == neighbor:
        raise StoryError("The hero and neighbor must be different characters.")

    return StoryParams(
        hero=hero,
        hero_type=hero_type or "boy",
        neighbor=neighbor,
        neighbor_type=neighbor_type or "mother",
        produce=produce,
        produce_label=PRODUCE[produce][0],
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.plural:
            bits.append("plural=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for h, n, p in models[:50]:
            print(f"  {h:8} {n:10} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Bugger", "boy", "Mrs. Reed", "mother", "apples", PRODUCE["apples"][0]),
            StoryParams("Bugger", "girl", "Mr. Pike", "father", "carrots", PRODUCE["carrots"][0]),
            StoryParams("Milo", "boy", "Aunt Jun", "woman", "pears", PRODUCE["pears"][0]),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} with {p.produce}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
