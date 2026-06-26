#!/usr/bin/env python3
"""
piddle_bashful_conflict_sharing_happy_ending_detective.py
==========================================================

A tiny detective-story world about a bashful child, a puzzling piddle, a bit of
conflict, a kind act of sharing, and a happy ending.

The premise is classical and child-facing:
- someone notices a small, mysterious mess
- feelings wobble because the mess is embarrassing
- the detective style turns the problem into a clue hunt
- sharing a helpful item or idea resolves the conflict
- the ending proves the change with a concrete, cozy image
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


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    reveal: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    share_verb: str
    helps_with: set[str]
    covers: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    clue: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hall": Setting("the town hall", indoor=True),
    "library": Setting("the little library", indoor=True),
    "school": Setting("the school office", indoor=True),
    "station": Setting("the station house", indoor=True),
    "museum": Setting("the museum lobby", indoor=True),
}

CLUES = {
    "piddle": Clue(
        id="piddle",
        label="piddle",
        phrase="a tiny piddle on the floor",
        region="floor",
        mess="wet",
        reveal="a small wet trail",
        keyword="piddle",
    ),
    "muddy_shoes": Clue(
        id="muddy_shoes",
        label="muddy shoes",
        phrase="muddy shoes by the door",
        region="floor",
        mess="muddy",
        reveal="muddy footprints",
        keyword="muddy",
    ),
    "ink_drop": Clue(
        id="ink_drop",
        label="ink drop",
        phrase="an ink drop near the desk",
        region="desk",
        mess="inky",
        reveal="a dark blue spot",
        keyword="ink",
    ),
}

TOOLS = {
    "towel": Tool(
        id="towel",
        label="a soft towel",
        phrase="a soft towel",
        share_verb="share the towel",
        helps_with={"wet"},
        covers={"floor"},
    ),
    "mat": Tool(
        id="mat",
        label="a clean mat",
        phrase="a clean mat",
        share_verb="share the mat",
        helps_with={"muddy"},
        covers={"floor"},
    ),
    "napkins": Tool(
        id="napkins",
        label="some napkins",
        phrase="some napkins",
        share_verb="share the napkins",
        helps_with={"inky"},
        covers={"desk"},
        plural=True,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Ada", "Pia", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Milo", "Sam", "Theo", "Finn", "Max"]
TRAITS = ["bashful", "careful", "curious", "gentle", "quiet", "brave"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is troubling when it creates a visible mess in the chosen place.
troubling(C) :- clue(C), mess(C, _).

% Sharing is the compatible fix: a tool helps when it can address the mess.
helps(T, C) :- tool(T), clue(C), mess(C, M), helps_with(T, M), matches(T, C).

% A valid story needs a troubling clue and a helpful shared tool.
valid_story(S, C, T) :- setting(S), clue(C), tool(T), troubling(C), helps(T, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("mess", cid, c.mess))
        lines.append(asp.fact("matches", "towel", cid) if c.id == "piddle" else "")
        lines.append(asp.fact("matches", "mat", cid) if c.id == "muddy_shoes" else "")
        lines.append(asp.fact("matches", "napkins", cid) if c.id == "ink_drop" else "")
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tid, m))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", tid, r))
    return "\n".join([ln for ln in lines if ln])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue_id, clue in CLUES.items():
            for tool_id, tool in TOOLS.items():
                if clue.mess in tool.helps_with:
                    combos.append((place, clue_id, tool_id))
    return combos


def clue_needs_tool(clue: Clue, tool: Tool) -> bool:
    return clue.mess in tool.helps_with


def explain_rejection(clue: Clue, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not help with {clue.label}. "
        f"Pick a tool that can really fix the mess.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who liked to notice tiny things."
    )


def set_scene(world: World, hero: Entity, parent: Entity, clue: Clue) -> None:
    world.say(
        f"One quiet day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to "
        f"{world.setting.place}."
    )
    world.say(
        f"Near the middle of the room, {hero.id} spotted {clue.phrase}."
    )


def detect(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} looked like a tiny detective. {hero.pronoun('subject').capitalize()} followed "
        f"{clue.reveal} like a clue trail."
    )


def bashful_conflict(world: World, hero: Entity, parent: Entity, clue: Clue) -> None:
    hero.memes["bashful"] = hero.memes.get("bashful", 0.0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.say(
        f"{hero.id} felt bashful. {hero.pronoun('subject').capitalize()} did not want everyone to notice "
        f"the {clue.label}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} gave a calm look and said the mess could be solved."
    )


def share_tool(world: World, hero: Entity, parent: Entity, clue: Clue, tool_def: Tool) -> Entity:
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        owner=parent.id,
        protective=True,
        plural=tool_def.plural,
        covers=set(tool_def.covers),
    ))
    tool.worn_by = parent.id
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    world.say(
        f"Then {hero.id}'s {parent.label} said, 'We can {tool_def.share_verb}.'"
    )
    world.say(
        f"{hero.id} nodded and let {hero.pronoun('possessive')} {parent.label} use it right away."
    )
    return tool


def resolve(world: World, hero: Entity, parent: Entity, clue: Clue, tool: Tool) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["happy"] = hero.memes.get("happy", 0.0) + 1
    world.say(
        f"That helped at once. The room stayed neat, and the little mystery was not scary anymore."
    )
    world.say(
        f"In the end, {hero.id} smiled, {parent.label} smiled, and the {clue.label} had become just one more clue."
    )


def tell(setting: Setting, clue_def: Clue, tool_def: Tool, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=[trait, "bashful"],
        meters={},
        memes={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
        traits=["calm"],
    ))
    clue = world.add(Entity(
        id=clue_def.id,
        type="clue",
        label=clue_def.label,
        phrase=clue_def.phrase,
        region=clue_def.region,
    ))

    introduce(world, hero)
    set_scene(world, hero, parent, clue_def)
    detect(world, hero, clue_def)
    world.para()
    bashful_conflict(world, hero, parent, clue_def)
    tool = share_tool(world, hero, parent, clue_def, tool_def)
    world.para()
    resolve(world, hero, parent, clue_def, tool)
    world.facts.update(hero=hero, parent=parent, clue=clue_def, tool=tool_def, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    tool = f["tool"]
    return [
        f'Write a short detective story for a small child about a bashful child who finds a {clue.label}.',
        f"Tell a gentle mystery where {hero.id} feels bashful, there is a conflict over a {clue.label}, and someone shares {tool.label}.",
        f'Write a cozy detective tale that includes the word "{clue.keyword}" and ends happily after sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    tool = f["tool"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and the {clue.label}?",
            answer=f"It is a detective story about {hero.id}, who is {hero.traits[0]} and bashful, and about a small clue: {clue.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel conflict when the {clue.label} was found?",
            answer=f"{hero.id} felt bashful because the {clue.label} was a messy little problem, and {hero.pronoun('possessive')} {parent.label} had to help without making {hero.id} feel worse.",
        ),
        QAItem(
            question=f"What did they share to fix the problem?",
            answer=f"They shared {tool.label}. That helped with the {clue.label} because it could handle the {clue.mess} mess.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a happy ending: the mess was handled, the worry faded, and {hero.id} and {parent.label} both smiled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = f["clue"]
    tool = f["tool"]
    out: list[QAItem] = [
        QAItem(
            question="What is a detective story?",
            answer="A detective story is a story about noticing clues, asking questions, and figuring out what happened.",
        ),
    ]
    if clue.id == "piddle":
        out.append(QAItem(
            question="What is a piddle?",
            answer="A piddle is a tiny little puddle or wet spot, usually small enough to notice as a clue on the floor.",
        ))
    if tool.id == "towel":
        out.append(QAItem(
            question="What is a towel for?",
            answer="A towel can soak up water and help dry things off.",
        ))
    if tool.id == "mat":
        out.append(QAItem(
            question="What is a mat for?",
            answer="A mat helps keep a floor cleaner by catching dirt or wet shoes.",
        ))
    if tool.id == "napkins":
        out.append(QAItem(
            question="What are napkins for?",
            answer="Napkins are small papers or cloths used to wipe up little spills.",
        ))
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
# Params and generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(clue="piddle", tool="towel", name="Mia", gender="girl", parent="mother", trait="bashful"),
    StoryParams(clue="muddy_shoes", tool="mat", name="Ben", gender="boy", parent="father", trait="curious"),
    StoryParams(clue="ink_drop", tool="napkins", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.tool:
        clue = CLUES[args.clue]
        tool = TOOLS[args.tool]
        if not clue_needs_tool(clue, tool):
            raise StoryError(explain_rejection(clue, tool))
    combos = [
        c for c in valid_combos()
        if (args.clue is None or c[1] == args.clue)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, clue_id, tool_id = rng.choice(sorted(combos))
    clue = CLUES[clue_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        clue=clue_id,
        tool=tool_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS["hall"],
        CLUES[params.clue],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        parts = []
        if e.label:
            parts.append(f"label={e.label}")
        if e.phrase:
            parts.append(f"phrase={e.phrase}")
        if e.region:
            parts.append(f"region={e.region}")
        if e.covers:
            parts.append(f"covers={sorted(e.covers)}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective-story world about piddle, bashful feelings, sharing, and a happy ending."
    )
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, clue, tool) combos:\n")
        for setting, clue, tool in stories:
            print(f"  {setting:12} {clue:14} {tool}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
