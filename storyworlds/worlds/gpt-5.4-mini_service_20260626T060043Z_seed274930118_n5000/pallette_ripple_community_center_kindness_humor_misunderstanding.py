#!/usr/bin/env python3
"""
A standalone story world about a community center, a pallette, and a ripple of
kindness, humor, and misunderstanding.

The story premise is simple: a child brings a pallette to the community center
for an art afternoon, a small misunderstanding makes everyone think a spilled
ripple of paint ruined the plan, and the people use kindness and humor to turn
the moment into something better.

This file follows the Storyweavers world contract:
- defines StoryParams and the standard CLI helpers
- generates a single simulated story world
- supports QA, JSON, trace, ASP, verify, and show-asp modes
- uses physical meters and emotional memes in the world model
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
    place: str = "the community center"
    affords: set[str] = field(default_factory=lambda: {"painting"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)
    keyword: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class SupportItem:
    id: str
    label: str
    prep: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return True


SETTING = Setting()

ACTIVITIES = {
    "painting": Activity(
        id="painting",
        verb="paint a big poster",
        gerund="painting a big poster",
        rush="dash for the paint cups",
        mess="paint",
        soil="splashed with paint",
        tags={"kindness", "humor", "misunderstanding"},
        keyword="ripple",
    )
}

PRIZES = {
    "pallette": Prize(
        label="pallette",
        phrase="a bright pallette with four paint wells",
        type="pallette",
        plural=False,
    )
}

SUPPORT = {
    "smock": SupportItem(
        id="smock",
        label="a long art smock",
        prep="put on a long art smock first",
        tags={"painting"},
    ),
    "towels": SupportItem(
        id="towels",
        label="paper towels",
        prep="keep paper towels nearby",
        tags={"paint"},
    ),
}

NAMES = ["Maya", "Noah", "Lina", "Owen", "Iris", "Eli", "Zoe", "June"]
TRAITS = ["funny", "kind", "curious", "bouncy", "careful", "silly"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type=params.parent, label="the community helper", meters={}, memes={}))
    prize = world.add(Entity(
        id=params.prize,
        type=params.prize,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
    ))

    activity = ACTIVITIES[params.activity]
    hero.memes["joy"] = 1.0
    hero.memes["kindness"] = 1.0

    world.say(f"{hero.id} was a {params.trait} child who loved the busy rooms at the community center.")
    world.say(f"{hero.pronoun().capitalize()} came in carrying {prize.phrase} because {activity.gerund} sounded like the best kind of afternoon.")
    world.say(f"The art table was set for a ripple of color, and {hero.id} was already grinning at the paint cups.")

    world.para()
    world.say(f"At the community center, {helper.label} pointed to the poster board and said, \"Let's be neat first.\"")
    world.say(f"{hero.id} nodded, but then {hero.pronoun('possessive')} sleeve nudged the table and a little ripple of paint slid toward the edge.")
    world.say(f"A nearby kid gasped, and for a moment everyone thought the pallette had been ruined.")

    hero.memes["misunderstanding"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(f"{hero.id} froze, because {hero.pronoun('possessive')} face said, \"Oh no, I made a giant mess.\"")

    world.para()
    helper.memes["kindness"] = 1.0
    helper.memes["humor"] = 1.0
    world.say(f"Then {helper.label} laughed softly and said, \"That is not a disaster. That is a very dramatic ripple.\"")
    world.say(f"{hero.id} blinked, and then the room giggled with {helper.pronoun('possessive')} joke.")
    world.say(f"Someone handed over paper towels, and {hero.id} wiped the table while smiling again.")

    world.say(f"{hero.id} put on {SUPPORT['smock'].label} and kept painting, careful this time.")
    world.say(f"With the mess cleaned and the joke still floating around, the poster turned bright and cheerful.")
    world.say(f"In the end, the community center had a funny story, a clean table, and a pallette that started the whole ripple of kindness.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        support=SUPPORT["smock"],
        setting=SETTING,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a funny story for a small child about {hero.id} at the community center, a pallette, and a paint ripple.",
        f"Tell a comedy where kindness and humor help after a misunderstanding during an art project.",
        f"Write a gentle story about a child, a paint mishap, and a happy fix at the community center.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Where does {hero.id} spend the afternoon with {prize.label}?",
            answer=f"{hero.id} spends the afternoon at the community center with {prize.label}.",
        ),
        QAItem(
            question=f"What small trouble happened when {hero.id} was painting?",
            answer="A little ripple of paint slid toward the edge, and some people first thought the pallette had been ruined.",
        ),
        QAItem(
            question=f"How did {helper.label} help fix the misunderstanding?",
            answer=f"{helper.label} used kindness and humor, called it a dramatic ripple, and helped everyone calm down.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The table got cleaned, the child kept painting, and the room ended with laughter instead of worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community center?",
            answer="A community center is a public place where people gather for activities, games, classes, and events.",
        ),
        QAItem(
            question="What is paint used for?",
            answer="Paint is used to add color to pictures, posters, walls, and other art projects.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something means one thing, but it really means something else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="community center", activity="painting", prize="pallette", name="Maya", gender="girl", parent="mother", trait="funny"),
    StoryParams(place="community center", activity="painting", prize="pallette", name="Noah", gender="boy", parent="father", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world at the community center.")
    ap.add_argument("--place", choices=["community center"])
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    return StoryParams(
        place=args.place or "community center",
        activity=args.activity or "painting",
        prize=args.prize or "pallette",
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


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
place(community_center).
activity(painting).
prize(pallette).
kindness.
humor.
misunderstanding.

story_ok :- place(community_center), activity(painting), prize(pallette),
            kindness, humor, misunderstanding.

#show story_ok/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "community_center"),
        asp.fact("activity", "painting"),
        asp.fact("prize", "pallette"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "misunderstanding"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP rules produce the expected story_ok model.")
        return 0
    print("MISMATCH: ASP rules did not produce story_ok.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible comedy story: community center / painting / pallette")
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
