#!/usr/bin/env python3
"""
A small standalone story world for a pirate tale set around an attic ladder,
with a twist and a happy ending.

Premise:
- A child pirate finds a mysterious attic ladder.
- The pirate wants treasure in the attic, but the ladder is wobbly and the
  captain worries about a fall.
- A simple turn happens when a hidden helper item solves the climb.
- The ending proves continuity: the same ladder, same attic, same treasure,
  but now the pirate reaches it safely.

The world uses two kinds of state:
- physical meters: climb, wobble, dust, height, treasure, steadiness
- emotional memes: longing, worry, trust, pride, delight, relief

The twist is that the "treasure" is not gold at all; it is a ship-in-a-bottle
and a map that was waiting in the attic all along.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the attic ladder"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    wear: str = ""


@dataclass
class Gear:
    id: str
    label: str
    helper: str
    solve: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    name: str
    parent: str
    title: str
    seed: Optional[int] = None


SETTING = Setting(place="the attic ladder", affords={"climb", "search"})
ACTIVITY = Activity(
    id="climb",
    verb="climb the attic ladder",
    gerund="climbing the attic ladder",
    rush="dash up the attic ladder",
    mess="wobble",
    soil="dangerous and shaky",
    keyword="attic",
    tags={"attic", "ladder", "twist", "continuity"},
)
PRIZE = Prize(
    label="treasure",
    phrase="an old chest of stories",
    type="treasure",
    wear="hidden",
)
GEAR = Gear(
    id="lantern",
    label="a lantern",
    helper="light the way",
    solve="follow the marks on the steps",
    tags={"light", "attic", "ladder"},
)

NAMES = ["Pip", "Mina", "Jory", "Lila", "Toby", "Nell"]
PARENTS = ["mother", "father", "uncle", "aunt", "captain"]
TITLES = ["stupendous", "continuity"]


def valid_story() -> bool:
    return True


def _do_climb(world: World, hero: Entity) -> None:
    if ("climb", hero.id) in world.fired:
        return
    world.fired.add(("climb", hero.id))
    hero.meters["wobble"] += 1
    hero.memes["longing"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} peered up the attic ladder, where the boards creaked like an old pirate ship."
    )
    world.say(
        f"{hero.id} wanted to {ACTIVITY.verb}, because something up there was calling like treasure."
    )


def _warn(world: World, parent: Entity, hero: Entity) -> None:
    if ("warn", hero.id) in world.fired:
        return
    world.fired.add(("warn", hero.id))
    hero.memes["worry"] += 1
    world.say(
        f"{parent.label or parent.type.capitalize()} looked at the rickety ladder and said, "
        f'"Easy now. That ladder has a twist in its steps."'
    )


def _twist(world: World, hero: Entity) -> None:
    if ("twist", hero.id) in world.fired:
        return
    world.fired.add(("twist", hero.id))
    hero.memes["surprise"] += 1
    world.say(
        f"{hero.id} found the twist: the attic was not full of gold coins at all."
    )
    world.say(
        f"Inside the dusty box waited a tiny ship in a bottle and a folded map with the same mark as the ladder."
    )
    world.facts["twist"] = "ship in a bottle and map"
    world.facts["treasure_kind"] = "storybook treasure"


def _helper(world: World, parent: Entity, hero: Entity) -> None:
    if ("helper", hero.id) in world.fired:
        return
    world.fired.add(("helper", hero.id))
    hero.memes["trust"] += 1
    hero.meters["steadiness"] += 1
    world.say(
        f"{parent.id if parent.id != 'Parent' else parent.label or 'the parent'} lit {GEAR.label} and held it low, "
        f"so the steps glowed one by one."
    )
    world.say(
        f"With the light, {hero.id} could {GEAR.solve}, and the ladder felt less wobbly."
    )


def _happy_ending(world: World, hero: Entity, parent: Entity) -> None:
    if ("end", hero.id) in world.fired:
        return
    world.fired.add(("end", hero.id))
    hero.memes["relief"] += 1
    hero.memes["delight"] += 1
    world.say(
        f"{hero.id} climbed down with the map tucked safe under one arm and the tiny ship held careful in the other."
    )
    world.say(
        f"{hero.id} laughed, because the attic treasure was not big and shiny; it was stupendous in a quieter way."
    )
    world.say(
        f"The ladder stayed the same old ladder, but now it carried a better story, and {parent.id.lower() if parent.id != 'Parent' else 'the parent'} smiled at the happy ending."
    )


def tell(name: str, parent_role: str, title: str) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="pirate",
        label="little pirate",
        phrase="a little pirate with a brave hat",
        meters={"wobble": 0.0, "steadiness": 0.0},
        memes={"longing": 0.0, "worry": 0.0, "trust": 0.0, "surprise": 0.0, "delight": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_role,
        label=f"the {parent_role}",
        meters={"steadiness": 0.0},
        memes={"worry": 0.0, "trust": 0.0},
    ))
    prize = world.add(Entity(
        id="Prize",
        type="treasure",
        label=PRIZE.label,
        phrase=PRIZE.phrase,
        owner=hero.id,
    ))
    lantern = world.add(Entity(
        id=GEAR.id,
        type="gear",
        label=GEAR.label,
        phrase="a lantern with a warm glow",
        owner=parent.id,
    ))

    world.facts.update(hero=hero, parent=parent, prize=prize, gear=lantern, title=title)

    world.say(
        f"{hero.id} was a {title} little pirate who loved any place that felt like a secret map."
    )
    world.say(
        f"One day, {hero.id} heard about {SETTING.place} and thought it might hide {prize.phrase}."
    )
    world.para()
    _do_climb(world, hero)
    _warn(world, parent, hero)
    world.para()
    _helper(world, parent, hero)
    _twist(world, hero)
    _happy_ending(world, hero, parent)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        "Write a pirate tale for young children about an attic ladder, a surprise, and a kind ending.",
        f"Tell a story where {hero.id} the pirate climbs an attic ladder and finds a twist waiting in the attic.",
        "Make the story feel like a little sea adventure indoors, with a safe climb and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    prize = world.facts["prize"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little pirate who loves secret places and treasure.",
        ),
        QAItem(
            question=f"What was special about {SETTING.place}?",
            answer=f"It had an attic ladder, and that ladder led up to a dusty surprise.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer="The treasure was not gold coins. It was a ship in a bottle and a folded map waiting in the attic.",
        ),
        QAItem(
            question=f"How did the grown-up help?",
            answer=f"{parent.id} lit the lantern and helped make the climb safer, so the pirate could see the steps clearly.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} coming back down safely while holding the treasure and smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ladder for?",
            answer="A ladder helps someone climb up or down to a higher place.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so people can see in dark places.",
        ),
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a person from old sea stories who sails ships and looks for treasure.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world around an attic ladder.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--title", choices=TITLES)
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
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    title = args.title or rng.choice(TITLES)
    return StoryParams(name=name, parent=parent, title=title)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.parent, params.title)
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


ASP_RULES = r"""
% Inline declarative twin, kept simple for parity checks.
story_theme(stupendous).
story_theme(continuity).
setting(attic_ladder).
feature(twist).
feature(happy_ending).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "attic_ladder"),
        asp.fact("feature", "twist"),
        asp.fact("feature", "happy_ending"),
        asp.fact("theme", "stupendous"),
        asp.fact("theme", "continuity"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show feature/1. #show theme/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    needed = {
        ("setting", ("attic_ladder",)),
        ("feature", ("twist",)),
        ("feature", ("happy_ending",)),
        ("theme", ("stupendous",)),
        ("theme", ("continuity",)),
    }
    if atoms == needed:
        print("OK: ASP facts match the story world's registry.")
        return 0
    print("MISMATCH: ASP facts do not match.")
    print("got:", sorted(atoms))
    print("want:", sorted(needed))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show feature/1. #show theme/1."))
    return sorted({(sym.name, tuple(a.name for a in sym.arguments)) for sym in model})


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1. #show feature/1. #show theme/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP registry:")
        for atom in asp_valid():
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Pip", parent="mother", title="stupendous"),
            StoryParams(name="Mina", parent="father", title="continuity"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
