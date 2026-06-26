#!/usr/bin/env python3
"""
gaze_ant_cautionary_fairy_tale.py
=================================

A small cautionary fairy-tale storyworld about a curious gaze, a little ant,
and the lesson that some looks can be unkind even when no one means harm.

Premise:
- A child in a fairy-tale garden loves to gaze at tiny things.
- An ant carries a crumb home across a stone path.
- The child's long, staring gaze unsettles the ant and blocks the path.

Turn:
- The child almost follows the ant too closely, and the ant's load begins to
  wobble near a puddle and a hungry sparrow's shadow.
- A kind elder explains that noticing is good, but chasing or hovering can
  frighten small creatures.

Resolution:
- The child softens the gaze, kneels still, and lets the ant pass.
- The ant reaches the nest, and the child learns to look with care.

This module follows the storyworld contract:
- one self-contained stdlib script
- results imported eagerly, asp lazily
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- ASP twin and verification
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
    touched: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "wizard"}
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
    indoor: bool = False
    allows: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    habitat: str
    burden: str
    cautious_about: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def creatures(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "creature"]


SETTINGS = {
    "garden": Setting(place="the moonlit garden", indoor=False, allows={"gaze", "follow"}),
    "meadow": Setting(place="the flower meadow", indoor=False, allows={"gaze", "follow"}),
    "path": Setting(place="the stone path", indoor=False, allows={"gaze", "follow"}),
}

ACTIVITIES = {
    "gaze": Activity(
        id="gaze",
        verb="gaze at the little ant",
        gerund="gazing at the little ant",
        rush="lean closer and follow the ant",
        risk="frighten the ant and block its path",
        weather="soft evening",
        keyword="gaze",
        tags={"gaze", "ant"},
    ),
    "follow": Activity(
        id="follow",
        verb="follow the ant",
        gerund="following the ant",
        rush="hurry after the ant",
        risk="startle the ant and make it drop its crumb",
        weather="soft evening",
        keyword="ant",
        tags={"ant"},
    ),
}

CREATURES = {
    "ant": Creature(
        id="ant",
        label="little ant",
        phrase="a little ant with a crumb",
        habitat="under the stones",
        burden="crumb",
        cautious_about={"shadow", "stomp", "stare"},
    )
}

HERO_NAMES = ["Mira", "Lina", "Toby", "Nell", "Arin", "Pip", "June", "Sage"]
TRAITS = ["curious", "gentle", "restless", "thoughtful", "bright-eyed"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _build_entity_name(name: str, gender: str, trait: str) -> Entity:
    return Entity(id=name, kind="character", type=_hero_type(gender), traits=["little", trait])


def _tell(world: World, params: StoryParams) -> World:
    hero = world.add(_build_entity_name(params.name, params.gender, params.trait))
    parent = world.add(Entity(id="elder", kind="character", type=params.parent, label="the elder"))
    ant = world.add(Entity(
        id="ant",
        kind="creature",
        type="ant",
        label=CREATURES["ant"].label,
        phrase=CREATURES["ant"].phrase,
        owner="nest",
        caretaker=None,
        plural=False,
    ))

    act = ACTIVITIES[params.activity]
    world.facts.update(hero=hero, parent=parent, ant=ant, activity=act, setting=world.setting)

    world.say(
        f"Once in {world.setting.place}, there lived a little {params.trait} "
        f"{hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved quiet corners and could not help {act.gerund} when the day was still."
    )
    world.say(
        f"One soft evening, {hero.id} found {ant.phrase} hurrying over a stone."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} long {act.keyword} made the ant pause."
    )
    world.say(
        f"The tiny traveler looked smaller and smaller as {hero.id} began to {act.rush}."
    )
    if act.id == "gaze":
        world.say(
            f"That was a poor choice, for a steady gaze can feel heavy to a creature carrying supper home."
        )
    else:
        world.say(
            f"That was a poor choice, for running after a tiny ant can make its burden tremble."
        )

    world.para()
    world.say(
        f"Then the elder came near and said, "
        f"\"A kind eye is a gentle thing, but a chasing eye can be a storm for small feet.\""
    )
    world.say(
        f"{hero.id} stopped at once and listened."
    )
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    hero.memes["care"] = hero.memes.get("care", 0) + 1

    world.para()
    world.say(
        f"{hero.id} knelt very still, softened {hero.pronoun('possessive')} gaze, and let the ant go on."
    )
    world.say(
        f"The ant crossed the last stone, carried the crumb home, and vanished safely beneath the roots."
    )
    world.say(
        f"At the end, {hero.id} learned that looking carefully is better than looking too hard."
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in ACTIVITIES.values():
            if act.id in setting.allows:
                combos.append((place, act.id))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.allows):
            lines.append(asp.fact("allows", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("burden", cid, c.burden))
        for x in sorted(c.cautious_about):
            lines.append(asp.fact("cautious_about", cid, x))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act) :- allows(Place, Act), activity(Act), setting(Place).
cautionary(Act) :- tag(Act, gaze).
cautionary(Act) :- tag(Act, ant).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and args.activity is None or c[1] == args.activity]
    # fix precedence carefully
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS) if hasattr(args, "trait") else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short cautionary fairy tale for a child named {hero.id} who keeps {act.gerund}.',
        f'Tell a fairy-tale story where a {hero.type} learns why {act.verb} can be rude to a tiny creature.',
        f'Write a gentle story using the word "{act.keyword}" and a lesson about being careful with a small ant.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, ant, act = f["hero"], f["parent"], f["ant"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.traits[-1]} {hero.type}, and the elder who teaches {hero.id} to be careful."
        ),
        QAItem(
            question=f"What was {hero.id} doing that bothered the ant?",
            answer=f"{hero.id} was {act.gerund}, and that long look or chase made the ant feel crowded."
        ),
        QAItem(
            question=f"What did the elder say to help {hero.id} choose better?",
            answer=(
                "The elder said that a kind eye is gentle, but a chasing eye can feel like a storm for small feet."
            ),
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} softened {hero.pronoun('possessive')} gaze, let the ant pass, and the ant carried its crumb home safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ant?",
            answer="An ant is a very small insect that can carry bits of food and work together with other ants."
        ),
        QAItem(
            question="What does it mean to gaze at something?",
            answer="To gaze means to look at something for a while, often with quiet attention."
        ),
        QAItem(
            question="Why can following a tiny creature be a problem?",
            answer="Following too closely can frighten a small creature, block its path, or make it drop what it is carrying."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="gaze", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="meadow", activity="follow", name="Toby", gender="boy", parent="father", trait="thoughtful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fairy tale storyworld about a gaze and an ant.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    _tell(world, params)
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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity) combos:\n")
        for place, act in combos:
            print(f"  {place:10} {act}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
