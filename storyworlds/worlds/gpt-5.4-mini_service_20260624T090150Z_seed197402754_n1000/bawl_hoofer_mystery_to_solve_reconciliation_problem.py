#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a hoofer, a mystery to solve, and a
gentle reconciliation.

Premise:
- A child hears a loud bawl in a quiet barnyard.
- A small hoofer has lost something important.
- The child helps solve the mystery by following clues.
- The worried friends reconcile when the missing thing is found.

The world is intentionally tiny and constraint-checked: it simulates a few
physical facts and emotional shifts, then renders a complete short story.
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
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carriers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "father", "woman", "man"}:
            return {"subject": "she" if self.type in {"mother", "woman"} else "he",
                    "object": "her" if self.type in {"mother", "woman"} else "him",
                    "possessive": "her" if self.type in {"mother", "woman"} else "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the barnyard"
    quiet: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    solve_step: str
    fix: str
    resolved_image: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    parent_name: str
    hoofer_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barnyard": Setting(place="the barnyard", quiet=True,
                        clues=["a blue ribbon", "a little hoofprint", "a hayseed trail"]),
    "meadow": Setting(place="the meadow", quiet=True,
                      clues=["a bent fence pin", "a warm bell sound", "a clump of clover"]),
    "stable": Setting(place="the stable", quiet=True,
                      clues=["a shiny buckle", "a soft straw nest", "a dusty bucket"]),
}

MYSTERIES = {
    "missing_bell": Mystery(
        id="missing_bell",
        missing="tiny bell",
        clue="a little bell-shaped sparkle in the straw",
        solve_step="look under the hay",
        fix="hang the bell back on the hoofer's harness",
        resolved_image="the tiny bell jingling again in the moonlight",
    ),
    "lost_ribbon": Mystery(
        id="lost_ribbon",
        missing="blue ribbon",
        clue="a blue thread caught on a gate latch",
        solve_step="follow the ribbon thread",
        fix="tie the ribbon neatly around the hoofer's neck",
        resolved_image="the blue ribbon fluttering softly like a sleepy wave",
    ),
    "misplaced_lantern": Mystery(
        id="misplaced_lantern",
        missing="lantern",
        clue="a circle of warm light reflected in a water trough",
        solve_step="peek into the trough",
        fix="set the lantern on the stable shelf",
        resolved_image="the lantern glowing safe and warm on its shelf",
    ),
}

HOOFERS = [
    ("Pip", "small hoofer"),
    ("Moss", "gentle hoofer"),
    ("Toby", "sleepy hoofer"),
]

HERO_NAMES = ["Mina", "Luca", "Nora", "Finn", "Poppy", "Jules"]
PARENT_NAMES = ["Mama", "Papa", "Mom", "Dad", "Auntie", "Uncle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when the setting offers a clue and the missing thing.
solvable(S, M) :- setting(S), mystery(M), clue_in(S, M), missing_in(M).

% Reconciliation happens when the hero finds the missing thing and returns it.
reconciled(M) :- solvable(_, M), found(M), returned(M).

% A bedtime story ends happily when the hoofer is soothed and the problem is fixed.
happy_end(M) :- reconciled(M), soothed(M), fixed(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.quiet:
            lines.append(asp.fact("quiet", sid))
        for clue in setting.clues:
            lines.append(asp.fact("clue", sid, clue))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, mystery.missing))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program grounds and solves.")
    return 0


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def clue_for(mystery: Mystery) -> str:
    return mystery.clue


def solve_step_for(mystery: Mystery) -> str:
    return mystery.solve_step


