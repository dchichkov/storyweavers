#!/usr/bin/env python3
"""
A small folk-tale storyworld about a junior forester, a credible warning, and
a twist in the woodland path.

Premise:
- A young forester called Junie loves walking the woods and helping the old
  forest keeper.
- A trusted helper warns about a tricky twist in the trail.
- Junie ignores the warning, reaches the twist, and gets into a muddle.
- A clever, gentle compromise turns the problem into a safe ending.

This script models physical meters and emotional memes, emits a story plus QA,
and includes an ASP twin for the reasonableness gate.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self):
        for k in ["scrape", "wet", "lost", "sweat", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "confidence", "relief", "curiosity", "frustration"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    trouble: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def story_verb(name: str) -> str:
    return name


PLACES = {
    "wood": Place("the wood", "wood", {"walk", "twist"}),
    "grove": Place("the grove", "grove", {"walk", "twist"}),
    "lane": Place("the lane by the trees", "lane", {"walk", "twist"}),
}

ACTIONS = {
    "twist": Action(
        id="twist",
        verb="follow the twist in the path",
        gerund="following the twist in the path",
        rush="dash around the bend",
        trouble="knotted and confused",
        zone={"feet", "legs"},
        keyword="twist",
        tags={"twist", "path", "wood"},
    ),
    "walk": Action(
        id="walk",
        verb="walk the forest path",
        gerund="walking the forest path",
        rush="hurry along the path",
        trouble="muddy and slow",
        zone={"feet", "legs"},
        keyword="walk",
        tags={"wood", "path"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="sturdy boots",
        covers={"feet"},
        guards={"wet", "scrape"},
        prep="put on sturdy boots",
        tail="went back with the sturdy boots",
        plural=True,
    ),
    Gear(
        id="cloak",
        label="a green cloak",
        covers={"torso"},
        guards={"wet"},
        prep="tie on a green cloak",
        tail="set off again under the green cloak",
    ),
    Gear(
        id="staff",
        label="a smooth walking staff",
        covers={"hands"},
        guards={"scrape"},
        prep="take a smooth walking staff",
        tail="walked on with the smooth staff",
    ),
]

KNOWLEDGE = {
    "twist": [(
        "What is a twist in a path?",
        "A twist in a path is a bend that turns the way to go, so you have to look carefully before you step."
    )],
    "wood": [(
        "What is a forest?",
        "A forest is a place with many trees growing close together, along with birds, bushes, and shady paths."
    )],
    "boots": [(
        "What are boots for?",
        "Boots protect your feet and help them stay dry or safe when the ground is rough or wet."
    )],
    "path": [(
        "Why do people watch the path in the woods?",
        "People watch the path because tree roots, mud, and bends can make it easy to slip or lose the way."
    )],
}


@dataclass
class StoryParams:
    place: str
    action: str
    gear: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def reasonableness_gate(action: Action, gear: Gear) -> bool:
    return bool(action.zone & gear.covers or gear.guards & {"scrape", "wet"})


def select_gear(action: Action) -> Optional[Gear]:
    for gear in GEAR:
        if reasonableness_gate(action, gear):
            return gear
    return None


def predict_mess(world: World, hero: Entity, action: Action) -> dict:
    sim = World(world.place)
    sim.entities = {k: Entity(**{
        **vars(v),
        "meters": dict(v.meters),
        "memes": dict(v.memes),
    }) for k, v in world.entities.items()}
    sim.zone = set(action.zone)
    h = sim.get(hero.id)
    h.memes["curiosity"] += 1
    if action.id == "twist":
        h.meters["lost"] += 1
    return {"lost": h.meters["lost"] >= THRESHOLD}


def build_story(world: World, hero: Entity, elder: Entity, action: Action, gear: Gear) -> None:
    world.say(
        f"In the old wood, there was a junior forester named {hero.id}. "
        f"{hero.pronoun().capitalize()} was small, quick, and very credible, for {hero.id} remembered the names of birds, bark, and moss."
    )
    world.say(
        f"{hero.id} loved {action.gerund}, because the trees leaned close like listening friends."
    )
    world.say(
        f"One day, {elder.id} said, \"Be careful at the {action.keyword}; it can turn a wanderer round and round.\""
    )
    hero.memes["curiosity"] += 1
    elder.memes["worry"] += 1

    world.para()
    world.say(
        f"But {hero.id} wanted to see the bend at once, so {hero.pronoun()} hurried ahead and tried to {action.verb}."
    )
    if predict_mess(world, hero, action)["lost"]:
        hero.meters["lost"] += 1
        hero.memes["frustration"] += 1
        world.say(
            f"At the twist, the trail looked {action.trouble}, and the little forester lost the sun from sight."
        )
        world.say(
            f"{elder.id} came along with a calm face and said, \"A true forester looks twice before stepping once.\""
        )

    world.para()
    hero.memes["worry"] += 1
    if gear.id == "boots":
        world.say(
            f"Then {elder.id} smiled and said, \"Put on {gear.label} and take my hand; rough ground is kinder when feet are safe.\""
        )
    else:
        world.say(
            f"Then {elder.id} smiled and said, \"Take {gear.label} and follow me; the path will be easier with care.\""
        )
    world.say(
        f"{hero.id} agreed, and together they {gear.tail}."
    )
    hero.memes["joy"] += 2
    hero.memes["relief"] += 2
    hero.memes["frustration"] = 0
    hero.meters["lost"] = 0
    world.say(
        f"At the end, the bend was no longer scary. {hero.id} could see the way home, the trees stood still and proud, and the junior forester had learned to respect a clever twist."
    )


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    gear = next(g for g in GEAR if g.id == params.gear)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="boy",
        traits=["junior", "credible", "forester"],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="elder",
        traits=["wise", "gentle"],
    ))
    tool = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        plural=gear.plural,
    ))
    tool.worn_by = hero.id

    build_story(world, hero, helper, action, gear)
    world.facts.update(hero=hero, helper=helper, gear=gear, action=action, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f"Write a folk tale for a child about a junior credible forester named {hero.id} and a twist in the woods.",
        f"Tell a short story where {hero.id} wants to {action.verb} but learns to listen to a wise helper.",
        "Write a gentle forest tale with a surprise turn, a safe helper, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    action = f["action"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the junior forester in the story?",
            answer=f"The junior forester is {hero.id}. {hero.id} is the little forest keeper who learns from the old path."
        ),
        QAItem(
            question=f"What warning did {helper.id} give about the path?",
            answer=f"{helper.id} warned that the {action.keyword} could turn a wanderer round and round."
        ),
        QAItem(
            question=f"What helped {hero.id} stay safe at the end?",
            answer=f"{gear.label} helped {hero.id} travel safely, and the two of them went on together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["action"].tags) | {"wood", "path", "boots"}
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            for q, a in pairs:
                out.append(QAItem(question=q, answer=a))
    return out


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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(action.zone):
            lines.append(asp.fact("zone", aid, r))
        lines.append(asp.fact("trouble", aid, action.keyword))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,G) :- zone(A,R), covers(G,R).
has_fix(A) :- at_risk(A,G), guards(G,scrape).
has_fix(A) :- at_risk(A,G), guards(G,wet).
valid(A,G) :- action(A), gear(G), has_fix(A).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for aid, action in ACTIONS.items():
        for g in GEAR:
            if reasonableness_gate(action, g):
                out.append((aid, g.id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a junior forester and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--name", default="Junie")
    ap.add_argument("--helper", default="Old Bram")
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
    place = args.place or rng.choice(list(PLACES))
    action = args.action or rng.choice(list(PLACES[place].affords & set(ACTIONS)))
    gear = args.gear or rng.choice([g.id for g in GEAR if reasonableness_gate(ACTIONS[action], g)])
    if not reasonableness_gate(ACTIONS[action], next(g for g in GEAR if g.id == gear)):
        raise StoryError("That gear does not make sense for this forest trouble.")
    return StoryParams(place=place, action=action, gear=gear, hero_name=args.name, helper_name=args.helper)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (action, gear) combos:\n")
        for action, gear in combos:
            print(f"  {action:8} {gear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("wood", "twist", "boots", "Junie", "Old Bram"),
            StoryParams("grove", "walk", "cloak", "Lark", "Grand Elm"),
        ]
        samples = [generate(p) for p in curated]
    else:
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
