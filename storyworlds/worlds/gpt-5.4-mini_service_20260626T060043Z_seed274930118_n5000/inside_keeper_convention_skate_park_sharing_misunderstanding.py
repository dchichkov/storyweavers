#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/inside_keeper_convention_skate_park_sharing_misunderstanding.py
===============================================================================================================

A small detective-story world set at a skate park, where an inside keeper
at a convention overhears a sharing misunderstanding and the team works
through clues to fix it.

The world is built from a compact causal simulation:
- people can want, hold, borrow, share, and notice things
- a misunderstanding can make someone think an item was taken
- teamwork can resolve the misunderstanding after clues are checked
- the ending image proves what changed in the world

The seed words are carried through the domain vocabulary:
inside, keeper, convention.

This script follows the Storyweavers world contract and includes:
- StoryParams
- registries
- build_parser
- resolve_params
- generate
- emit
- main
- inline ASP_RULES plus a Python reasonableness gate
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    inside: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the skate park"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    clue: str
    mess: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    protective: bool = False


@dataclass
class Crew:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "skate_park": Setting(place="the skate park", indoor=False, affords={"share_board", "search_case", "teamwork"}),
}

ACTIVITIES = {
    "share_board": Activity(
        id="share_board",
        verb="share the board",
        gerund="sharing the board",
        clue="the board was already lent to a friend",
        mess="confused",
        zone="ramp",
        keyword="sharing",
        tags={"sharing"},
    ),
    "search_case": Activity(
        id="search_case",
        verb="search for the missing case",
        gerund="following clues around the park",
        clue="the case was tucked beside the bench",
        mess="confused",
        zone="bench",
        keyword="misunderstanding",
        tags={"misunderstanding"},
    ),
    "teamwork": Activity(
        id="teamwork",
        verb="work together",
        gerund="working together",
        clue="the clues fit once everyone spoke calmly",
        mess="calm",
        zone="center",
        keyword="teamwork",
        tags={"teamwork"},
    ),
}

ITEMS = {
    "case": Item(
        id="case",
        label="skate case",
        phrase="a bright blue skate case",
        region="bench",
    ),
    "helmet": Item(
        id="helmet",
        label="helmet",
        phrase="a green helmet with a star sticker",
        region="head",
    ),
    "badge": Item(
        id="badge",
        label="keeper badge",
        phrase="a shiny keeper badge",
        region="torso",
        genders={"girl", "boy"},
    ),
}

