#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/liquor_slumber_oblong_teamwork_mystery_to_solve.py
===============================================================================================================

A small comedy storyworld about a puzzling oblong object, a sleepy plan,
and a teamwork mystery to solve.

Seed words:
- liquor
- slumber
- oblong

This world keeps the narrative child-facing and gentle. The word "liquor"
appears as a label on a locked-up grownup bottle in the background of the
mystery; the actual story centers on a silly household puzzle about a missing
nap-time box and the team effort needed to solve it.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the library nook"
    indoor: bool = True
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
class Mystery:
    label: str
    clue: str
    object_label: str
    object_phrase: str
    involved: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    offers: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _act_mystery(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if e.meters.get("search", 0) < THRESHOLD:
            continue
        sig = ("mystery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["confidence"] = e.memes.get("confidence", 0) + 1
        out.append(f"{e.label} kept looking and felt the puzzle starting to shrink.")
    return out


def _act_help(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes.get("teamwork", 0) < THRESHOLD:
            continue
        sig = ("help", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] = e.memes.get("joy", 0) + 1
        out.append(f"{e.label} was happier because everyone shared the job.")
    return out


CAUSAL_RULES = [
    _act_mystery,
    _act_help,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def find_oblong(world: World, hero: Entity, mystery: Mystery) -> bool:
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.label} peeked under the couch, behind the stack of books, and beside the teacup."
    )
    world.say(
        f"At last, {hero.pronoun()} spotted an oblong box hiding near {mystery.clue}."
    )
    return True


def team_up(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    world.say(
        f"{helper.label} joined {hero.pronoun('object')} and said they should solve it together."
    )
    world.say(
        f"So they made a little plan: one person looked, one person held the lamp, and one person guessed."
    )
    propagate(world, narrate=True)


def solve_mystery(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.meters["solve"] = hero.meters.get("solve", 0) + 1
    helper.meters["solve"] = helper.meters.get("solve", 0) + 1
    world.say(
        f"They used {tool.phrase}, and that was the clue that made the mystery obvious."
    )
    world.say(
        f"The oblong box was not lost at all; it had been turned into a sleepy nest for {mystery.object_phrase}."
    )
    world.say(
        f"{hero.label} laughed, because the very thing everyone hunted turned out to be the nap-time prize."
    )


def intro(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.label} was a curious {hero.type} who loved a good mystery to solve."
    )
    world.say(
        f"{helper.label} was the kind of friend who could turn a muddle into teamwork."
    )
    world.say(
        f"On the shelf sat a bottle labeled liquor, but the grownups had tucked it far away where nobody could reach it."
    )
    world.say(
        f"The real puzzle was the oblong box by the window: nobody knew where {mystery.object_phrase} had gone."
    )


def tension(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.para()
    world.say(
        f"They checked the closet, the chair, and even under a sleepy blanket, but the box was still missing."
    )
    world.say(
        f"{hero.label} frowned and said the room would not feel restful until {mystery.object_phrase} turned up."
    )
    world.say(
        f"{helper.label} answered that a mystery gets smaller when two heads think about it at once."
    )


def resolution(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    world.para()
    team_up(world, helper, hero)
    solve_mystery(world, hero, helper, mystery, tool)
    world.say(
        f"After that, the room felt calm again, and the oblong box sat right where a cozy slumber box should sit."
    )


SETTING = Setting(place="the library nook", indoor=True, affords={"search", "nap"})
ACTIVITY = Activity(
    id="search",
    verb="search for the missing thing",
    gerund="searching for clues",
    rush="dash to the next corner",
    mess="scuffed",
    soil="a little scuffed",
    zone={"hands", "feet"},
    keyword="mystery",
    tags={"mystery", "teamwork"},
)
MYSTERY = Mystery(
    label="the missing slumber box",
    clue="the window cushion",
    object_label="slumber box",
    object_phrase="the soft pillows and folded blanket",
    involved={"oblong", "slumber"},
)
TOOL = Tool(
    id="lamp",
    label="lamp",
    phrase="the little lamp",
    helps={"search"},
    offers="a warm circle of light",
)


def build_world() -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="Mina", kind="character", type="girl", label="Mina"))
    helper = world.add(Entity(id="Pip", kind="character", type="boy", label="Pip"))
    box = world.add(Entity(
        id="box",
        kind="thing",
        type="box",
        label="oblong box",
        phrase="an oblong box full of sleepy cushions",
    ))
    world.facts.update(hero=hero, helper=helper, box=box, mystery=MYSTERY, tool=TOOL)
    intro(world, hero, helper, MYSTERY)
    tension(world, hero, helper, MYSTERY)
    find_oblong(world, hero, MYSTERY)
    resolution(world, hero, helper, MYSTERY, TOOL)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short comedy story for a young child about a mystery to solve, teamwork, and a sleepy oblong box.',
        'Tell a gentle story using the words liquor, slumber, and oblong, where friends solve a puzzle together.',
        'Write a funny story in which two children search for a missing nap-time item and learn that teamwork helps.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question="Who were the two friends in the story?",
            answer=f"The friends were {hero.label} and {helper.label}. They worked together to solve the mystery.",
        ),
        QAItem(
            question="What was the mystery to solve?",
            answer=f"The mystery was finding {mystery.object_phrase}, which turned out to belong in the oblong slumber box.",
        ),
        QAItem(
            question="What helped the friends solve the puzzle?",
            answer=f"They used teamwork and a little lamp, which helped them spot the clues and finish the job.",
        ),
        QAItem(
            question="What did the oblong box turn out to be?",
            answer="It turned out to be a cozy place for pillows and a blanket, not a lost treasure after all.",
        ),
        QAItem(
            question="Why was the word liquor mentioned?",
            answer="A bottle labeled liquor was mentioned as a background detail on a shelf, but it was not part of the children's game.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share the work, help each other, and solve a problem together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing or unknown that people try to figure out.",
        ),
        QAItem(
            question="What does oblong mean?",
            answer="Oblong means longer than it is wide, like a stretched-out rectangle.",
        ),
        QAItem(
            question="What does slumber mean?",
            answer="Slumber means sleep, usually in a gentle or old-fashioned way.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str = "the library nook"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about teamwork and a mystery to solve.")
    ap.add_argument("--place", default=None, choices=["the library nook", "the playroom", "the attic corner"])
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
    return StoryParams(place=args.place or rng.choice(["the library nook", "the playroom", "the attic corner"]))


def generate(params: StoryParams) -> StorySample:
    world = build_world()
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
% A mystery is solvable when teamwork and searching both happen.
solvable_story :- teamwork, search.

teamwork :- helper.
search :- hero.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("hero"),
        asp.fact("helper"),
        asp.fact("oblong"),
        asp.fact("slumber"),
        asp.fact("liquor"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solvable_story/0."))
    return 0 if any(sym.name == "solvable_story" for sym in model) else 1


CURATED = [
    StoryParams(place="the library nook"),
    StoryParams(place="the playroom"),
    StoryParams(place="the attic corner"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show solvable_story/0."))
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
