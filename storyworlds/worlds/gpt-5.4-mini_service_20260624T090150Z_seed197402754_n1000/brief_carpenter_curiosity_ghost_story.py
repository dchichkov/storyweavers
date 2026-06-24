#!/usr/bin/env python3
"""
brief_carpenter_curiosity_ghost_story.py
=======================================

A compact, child-facing story world with a ghost-story mood:
a carpenter, a brief note, and curiosity leading to a gentle reveal.

A tiny source tale used to build the world model:
---
One evening, a carpenter named Nora found a brief note on her workbench. It said,
"Come upstairs and listen." Nora felt curious, but the old house was whispery and
still. She followed the creak of the stairs to the attic, where a shy ghost had
been tapping on a loose board all week.

The ghost was not scary at all. It only wanted help making the floor stop squeaking.
Nora smiled, fetched her hammer, and fixed the board. The ghost thanked her by
making the lantern glow soft and gold. Nora went back down with a calm heart, and
the house felt friendly from then on.
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
# World entities
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"woman", "girl", "mother", "mom", "carpenter"}
        masculine = {"man", "boy", "father", "dad"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    is_old_house: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    trigger: str
    clue: str
    sound: str
    reveal: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story_bits: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "workshop": Setting(place="the old workshop", indoors=True, affords={"note", "attic"}),
    "house": Setting(place="the old house", indoors=True, affords={"note", "attic"}),
    "attic": Setting(place="the attic", indoors=True, affords={"note", "attic"}),
}

MYSTERIES = {
    "brief_note": Mystery(
        id="brief_note",
        trigger="note",
        clue="a brief note",
        sound="a soft scratch of paper",
        reveal="a shy ghost was asking for help",
        mood="curious",
        tags={"brief", "curiosity", "ghost"},
    ),
    "loose_board": Mystery(
        id="loose_board",
        trigger="attic",
        clue="a loose board",
        sound="a little creak in the floor",
        reveal="the ghost wanted the squeak to stop",
        mood="spooky",
        tags={"ghost", "carpenter"},
    ),
}

TOOLS = {
    "hammer": Tool(
        id="hammer",
        label="hammer",
        phrase="a small hammer",
        helps_with={"attic"},
        action="tap the board straight",
        tags={"carpenter"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a warm lantern",
        helps_with={"ghost"},
        action="make the attic glow softly",
        tags={"ghost"},
    ),
    "briefcase": Tool(
        id="briefcase",
        label="briefcase",
        phrase="a little briefcase",
        helps_with={"note"},
        action="carry the brief note safely",
        tags={"brief"},
    ),
}

CURIOUS_TRAITS = ["curious", "quietly curious", "gentle", "brave", "patient"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    name: str
    role: str = "carpenter"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for t in TOOLS:
                if _compatible(m, t):
                    combos.append((s, m, t))
    return combos


def _compatible(mystery_id: str, tool_id: str) -> bool:
    m = MYSTERIES[mystery_id]
    t = TOOLS[tool_id]
    return bool(m.trigger in t.helps_with or m.id.split("_")[0] in t.tags or m.tags & t.tags)


def reason_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not reasonably help with {mystery.clue}. "
        f"Pick a tool that fits the brief note or the attic mystery.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery, tool = f["hero"], f["mystery"], f["tool"]
    return [
        f'Write a short ghost story for a small child about a {hero.type} named {hero.id}, '
        f'a {mystery.clue}, and a gentle surprise.',
        f'Tell a brief, cozy story where {hero.id} the {hero.type} feels {hero.memes.get("curiosity", 0):.0f} curious and uses {tool.label} in a spooky old house.',
        f'Write a child-friendly story using the word "brief" and ending with a calm, friendly ghost.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    setting: Setting = f["setting"]

    qa = [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=(
                f"It is about {hero.id}, a {hero.type} who works in {setting.place}, "
                f"and a shy ghost who leaves a brief note."
            ),
        ),
        QAItem(
            question=f"What did the brief note ask for?",
            answer=(
                f"The brief note asked someone to come listen and look upstairs, "
                f"because the ghost needed help with {mystery.reveal}."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} go to the attic?",
            answer=(
                f"{hero.id} felt curious after reading the note, so {hero.pronoun()} went to the attic "
                f"to find out what was making the little creak."
            ),
        ),
        QAItem(
            question=f"What tool did {hero.id} use to help?",
            answer=(
                f"{hero.id} used {tool.phrase} to {tool.action}, which helped the ghost feel safe."
            ),
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=(
                f"The house felt friendly, the ghost was no longer lonely, and {hero.id} went downstairs "
                f"with a calm heart."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carpenter?",
            answer="A carpenter is a person who builds and fixes things made of wood, like boards, doors, and shelves.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more and go see what is happening.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky-looking person or shape from make-believe, but it can be kind or lonely too.",
        ),
        QAItem(
            question="What is a brief note?",
            answer="A brief note is a very short message written on paper.",
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
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(S, M, T) :- setting(S), mystery(M), tool(T),
                       trigger(M, Tr), helps(T, Tr).

valid_story(S, M, T) :- compatible(S, M, T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("trigger", mid, m.trigger))
        for tag in sorted(m.tags):
            lines.append(asp.fact("mystery_tag", mid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _say(world: World, text: str) -> None:
    world.say(text)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.role, traits=[params.trait]))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="a shy ghost"))

    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]

    hero.memes["curiosity"] = 1
    ghost.memes["loneliness"] = 1

    # Act 1
    _say(world, f"{hero.id} was a {params.trait} {params.role} who worked in {setting.place}.")
    _say(world, f"One evening, {hero.id} found {mystery.clue} on the workbench.")
    _say(world, f"It was a {mystery.trigger} with {mystery.sound} behind it.")
    world.para()
    _say(world, f"{hero.id} felt curiosity tugging at {hero.pronoun('possessive')} sleeve.")
    _say(world, f"Even though the house was quiet and a little spooky, {hero.id} followed the clue.")

    # Act 2
    world.para()
    _say(world, f"Upstairs, the attic answered with {mystery.sound}.")
    hero.memes["curiosity"] += 1
    if tool.id == "hammer":
        _say(world, f"{hero.id} picked up {tool.phrase} and listened to the loose board.")
    elif tool.id == "lantern":
        _say(world, f"{hero.id} lit {tool.phrase} so the dark corners would not feel lonely.")
    else:
        _say(world, f"{hero.id} carried {tool.phrase} carefully so the note would not bend.")
    _say(world, f"Then the ghost appeared, not scary at all, only soft as a pillow shadow.")

    # Act 3
    world.para()
    if tool.id == "hammer":
        _say(world, f"The ghost pointed to the squeaky floor and asked for help.")
        _say(world, f"{hero.id} used {tool.phrase} to tap the board straight.")
    elif tool.id == "lantern":
        _say(world, f"The ghost shivered, so {hero.id} held up {tool.phrase} and spoke kindly.")
        _say(world, f"The warm light made the attic glow softly while the ghost explained the problem.")
    else:
        _say(world, f"{hero.id} opened the little briefcase and found the note safe inside.")
        _say(world, f"The ghost smiled, because the note had reached the right person.")
    _say(world, f"The ghost thanked {hero.id} and made the lantern glow soft and gold.")
    _say(world, f"{hero.id} went back downstairs with a calm heart, and the old house felt friendly.")

    world.facts = {
        "hero": hero,
        "ghost": ghost,
        "mystery": mystery,
        "tool": tool,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with a carpenter and a brief note.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["carpenter"], default="carpenter")
    ap.add_argument("--trait", choices=CURIOUS_TRAITS)
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
    if args.mystery and args.tool:
        if not _compatible(args.mystery, args.tool):
            raise StoryError(reason_rejection(MYSTERIES[args.mystery], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Nora", "Ivy", "Mina", "Ada", "Lena"])
    trait = args.trait or rng.choice(CURIOUS_TRAITS)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, name=name, trait=trait, role=args.role)


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, memes={dict(e.memes)}, meters={dict(e.meters)}")
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, tool) combos:\n")
        for s, m, t in combos:
            print(f"  {s:10} {m:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(setting="workshop", mystery="brief_note", tool="briefcase", name="Nora", trait="curious"),
        StoryParams(setting="house", mystery="loose_board", tool="hammer", name="Ivy", trait="quietly curious"),
        StoryParams(setting="attic", mystery="loose_board", tool="lantern", name="Mina", trait="gentle"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} with {p.tool} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
