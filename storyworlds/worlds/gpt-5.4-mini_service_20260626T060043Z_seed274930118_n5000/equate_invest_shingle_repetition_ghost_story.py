#!/usr/bin/env python3
"""
storyworlds/worlds/equate_invest_shingle_repetition_ghost_story.py
===================================================================

A small ghost-story world about a child, a repeated clue, and a roof shingle
that keeps the house awake.

Premise:
- A child hears a ghost repeat three words in the dark.
- The repeated clue points to a loose shingle above the room.
- The child learns to equate the ghost's tapping with a roof problem.
- A grown-up invests money and effort to fix the shingle.
- The ghost grows gentle once the house is safe again.

This world uses a simple state model with meters and memes:
- meters: fear, leak, coins, repair, rustle
- memes: curiosity, courage, relief, patience, haunting

The story is deliberately compact and child-facing, but it is state-driven:
the repeated ghost signal, the learned equation, and the repair all change the
world before the ending image appears.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, name: str) -> float:
        return self.meters.get(name, 0.0)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    room: str = "the attic"


@dataclass
class Clue:
    word1: str
    word2: str
    word3: str
    repeat_count: int
    echo: str
    description: str


@dataclass
class RepairPlan:
    cost: int
    action: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    grownup: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "old_house": Setting(place="the old house", room="the attic"),
    "cottage": Setting(place="the little cottage", room="the upstairs hall"),
    "mansion": Setting(place="the quiet mansion", room="the narrow stair"),
}

CLUES = {
    "equate": Clue(
        word1="equate",
        word2="invest",
        word3="shingle",
        repeat_count=3,
        echo="equate, invest, shingle",
        description="the ghost keeps repeating three careful words",
    ),
    "invest": Clue(
        word1="invest",
        word2="equate",
        word3="shingle",
        repeat_count=3,
        echo="invest, equate, shingle",
        description="the ghost repeats a clue about money and a roof",
    ),
    "shingle": Clue(
        word1="shingle",
        word2="equate",
        word3="invest",
        repeat_count=3,
        echo="shingle, equate, invest",
        description="the ghost repeats a clue about the roof tile first",
    ),
}

REPAIR = RepairPlan(
    cost=3,
    action="put fresh nails into the loose shingle",
    ending="Soon the roof was steady, the drip stopped, and the house felt warm again.",
)

GIRL_NAMES = ["Mina", "Ivy", "Tara", "Lena", "Nora", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Theo", "Max"]


def _ghost_repeats(world: World, ghost: Entity, clue: Clue) -> None:
    ghost.memes["haunting"] += 1
    world.say(
        f"At night, a small ghost drifted by the dark window and said, "
        f'"{clue.echo}."'
    )
    world.say(
        f"It said the same three words again and again: {clue.echo}, {clue.echo}, {clue.echo}."
    )


def _child_listens(world: World, child: Entity, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    child.meters["fear"] += 1
    world.say(
        f"{child.id} sat very still and listened. "
        f"{child.pronoun().capitalize()} felt spooky, but {child.pronoun()} also wondered why the ghost kept repeating the same thing."
    )


def _equate_clue(world: World, child: Entity, ghost: Entity, shingle: Entity, clue: Clue) -> None:
    if ("equate", child.id) in world.fired:
        return
    world.fired.add(("equate", child.id))
    child.memes["courage"] += 1
    world.say(
        f"Then {child.id} learned to equate the clue with the problem above the room: "
        f"the tapping sound matched the loose shingle."
    )
    world.say(
        f"The ghost had not come to frighten anyone; it had come to point at the shingle."
    )
    shingle.meters["loose"] = 1.0
    world.facts["clue_echo"] = clue.echo


def _invest_money(world: World, grownup: Entity, child: Entity, shingle: Entity) -> None:
    if world.get("jar").meters["coins"] < THRESHOLD:
        return
    if ("invest", grownup.id) in world.fired:
        return
    world.fired.add(("invest", grownup.id))
    world.get("jar").meters["coins"] -= 3
    world.get("repair").meters["work"] += 1
    shingle.meters["loose"] = 0.0
    shingle.meters["fixed"] = 1.0
    grownup.memes["patience"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{grownup.id} smiled, took the repair money from the jar, and invested it in a real fix."
    )
    world.say(
        f"{grownup.id} hired help to {REPAIR.action}."
    )


def _quiet_ghost(world: World, ghost: Entity, child: Entity, shingle: Entity) -> None:
    if shingle.meters.get("fixed", 0.0) < THRESHOLD:
        return
    if ("quiet", ghost.id) in world.fired:
        return
    world.fired.add(("quiet", ghost.id))
    ghost.memes["haunting"] = 0.0
    child.meters["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"When the shingle stopped rattling, the ghost gave one soft wave and grew calm."
    )
    world.say(
        f"It was not a mean ghost at all. It had only wanted the house to be safe."
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        if world.get("ghost").memes.get("haunting", 0.0) >= THRESHOLD and world.facts.get("echoed") is False:
            world.facts["echoed"] = True
            changed = True
        if world.facts.get("echoed") and world.facts.get("equated") is False:
            world.facts["equated"] = True
            changed = True
        if world.get("jar").meters.get("coins", 0.0) >= 3 and world.facts.get("invested") is False:
            world.facts["invested"] = True
            changed = True
        if world.get("shingle").meters.get("fixed", 0.0) >= THRESHOLD and world.facts.get("quiet") is False:
            world.facts["quiet"] = True
            changed = True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={"fear": 0.0},
        memes={"curiosity": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    grownup = world.add(Entity(
        id=params.grownup,
        kind="character",
        type="adult",
        meters={"money": 3.0},
        memes={"patience": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        meters={},
        memes={"haunting": 1.0},
    ))
    shingle = world.add(Entity(
        id="shingle",
        type="roof_shingle",
        label="loose shingle",
        meters={"loose": 1.0, "fixed": 0.0},
    ))
    jar = world.add(Entity(
        id="jar",
        type="jar",
        label="repair jar",
        meters={"coins": 3.0},
    ))
    repair = world.add(Entity(
        id="repair",
        type="work",
        label="repair work",
        meters={"work": 0.0},
    ))

    clue = CLUES[params.clue]

    world.say(
        f"In {setting.place}, a child named {child.id} lived under a roof that sometimes whispered at night."
    )
    world.say(
        f"One night, {child.id} heard a ghost in {setting.room}."
    )
    _ghost_repeats(world, ghost, clue)

    world.para()
    _child_listens(world, child, clue)
    world.say(
        f"The repeating words sounded spooky at first, but they also sounded like a message."
    )

    world.para()
    _equate_clue(world, child, ghost, shingle, clue)
    world.say(
        f"{child.id} pointed up and said the sound was not a curse. It was a clue about {shingle.label}."
    )

    world.para()
    _invest_money(world, grownup, child, shingle)
    if shingle.meters.get("fixed", 0.0) >= THRESHOLD:
        world.say(REPAIR.ending)

    world.para()
    _quiet_ghost(world, ghost, child, shingle)
    world.say(
        f"In the last dark hour, the house was still. {child.id} could sleep without listening for the tap-tap-tap."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        ghost=ghost,
        shingle=shingle,
        jar=jar,
        repair=repair,
        clue=clue,
        setting=setting,
        resolved=shingle.meters.get("fixed", 0.0) >= THRESHOLD,
    )
    return world


def format_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    return [
        f'Write a short ghost story for a young child that repeats "{clue.echo}" three times.',
        f"Tell a gentle haunted-house story where {child.id} learns to equate a ghost's clue with a loose shingle.",
        f"Write a spooky-but-soft story about a ghost, a repair jar, and the word {clue.word1}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    grownup: Entity = f["grownup"]
    ghost: Entity = f["ghost"]
    shingle: Entity = f["shingle"]
    clue: Clue = f["clue"]
    qa = [
        QAItem(
            question=f"What did the ghost keep repeating in the story?",
            answer=f"The ghost kept repeating {clue.echo}. It said the same three words again and again because it was trying to point at the roof problem.",
        ),
        QAItem(
            question=f"What did {child.id} learn to equate the ghost's clue with?",
            answer=f"{child.id} learned to equate the tapping clue with a loose shingle above the room.",
        ),
        QAItem(
            question=f"What did {grownup.id} do with the money from the repair jar?",
            answer=f"{grownup.id} invested it in repair work and fixed the loose shingle.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end after the shingle was fixed?",
                answer=f"The roof became steady, the drip stopped, and the ghost grew calm instead of spooky.",
            )
        )
    return qa


KNOWLEDGE = {
    "ghost": (
        "What is a ghost in a story?",
        "A ghost in a story is often a spooky character that can float, whisper, or rattle things.",
    ),
    "shingle": (
        "What is a shingle?",
        "A shingle is one of the flat pieces that cover a roof and help keep rain out.",
    ),
    "repair": (
        "Why do people fix a loose roof shingle?",
        "People fix a loose roof shingle so water does not leak into the house.",
    ),
    "equate": (
        "What does it mean to equate two things?",
        "To equate two things means to see that they match or go together in an important way.",
    ),
    "invest": (
        "What does it mean to invest money?",
        "To invest money means to spend it carefully on something useful that will help later.",
    ),
    "repeat": (
        "Why do stories sometimes repeat words?",
        "Stories repeat words to make them easy to remember, to build suspense, or to show that a message matters.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a)
        for key in ["ghost", "shingle", "repair", "equate", "invest", "repeat"]
        for q, a in [KNOWLEDGE[key]]
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if bits:
            lines.append(f"  {e.id} ({e.type}): {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the ghost story needs a loose shingle, a repeated clue, and enough money to repair it.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with repetition, a clue, and a shingle.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--clue", choices=CLUES.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    clue = args.clue or rng.choice(list(CLUES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(place=place, child_name=name, child_gender=gender, grownup=grownup, clue=clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=format_story_text(world),
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
% A story is reasonable when there is a repeated clue, a loose shingle, and a repair outcome.
clued(C) :- clue(C).
repeated(C) :- repeats(C,N), N >= 3.
problem(shingle) :- loose(shingle).
fixable(shingle) :- money(jar,3), repair_action(shingle).
valid_story(P,C) :- place(P), clued(C), repeated(C), problem(shingle), fixable(shingle).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeats", cid, clue.repeat_count))
    lines.append(asp.fact("loose", "shingle"))
    lines.append(asp.fact("money", "jar", 3))
    lines.append(asp.fact("repair_action", "shingle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, c) for p in SETTINGS for c in CLUES)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} candidates).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(place="old_house", child_name="Mina", child_gender="girl", grownup="mother", clue="equate"),
    StoryParams(place="cottage", child_name="Eli", child_gender="boy", grownup="father", clue="invest"),
    StoryParams(place="mansion", child_name="Nora", child_gender="girl", grownup="mother", clue="shingle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
