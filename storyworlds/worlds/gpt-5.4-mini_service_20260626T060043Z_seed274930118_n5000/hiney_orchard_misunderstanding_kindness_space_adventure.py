#!/usr/bin/env python3
"""
Storyworld: Hiney Orchard Misunderstanding Kindness Space Adventure
===================================================================

A tiny, classical story world set in an orchard with a space-adventure feel:
a child plans a playful mission, a misunderstanding causes a wobble, and a
kind act clears the air.

The seed words steer the premise:
- hiney
- misunderstanding
- kindness
- orchard
- space adventure

The core premise is simple and child-facing:
a small explorer in an orchard wants to reach a shiny "space fruit" at the top
of the tree, but someone thinks the plan is rude or silly because of a word
they overhear. A helpful kindness gesture resolves the misunderstanding.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
    affords: set[str] = field(default_factory=lambda: {"space_walk", "climb", "stargaze"})


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    risk: str
    can_misunderstand: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    region: str = "torso"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Story registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"space_walk", "climb", "stargaze"}),
}

MISSIONS = {
    "space_walk": Mission(
        id="space_walk",
        verb="space-walk to the tallest apple tree",
        gerund="space-walking between the trees",
        rush="dash toward the ladder like a rocket",
        keyword="space",
        risk="might knock the basket over",
        can_misunderstand=True,
        tags={"space", "orchard"},
    ),
    "stargaze": Mission(
        id="stargaze",
        verb="look for star-shaped apples",
        gerund="staring up at the branches",
        rush="run under the moonlit trees",
        keyword="stars",
        risk="might make the others think someone is lost",
        can_misunderstand=True,
        tags={"space", "orchard"},
    ),
    "climb": Mission(
        id="climb",
        verb="climb up to the ripe apples",
        gerund="climbing carefully",
        rush="scramble up the trunk",
        keyword="ladder",
        risk="might shake the branches",
        can_misunderstand=True,
        tags={"orchard"},
    ),
}

TREASURES = {
    "fruit_cap": Treasure(
        label="space cap",
        phrase="a shiny silver cap with a star on it",
        type="cap",
        region="head",
    ),
    "jacket": Treasure(
        label="jacket",
        phrase="a bright blue jacket",
        type="jacket",
        region="torso",
    ),
    "satchel": Treasure(
        label="satchel",
        phrase="a little canvas satchel",
        type="satchel",
        region="torso",
    ),
}

GIRL_NAMES = ["Luna", "Mina", "Tilly", "Nora", "Ivy"]
BOY_NAMES = ["Arlo", "Pip", "Jasper", "Milo", "Theo"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mission: str
    treasure: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.affords:
            for treasure_id in TREASURES:
                combos.append((place, mission_id, treasure_id))
    return combos


def reasonableness_gate(mission: Mission, treasure: Treasure) -> bool:
    if mission.id == "space_walk" and treasure.region != "head":
        return False
    return True


def explain_rejection(mission: Mission, treasure: Treasure) -> str:
    return (
        f"(No story: a {treasure.label} would not be the right thing for a "
        f"{mission.gerund} misunderstanding in the orchard.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small orchard space-adventure story world with a misunderstanding and a kindness turn."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()

    if args.mission and args.treasure:
        m, t = MISSIONS[args.mission], TREASURES[args.treasure]
        if not reasonableness_gate(m, t):
            raise StoryError(explain_rejection(m, t))

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.treasure is None or c[2] == args.treasure)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, mission_id, treasure_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father"])
    return StoryParams(place=place, mission=mission_id, treasure=treasure_id, name=name, gender=gender, companion=companion)


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="companion", kind="character", type=params.companion, label=f"the {params.companion}"))
    mission = MISSIONS[params.mission]
    treasure = TREASURES[params.treasure]
    item = world.add(Entity(
        id="treasure",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    # Act 1
    world.say(
        f"{hero.id} was a little explorer who loved space adventure stories and the orchard at dusk."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept a favorite word, hiney, because {hero.pronoun('possessive')} {companion} said silly words could make a hard day feel lighter."
    )
    world.say(
        f"One afternoon, {hero.id} packed {hero.pronoun('possessive')} {item.label} and dreamed of a {mission.keyword} mission among the apple trees."
    )

    # Act 2
    world.para()
    world.say(
        f"In {world.setting.place}, {hero.id} wanted to {mission.verb}, but a small misunderstanding floated up like a cloud."
    )
    world.say(
        f"{hero.pronoun().capitalize()} said the word hiney while pointing at a cart, but {helper.label} thought {hero.pronoun('subject')} was being rude."
    )
    world.say(
        f"That made the air feel bumpy and tight, and {hero.id} felt the adventure pause."
    )
    world.facts["misunderstanding"] = True
    world.facts["hurt_feelings"] = True

    # Act 3
    world.para()
    world.say(
        f"Then {hero.id} took a careful breath and showed {helper.pronoun('object')} a tiny drawing of a rocket landing by an apple crate."
    )
    world.say(
        f"{hero.id} explained that hiney was only a silly joke word, not a mean one."
    )
    world.say(
        f"{helper.label.capitalize()} softened right away, because kindness can straighten out a crooked moment."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, offered a hand, and said they could try the mission together."
    )
    world.say(
        f"Soon {hero.id} was {mission.gerund} in {world.setting.place}, {item.label} stayed safe, and the orchard felt like a friendly starship garden."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        mission=mission,
        treasure=item,
        resolved=True,
        kindness=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    return [
        f'Write a gentle space-adventure story set in an orchard that includes the word "hiney".',
        f"Tell a short story about {hero.id}, a small explorer, who wants to {mission.verb} but runs into a misunderstanding and fixes it with kindness.",
        f"Write a child-friendly orchard story where a silly word causes confusion, then kindness helps everyone feel better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mission = f["mission"]
    treasure = f["treasure"]
    return [
        QAItem(
            question=f"What kind of story was {hero.id} living in the orchard?",
            answer="It was a space-adventure story with a small misunderstanding and a kind ending.",
        ),
        QAItem(
            question=f"What word caused the misunderstanding?",
            answer="The word was hiney, and it made the helper think the explorer might be being rude.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem with {helper.label}?",
            answer="The explorer explained the joke kindly and showed a drawing, which helped the helper understand.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the orchard mission?",
            answer=f"{hero.id} wanted to {mission.verb}, and the adventure became peaceful once kindness solved the misunderstanding.",
        ),
        QAItem(
            question=f"What stayed safe during the ending?",
            answer=f"The {treasure.label} stayed safe while {hero.id} went on with the mission.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow together.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring with others.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when people do not understand each other the right way at first.",
        ),
        QAItem(
            question="What is a space adventure?",
            answer="A space adventure is a story about exploring, like a brave trip among stars or imagined planets.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} kind={e.kind}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A valid orchard story needs a mission, a treasure, a misunderstanding,
% and a kindness-based resolution.
valid_story(P, M, T) :- place(P), mission(M), treasure(T),
                        orchard(P), can_misunderstand(M), kind_fix(T).

kind_fix(T) :- treasure(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("orchard", pid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        if m.can_misunderstand:
            lines.append(asp.fact("can_misunderstand", mid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("kind_fix", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, m, t) for p, m, t in valid_combos()}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Emit / CLI
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


CURATED = [
    StoryParams(place="orchard", mission="space_walk", treasure="fruit_cap", name="Luna", gender="girl", companion="mother"),
    StoryParams(place="orchard", mission="climb", treasure="jacket", name="Arlo", gender="boy", companion="father"),
    StoryParams(place="orchard", mission="stargaze", treasure="satchel", name="Mina", gender="girl", companion="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible orchard stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.mission} in the orchard"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