CREWS = {
    "team": Crew(
        id="team",
        label="the team",
        prep="call everyone over and check the clues",
        tail="stood together and sorted the story out",
        helps={"share_board", "search_case", "teamwork"},
    )
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "June", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Max", "Eli", "Noah", "Theo", "Jack"]
TRAITS = ["curious", "careful", "brave", "bright", "gentle", "clever"]


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    keeper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def can_generate(activity: Activity, item: Item) -> bool:
    return activity.id in {"share_board", "search_case", "teamwork"} and item.id in {"case", "helmet", "badge"}


def explain_rejection(activity: Activity, item: Item) -> str:
    return f"(No story: {activity.verb} and {item.label} do not make a strong detective-style misunderstanding in this world.)"


def explain_gender(item_id: str, gender: str) -> str:
    allowed = " / ".join(sorted(ITEMS[item_id].genders))
    return f"(No story: this {ITEMS[item_id].label} does not fit {gender} here; try {allowed}.)"


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for item_id in ITEMS:
                act = ACTIVITIES[act_id]
                item = ITEMS[item_id]
                if can_generate(act, item):
                    if args.place is None or args.place == place:
                        if args.activity is None or args.activity == act_id:
                            if args.item is None or args.item == item_id:
                                if args.gender is None or args.gender in item.genders:
                                    combos.append((place, act_id, item_id))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        inside=False,
        meters={"calm": 0.0},
        memes={"curiosity": 1.0},
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=params.keeper,
        label="the keeper",
        inside=True,
        meters={"calm": 1.0},
    ))
    item = world.add(Entity(
        id="Item",
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=hero.id,
        inside=True,
    ))

    activity = ACTIVITIES[params.activity]
    crew = CREWS["team"]

    # Act 1: setup.
    world.say(
        f"{hero.id} was a {params.trait} child who loved the skate park. "
        f"At the inside window, the keeper watched the crowd and kept a neat list."
    )
    world.say(
        f"{hero.id} wore {item.phrase}, and everyone at the convention booth knew "
        f"that {item.label} mattered to the day's plans."
    )

    # Act 2: misunderstanding.
    world.para()
    world.say(
        f"One afternoon, {hero.id} tried to {activity.verb}, but a quick glance made "
        f"the keeper think the {item.label} was gone."
    )
    world.say(
        f"The keeper said, 'This looks wrong.' {hero.id} pointed to the bench, but "
        f"the words came out tangled and the misunderstanding grew."
    )

    hero.memes["confusion"] = 1.0
    keeper.memes["worry"] = 1.0
    world.facts["misunderstanding"] = True
    world.facts["activity"] = activity
    world.facts["item"] = item
    world.facts["keeper"] = keeper
    world.facts["hero"] = hero

    # Act 3: teamwork and resolution.
    world.para()
    world.say(
        f"Then the team heard the noise, and the keeper asked them to {crew.prep}."
    )
    world.say(
        f"They found the clue: {activity.clue}. Once everyone looked again, the truth was easy to see."
    )
    world.say(
        f"The keeper laughed softly, and {hero.id} shared the space by holding the {item.label} out for a turn."
    )
    world.say(
        f"{crew.tail}. By the end, {hero.id} was {activity.gerund}, the keeper was calm, and the convention booth felt friendly again."
    )
    hero.memes["joy"] = 1.0
    hero.memes["confusion"] = 0.0
    keeper.memes["worry"] = 0.0
    world.facts["resolved"] = True
    world.facts["crew"] = crew
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    item = f["item"]
    return [
        f'Write a short detective-story about {hero.id}, a keeper, and a {item.label} at the skate park, using the word "{activity.keyword}".',
        f"Tell a child-friendly mystery where a sharing misunderstanding at the skate park gets fixed by teamwork.",
        f"Write a story with an inside keeper at a convention booth where a child tries to {activity.verb} and everyone learns the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    activity = f["activity"]
    item = f["item"]
    crew = f["crew"]
    return [
        QAItem(
            question=f"Why did the keeper worry when {hero.id} tried to {activity.verb}?",
            answer=f"The keeper thought the {item.label} had been taken, but it was really just a misunderstanding.",
        ),
        QAItem(
            question=f"How did the team fix the problem at the skate park?",
            answer=f"The team worked together, checked the clues, and saw that {item.phrase} was still there.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} was {activity.gerund} again, and the keeper was calm because everyone shared the space kindly.",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{crew.label} helped solve it by looking closely and talking calmly.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it all to yourself.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing because they do not yet have the full story.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help each other reach the same goal.",
        )
    ],
    "inside": [
        QAItem(
            question="What does inside mean?",
            answer="Inside means being in a building or another place that has walls around you.",
        )
    ],
    "keeper": [
        QAItem(
            question="What does a keeper do?",
            answer="A keeper watches over a place or a thing and helps keep it safe and organized.",
        )
    ],
    "convention": [
        QAItem(
            question="What is a convention?",
            answer="A convention is a big meeting or event where people gather around a shared topic or interest.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({"sharing", "misunderstanding", "teamwork", "inside", "keeper", "convention"})
    out: list[QAItem] = []
    for tag in ["inside", "keeper", "convention", "sharing", "misunderstanding", "teamwork"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A combo is valid when the place affords the activity and the item fits the story.
valid_story(Place, Act, Item) :- affords(Place, Act), valid_item(Item), valid_act(Act).

% The detective story is especially about misunderstandings, sharing, and teamwork.
story_theme(Act) :- valid_act(Act), keyword(Act, sharing).
story_theme(Act) :- valid_act(Act), keyword(Act, misunderstanding).
story_theme(Act) :- valid_act(Act), keyword(Act, teamwork).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("valid_act", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("valid_item", iid))
        if item.plural:
            lines.append(asp.fact("plural_item", iid))
        for g in sorted(item.genders):
            lines.append(asp.fact("wears", g, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {
        (place, act, item)
        for place, setting in SETTINGS.items()
        for act in setting.affords
        for item in ITEMS
        if can_generate(ACTIVITIES[act], ITEMS[item])
    }
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-story world at a skate park with sharing, misunderstanding, and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.item:
        if not can_generate(ACTIVITIES[args.activity], ITEMS[args.item]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], ITEMS[args.item]))
    if args.gender and args.item and args.gender not in ITEMS[args.item].genders:
        raise StoryError(explain_gender(args.item, args.gender))

    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for item in ITEMS:
                if not can_generate(ACTIVITIES[act], ITEMS[item]):
                    continue
                if args.place is not None and args.place != place:
                    continue
                if args.activity is not None and args.activity != act:
                    continue
                if args.item is not None and args.item != item:
                    continue
                if args.gender is not None and args.gender not in ITEMS[item].genders:
                    continue
                combos.append((place, act, item))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, act, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(ITEMS[item].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper = args.keeper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, item=item, name=name, gender=gender, keeper=keeper, trait=trait)


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
        if e.inside:
            bits.append("inside=True")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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
    StoryParams(place="skate_park", activity="share_board", item="badge", name="Mia", gender="girl", keeper="mother", trait="curious"),
    StoryParams(place="skate_park", activity="search_case", item="case", name="Leo", gender="boy", keeper="father", trait="clever"),
    StoryParams(place="skate_park", activity="teamwork", item="helmet", name="Nora", gender="girl", keeper="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, act, item in stories:
            print(f"  {place:10} {act:13} {item}")
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