def build_story_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="child", label=params.hero_name))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="parent", label=params.parent_name))
    hoofer = world.add(Entity(id=params.hoofer_name, kind="character", type="hoofer", label=params.hoofer_name))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=mystery.missing,
        label=mystery.missing,
        phrase=f"the {mystery.missing}",
        owner=hoofer.id,
    ))

    hero.memes["curious"] = 1.0
    hoofer.memes["worry"] = 1.0
    hoofer.memes["bawl"] = 1.0
    parent.memes["care"] = 1.0

    world.facts.update(
        hero=hero,
        parent=parent,
        hoofer=hoofer,
        missing=missing,
        mystery=mystery,
        clue=clue_for(mystery),
        solve_step=solve_step_for(mystery),
    )

    # Act 1
    world.say(
        f"At {setting.place}, {params.hero_name} was tucked in beside {params.parent_name} "
        f"when a soft bawl drifted from the dark barnyard."
    )
    world.say(
        f"It came from {params.hoofer_name}, a gentle hoofer who had lost {missing.phrase}."
    )

    # Act 2
    world.para()
    hero.memes["concern"] = 1.0
    world.say(
        f"{params.hero_name} listened carefully and chose to solve the mystery instead of feeling afraid."
    )
    world.say(
        f"They noticed {clue_for(mystery)}, so they decided to {solve_step_for(mystery)}."
    )

    # Simulated discovery
    world.para()
    found = False
    if params.mystery == "missing_bell":
        found = True
        world.say("Under the hay, there was the tiny bell, shining like a sleepy star.")
    elif params.mystery == "lost_ribbon":
        found = True
        world.say("By the gate, the blue thread led to the missing ribbon, tied around a post.")
    elif params.mystery == "misplaced_lantern":
        found = True
        world.say("In the water trough, the lantern's glow wobbled back at them from the dark water.")

    if not found:
        raise StoryError("The mystery could not be solved.")

    hero.memes["pride"] = 1.0
    hoofer.memes["worry"] = 0.2
    world.facts["found"] = True

    # Act 3
    world.para()
    world.say(
        f"{params.hero_name} brought {missing.phrase} back to {params.hoofer_name}, and the hoofer's"
        f" sad face softened into a grateful smile."
    )
    world.say(
        f"Together they made {mystery.fix}, and soon the night felt calm again."
    )
    world.say(
        f"By the end, {mystery.resolved_image} made the little barnyard feel cozy and safe."
    )

    hoofer.memes["peace"] = 1.0
    hero.memes["joy"] = 1.0
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story about {f['hero'].id} solving a mystery for {f['hoofer'].id} after hearing a bawl.",
        f"Tell a gentle story where a child helps a hoofer find {f['missing'].phrase} and everyone reconciles.",
        f"Write a small bedtime story with clues, problem solving, and a happy reconciliation in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    hoofer: Entity = f["hoofer"]
    mystery: Mystery = f["mystery"]
    missing: Entity = f["missing"]

    return [
        QAItem(
            question=f"Why did {hoofer.id} bawl in the barnyard?",
            answer=f"{hoofer.id} bawled because {hoofer.pronoun('possessive')} {missing.label} was missing, and that made {hoofer.pronoun('possessive')} heart feel worried.",
        ),
        QAItem(
            question=f"How did {hero.id} help solve the mystery?",
            answer=f"{hero.id} looked for the clue, followed the trail, and found the missing {mystery.missing}. That was the careful problem-solving part of the story.",
        ),
        QAItem(
            question=f"What changed when {hero.id} returned the missing thing to {hoofer.id}?",
            answer=f"{hoofer.id} stopped bawling, smiled again, and the two of them reconciled. The story ended with the missing thing safely back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something confusing or hidden that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people or friends stop being upset and come back together kindly.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a problem, thinking about clues, and choosing a sensible way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    out.append(f"facts={world.facts}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story mystery world about a child and a hoofer.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--hoofer-name")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    hoofer_name = args.hoofer_name or rng.choice([n for n, _ in HOOFERS])
    if hero_name == hoofer_name:
        raise StoryError("The child and hoofer need different names.")
    return StoryParams(place=place, mystery=mystery, hero_name=hero_name,
                       parent_name=parent_name, hoofer_name=hoofer_name)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show setting/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        seeds = [base_seed + i for i in range(len(SETTINGS) * len(MYSTERIES))]
        samples = []
        i = 0
        for place in SETTINGS:
            for mystery in MYSTERIES:
                p = StoryParams(
                    place=place,
                    mystery=mystery,
                    hero_name=HERO_NAMES[i % len(HERO_NAMES)],
                    parent_name=PARENT_NAMES[i % len(PARENT_NAMES)],
                    hoofer_name=HOOFERS[i % len(HOOFERS)][0],
                    seed=seeds[i],
                )
                samples.append(generate(p))
                i += 1
    else:
        samples = []
        seen = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 20):
            attempts += 1
            seed = base_seed + attempts
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
