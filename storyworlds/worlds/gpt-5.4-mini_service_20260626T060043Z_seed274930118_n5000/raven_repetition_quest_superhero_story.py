#!/usr/bin/env python3
"""
raven_repetition_quest_superhero_story.py
=========================================

A small superhero storyworld about a hero, a raven, a quest, and a repeating
challenge. The world is intentionally tiny and constraint-checked: the quest
must be reasonable, the raven must be relevant, and the ending must show what
changed.

Premise:
- A young superhero is trying to complete a quest.
- A clever raven helps by repeating a clue or action.
- The hero must try the right approach more than once before the path opens.

The story is driven by simulated state:
- meters track physical state such as distance, items found, and barriers opened.
- memes track emotional state such as hope, doubt, and trust.

The core shape is:
1) setup with hero, raven, quest goal
2) tension with a repeating obstacle
3) turn where the raven's repetition reveals a pattern
4) resolution where the hero completes the quest
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
# Domain knobs
# ---------------------------------------------------------------------------

LOCATIONS = {
    "skybridge": "the skybridge",
    "rooftop": "the rooftop",
    "moonlot": "the moonlit lot",
    "clocktower": "the old clocktower",
}

QUESTS = {
    "lantern": {
        "goal": "recover the glowing lantern",
        "object": "glowing lantern",
        "reveal": "light",
        "trail": "light trail",
        "obstacle": "shifting shadows",
        "repeat": "tap the railing twice",
        "solution": "follow the rhythm",
    },
    "crown": {
        "goal": "find the silver crown",
        "object": "silver crown",
        "reveal": "sparkles",
        "trail": "sparkle trail",
        "obstacle": "locked doors",
        "repeat": "knock three times",
        "solution": "listen for the answer",
    },
    "map": {
        "goal": "bring back the star map",
        "object": "star map",
        "reveal": "ink",
        "trail": "ink marks",
        "obstacle": "blank walls",
        "repeat": "say the clue again",
        "solution": "notice the pattern",
    },
}

HERO_NAMES = ["Nova", "Mira", "Jett", "Ari", "Zoe", "Finn", "Luna", "Kai"]
RAVEN_NAMES = ["Midnight", "Echo", "Rook", "Onyx"]
VILLAIN_NAMES = ["Captain Hush", "Mister Mist", "Lady Loop", "General Gloom"]
TRAITS = ["brave", "quick", "kind", "bold", "clever"]

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "raven":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class QuestDef:
    id: str
    goal: str
    object: str
    reveal: str
    trail: str
    obstacle: str
    repeat: str
    solution: str


@dataclass
class StoryParams:
    location: str
    quest: str
    name: str
    gender: str
    trait: str
    raven_name: str
    villain: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: str, quest: QuestDef):
        self.location = location
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    quest = QuestDef(**QUESTS[params.quest])
    world = World(LOCATIONS[params.location], quest)

    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(
        id=params.name, kind="character", type=hero_type, label=params.name,
        meters={"distance": 0.0, "progress": 0.0},
        memes={"hope": 1.0, "trust": 0.0, "worry": 0.0},
    ))
    raven = world.add(Entity(
        id=params.raven_name, kind="raven", type="raven", label=params.raven_name,
        meters={"distance": 0.0},
        memes={"trust": 0.0, "mischief": 0.0},
    ))
    villain = world.add(Entity(
        id=params.villain, kind="character", type="villain", label=params.villain,
        meters={"barrier": 1.0},
        memes={"gloom": 1.0},
    ))
    prize = world.add(Entity(
        id="quest_item", type="artifact", label=quest.object, owner=params.name,
        meters={"hidden": 1.0, "found": 0.0},
    ))

    world.facts.update(hero=hero, raven=raven, villain=villain, prize=prize)
    return world


def _repeat_step(world: World, hero: Entity, raven: Entity, quest: QuestDef) -> None:
    sig = ("repeat", quest.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["worry"] += 1.0
    raven.memes["mischief"] += 1.0
    world.say(
        f"{hero.id} tried to solve the clue, but the path stayed closed. "
        f"{raven.id} hopped onto a post and called, “{quest.repeat}!”"
    )


def _pattern_step(world: World, hero: Entity, raven: Entity, quest: QuestDef) -> None:
    sig = ("pattern", quest.id)
    if sig in world.fired:
        return
    if hero.memes["worry"] < THRESHOLD:
        return
    world.fired.add(sig)
    hero.memes["trust"] += 1.0
    raven.memes["trust"] += 1.0
    world.say(
        f"{hero.id} listened carefully and noticed the repeat: every clue matched the "
        f"{quest.trail}. {raven.id} nodded as if that was the whole secret."
    )


def _open_path(world: World, hero: Entity, raven: Entity, prize: Entity, quest: QuestDef) -> None:
    sig = ("open", quest.id)
    if sig in world.fired:
        return
    if hero.memes["trust"] < THRESHOLD:
        return
    world.fired.add(sig)
    prize.meters["found"] = 1.0
    hero.meters["progress"] = 1.0
    world.say(
        f"Together they followed the {quest.trail} to the hidden place. "
        f"The {quest.obstacle} vanished, and {quest.goal} was finally within reach."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.facts["hero"]
    raven = world.facts["raven"]
    villain = world.facts["villain"]
    prize = world.facts["prize"]
    quest = world.quest

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} young superhero who loved to help people. "
        f"One evening, {hero.pronoun('subject')} set out to {quest.goal} at {world.location}."
    )
    world.say(
        f"Flying above the lanterns was a clever raven named {raven.id}, who seemed to know "
        f"where every secret path began."
    )
    world.para()

    # Act 2
    world.say(
        f"But {params.villain} had left behind {quest.obstacle}, and the way forward stayed shut."
    )
    _repeat_step(world, hero, raven, quest)
    world.say(
        f"{hero.id} tried once, then twice, but the barrier would not move. "
        f"{quest.solution.capitalize()}, the raven seemed to say with a sharp glance."
    )
    _pattern_step(world, hero, raven, quest)
    world.say(
        f"{villain.id} laughed from the shadows, hoping the quest would end there."
    )
    world.para()

    # Act 3
    _open_path(world, hero, raven, prize, quest)
    world.say(
        f"{hero.id} reached for the {prize.label}, and {raven.id} fluttered down beside "
        f"{hero.pronoun('object')} like a tiny black banner of victory."
    )
    world.say(
        f"In the end, the same clue that felt annoying at first became the key that saved the day."
    )

    world.facts.update(resolved=bool(prize.meters["found"] >= THRESHOLD))
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = world.quest
    return [
        f"Write a short superhero story for a child where {hero.id} and a raven complete a quest by noticing repetition.",
        f"Tell a gentle quest story at {world.location} where a raven repeats a clue and helps the hero solve {quest.goal}.",
        f"Write a kid-friendly superhero adventure that ends with {quest.object} being found after a repeated hint.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    raven = f["raven"]
    villain = f["villain"]
    prize = f["prize"]
    quest = world.quest

    return [
        QAItem(
            question=f"Who went on the quest at {world.location}?",
            answer=(
                f"{hero.id}, a {hero.memes and 'young superhero' or 'hero'}, went on the quest "
                f"with the raven named {raven.id}."
            ),
        ),
        QAItem(
            question=f"What made the quest hard at first?",
            answer=(
                f"The quest was hard because {villain.id} left behind {quest.obstacle}, so the path "
                f"would not open right away."
            ),
        ),
        QAItem(
            question=f"What did the raven repeat to help?",
            answer=(
                f"The raven repeated “{quest.repeat},” which helped {hero.id} notice the pattern."
            ),
        ),
        QAItem(
            question=f"What was the final prize of the story?",
            answer=(
                f"{hero.id} and {raven.id} finally found the {prize.label}, and the quest was complete."
            ),
        ),
        QAItem(
            question=f"How did the repeated clue help in the end?",
            answer=(
                f"After hearing the clue again, {hero.id} stopped guessing and followed the pattern, "
                f"which opened the way to the {prize.label}."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "raven": [
        QAItem(
            question="What is a raven?",
            answer="A raven is a large black bird that can be very smart and watch what is happening around it."
        ),
        QAItem(
            question="Can a raven help people by paying attention?",
            answer="Yes. A raven can watch carefully, notice patterns, and help someone find a clue."
        ),
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a special journey to find something, solve a problem, or help someone."
        )
    ],
    "repeat": [
        QAItem(
            question="Why can repeating a clue be helpful?",
            answer="Repeating a clue can help someone notice a pattern they missed the first time."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["raven"] + WORLD_KNOWLEDGE["quest"] + WORLD_KNOWLEDGE["repeat"]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_ok(L,Q) :- location(L), quest(Q), clue(Q), repeat_help(Q), not blocked(L,Q).
resolved(L,Q) :- quest_ok(L,Q).
#show quest_ok/2.
#show resolved/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("obstacle", qid, q["obstacle"]))
        lines.append(asp.fact("clue", qid))
        lines.append(asp.fact("repeat_help", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_ok/2.\n"))
    return sorted(set(asp.atoms(model, "quest_ok")))


def asp_verify() -> int:
    py = {(loc, q) for loc in LOCATIONS for q in QUESTS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} quest pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story parameters, selection, generation, CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: a raven, a quest, and a repeating clue.")
    ap.add_argument("--location", choices=LOCATIONS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--raven-name", choices=RAVEN_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
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
    location = args.location or rng.choice(list(LOCATIONS.keys()))
    quest = args.quest or rng.choice(list(QUESTS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    raven_name = args.raven_name or rng.choice(RAVEN_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(
        location=location,
        quest=quest,
        name=name,
        gender=gender,
        trait=trait,
        raven_name=raven_name,
        villain=villain,
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


CURATED = [
    StoryParams(location="clocktower", quest="lantern", name="Nova", gender="girl", trait="bold", raven_name="Echo", villain="Captain Hush"),
    StoryParams(location="rooftop", quest="map", name="Kai", gender="boy", trait="clever", raven_name="Rook", villain="Lady Loop"),
    StoryParams(location="skybridge", quest="crown", name="Luna", gender="girl", trait="brave", raven_name="Midnight", villain="General Gloom"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_ok/2.\n#show resolved/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible quest combos:\n")
        for loc, q in combos:
            print(f"  {loc:10} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
