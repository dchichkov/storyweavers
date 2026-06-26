#!/usr/bin/env python3
"""
nectar_teamwork_suspense_comedy.py
==================================

A small story world about a sweet mix-up with nectar, teamwork, suspense, and
a cheerful comic ending.

Premise:
- A child character loves a sweet treat or task involving nectar.
- Something goes wrong: a jar, feeder, or spoon is stuck, tipped, or nearly
  spills.
- Two helpers work together under a little suspense to fix it.
- The ending proves the nectar was saved and everyone is laughing.

The world model tracks:
- physical meters: sticky, spilled, balanced, muddy, full, dry
- emotional memes: worry, hope, giggles, pride, relief, cooperation
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
# Core world data
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["sticky", "spilled", "balanced", "dry", "full", "safe", "blocked"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "hope", "giggles", "pride", "relief", "cooperation", "suspense"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    danger: str
    suspense: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.teams: list[str] = []

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]

    def copy(self) -> "World":
        import copy

        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.story = list(self.story)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.teams = list(self.teams)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SCENES = {
    "garden": Scene(place="the garden", indoors=False, affords={"collect", "carry"}),
    "kitchen": Scene(place="the kitchen", indoors=True, affords={"mix", "carry"}),
    "porch": Scene(place="the porch", indoors=False, affords={"collect", "carry"}),
}

CHALLENGES = {
    "leaky-jar": Challenge(
        id="leaky-jar",
        verb="carry the nectar jar",
        gerund="carrying the nectar jar",
        danger="the jar might drip",
        suspense="a sticky drip trembled at the rim",
        mess="sticky",
        tags={"nectar", "sticky"},
    ),
    "high-hive": Challenge(
        id="high-hive",
        verb="reach the nectar pot",
        gerund="reaching the nectar pot",
        danger="the pot was just too high",
        suspense="the spoon was wobbling on the edge",
        mess="spilled",
        tags={"nectar", "suspense"},
    ),
    "floppy-lid": Challenge(
        id="floppy-lid",
        verb="open the nectar tin",
        gerund="opening the nectar tin",
        danger="the lid kept flopping shut",
        suspense="nobody knew if the lid would pop open or bonk a finger",
        mess="blocked",
        tags={"nectar", "comedy"},
    ),
}

TOOLS = [
    Tool(
        id="tray",
        label="a tray",
        phrase="a flat tray",
        helps={"sticky", "spilled"},
        covers={"steady"},
    ),
    Tool(
        id="cloth",
        label="a clean cloth",
        phrase="a soft clean cloth",
        helps={"sticky"},
        covers={"grip"},
    ),
    Tool(
        id="stepstool",
        label="a step stool",
        phrase="a wobbly little step stool",
        helps={"spilled", "blocked"},
        covers={"reach"},
    ),
    Tool(
        id="spoon",
        label="a long spoon",
        phrase="a long spoon with a bright handle",
        helps={"blocked"},
        covers={"reach"},
    ),
]

HERO_NAMES = ["Mia", "Noah", "Lena", "Pico", "Tali", "Finn", "June", "Rory"]
HELPER_NAMES = ["Ada", "Ollie", "Bea", "Milo", "Zuri", "Pip", "Nora", "Sami"]
TRAITS = ["cheerful", "curious", "silly", "careful", "bouncy", "bright"]


@dataclass
class StoryParams:
    scene: str
    challenge: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
at_risk(C) :- challenge(C), dangerous(C).
needs_teamwork(C) :- challenge(C), difficult(C).
valid_story(S, C, T) :- scene(S), challenge(C), tool(T), at_risk(C),
                        helps(T, M), mess(C, M), needs_teamwork(C).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("dangerous", cid))
        lines.append(asp.fact("difficult", cid))
        lines.append(asp.fact("mess", cid, ch.mess))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for m in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def challenge_requires_teamwork(ch: Challenge) -> bool:
    return True


def compatible_tool(ch: Challenge) -> Optional[Tool]:
    for tool in TOOLS:
        if ch.mess in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for scene_id in SCENES:
        scene = SCENES[scene_id]
        for ch_id, ch in CHALLENGES.items():
            if scene.indoors and ch_id == "high-hive":
                continue
            tool = compatible_tool(ch)
            if tool:
                out.append((scene_id, ch_id, tool.id))
    return out


def explain_rejection(scene_id: str, ch_id: str) -> str:
    scene = SCENES[scene_id]
    ch = CHALLENGES[ch_id]
    if scene.indoors and ch_id == "high-hive":
        return "(No story: the high-hive problem needs reaching up, but this indoor scene doesn't fit that kind of scramble.)"
    if not compatible_tool(ch):
        return "(No story: there is no tool in the catalog that sensibly solves that problem.)"
    return "(No story: that combination is not reasonable enough for this world.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _narrate(world: World, text: str) -> None:
    world.say(text)


def _apply_suspense(world: World, hero: Entity, helper: Entity, ch: Challenge) -> None:
    hero.memes["suspense"] += 1
    helper.memes["suspense"] += 1
    _narrate(world, f"{ch.suspense}. {hero.id} and {helper.id} paused and looked at each other like two busy squirrels at snack time.")


def _take_action(world: World, hero: Entity, helper: Entity, ch: Challenge, tool: Tool) -> None:
    hero.memes["cooperation"] += 1
    helper.memes["cooperation"] += 1
    if ch.mess == "sticky":
        hero.meters["sticky"] += 1
        helper.meters["sticky"] += 1
    elif ch.mess == "spilled":
        hero.meters["spilled"] += 1
    elif ch.mess == "blocked":
        hero.meters["blocked"] += 1
    _narrate(world, f"Together they used {tool.label} and fixed the problem in a very serious way, which was funny because they kept trying not to laugh.")


def tell(scene: Scene, ch: Challenge, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label=helper_name))

    hero.memes["hope"] += 1
    helper.memes["hope"] += 1

    world.say(f"{hero.id} was a {trait} child who loved nectar most of all.")
    world.say(f"{helper.id} was the kind of friend who showed up when a plan needed extra hands and a little courage.")
    world.say(f"One day in {scene.place}, {hero.id} wanted to {ch.verb}.")
    world.say(f"But {ch.danger}, so the whole thing felt a bit suspenseful.")

    world.para()
    _apply_suspense(world, hero, helper, ch)

    tool = compatible_tool(ch)
    if tool is None:
        raise StoryError("No sensible tool for this challenge.")
    world.facts["tool"] = tool

    world.say(f"Then {hero.id} and {helper.id} made a teamwork plan.")
    _take_action(world, hero, helper, ch, tool)

    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["giggles"] += 1
    helper.memes["giggles"] += 1
    world.para()
    world.say(f"In the end, the nectar stayed safe, the sticky trouble was solved, and both friends laughed so hard that even the quiet spoon seemed proud of itself.")

    world.facts.update(
        hero=hero,
        helper=helper,
        challenge=ch,
        scene=scene,
        tool=tool,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ch = f["challenge"]
    scene = f["scene"]
    return [
        f'Write a short comedy for a child named {hero.id} about nectar, teamwork, and a tricky moment in {scene.place}.',
        f"Tell a suspenseful but funny story where {hero.id} and {helper.id} work together to {ch.verb}.",
        f'Create a gentle story in which nectar causes a small problem, two friends cooperate, and the ending is cheerful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ch = f["challenge"]
    scene = f["scene"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {scene.place}?",
            answer=f"{hero.id} wanted to {ch.verb}, but the task looked tricky and a little suspenseful.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the nectar problem?",
            answer=f"{helper.id} helped {hero.id}, and they solved it together with teamwork.",
        ),
        QAItem(
            question=f"What tool helped them fix the problem?",
            answer=f"{tool.label} helped them, because it made the nectar trouble easier to handle.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the nectar safe, the problem solved, and both friends laughing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is nectar?",
            answer="Nectar is a sweet liquid made by flowers that bees and other animals may drink.",
        ),
        QAItem(
            question="Why is teamwork useful?",
            answer="Teamwork is useful because two or more helpers can share the work and solve a problem faster.",
        ),
        QAItem(
            question="Why can suspense make a story fun?",
            answer="Suspense makes a story fun because you wonder what will happen next before the surprise is revealed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny story world about nectar, teamwork, suspense, and comedy.")
    ap.add_argument("--scene", choices=SCENES.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.scene or args.challenge:
        combos = [
            c for c in combos
            if (args.scene is None or c[0] == args.scene)
            and (args.challenge is None or c[1] == args.challenge)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene_id, challenge_id, _ = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene=scene_id, challenge=challenge_id, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], CHALLENGES[params.challenge], params.name, params.helper, params.trait)
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


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    clingo_stories = set(asp_valid_stories())
    # Compare only the scene/challenge/tool triples from clingo's valid_story/3
    clingo = {(a, b, c) for (a, b, c) in clingo_stories}
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in python:", sorted(py - clingo))
    print("only in clingo:", sorted(clingo - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story combinations:")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "leaky-jar", "Mia", "Ada", "curious"),
            StoryParams("kitchen", "high-hive", "Noah", "Pip", "silly"),
            StoryParams("porch", "floppy-lid", "Lena", "Ollie", "cheerful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
