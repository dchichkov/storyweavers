#!/usr/bin/env python3
"""
rhino_lemon_dumb_lesson_learned_quest_animal.py
================================================

A small animal-story world about a rhino, a lemon, and a silly mistake that
turns into a lesson learned.

Premise:
- A young rhino wants to go on a quest.
- The quest centers on a bright lemon that needs to be carried safely to a friend.
- The rhino starts off acting a little dumb: rushing, guessing, and ignoring help.
- Something goes wrong, the rhino learns a lesson, and the quest still ends
  well because the rhino chooses a smarter way.

This world is intentionally small and constraint-checked. It generates complete,
child-facing stories with a clear beginning, turn, and ending image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "stubborn": 0.0, "embarrassment": 0.0, "lesson": 0.0}


@dataclass
class Quest:
    goal: str
    risk: str
    safe_method: str
    lesson: str


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def quest_is_reasonable(quest: Quest) -> bool:
    return bool(quest.goal and quest.risk and quest.safe_method and quest.lesson)


def story_shape_ok(world: World) -> bool:
    f = world.facts
    return (
        f.get("setup", False)
        and f.get("problem", False)
        and f.get("turn", False)
        and f.get("resolution", False)
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "jungle": "the green jungle",
    "river": "the riverbank",
    "grove": "the sunny grove",
}

NAMES = ["Roo", "Nala", "Momo", "Tika", "Bibi", "Koko"]
FRIENDS = ["a mouse friend", "a small bird", "a turtle friend", "a squirrel friend"]

QUESTS = {
    "lemon_delivery": Quest(
        goal="bring a lemon to a friend",
        risk="the lemon could get squashed or dropped",
        safe_method="carry it gently in a leaf basket",
        lesson="it is smart to ask for help and use the right tool",
    ),
    "shiny_finding": Quest(
        goal="find a bright lemon for a picnic",
        risk="rushing could make the rhino miss the best fruit",
        safe_method="look carefully and walk slowly",
        lesson="slow eyes can find better things than fast feet",
    ),
    "juice_help": Quest(
        goal="take a lemon to a thirsty friend",
        risk="bumping into stones could bruise the lemon",
        safe_method="use a soft cloth wrap and a careful walk",
        lesson="gentle hands are better than silly guessing",
    ),
}

CURATED = [
    ("jungle", "lemon_delivery"),
    ("river", "juice_help"),
    ("grove", "shiny_finding"),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    friend: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    if not quest_is_reasonable(quest):
        raise StoryError("The quest is missing a clear goal, risk, or lesson.")

    world = World(setting=setting)
    rhino = world.add(Entity(
        id=params.name,
        kind="character",
        type="rhino",
        label="rhino",
        traits=["curious", "big-hearted", "dumb-at-first"],
        meters={"damage": 0.0, "tired": 0.0},
        memes={"joy": 0.0, "stubborn": 1.0, "embarrassment": 0.0, "lesson": 0.0},
    ))
    lemon = world.add(Entity(
        id="lemon",
        type="lemon",
        label="lemon",
        phrase="a bright yellow lemon",
        owner=rhino.id,
        meters={"damage": 0.0, "tired": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="friend",
        label=params.friend,
        traits=["patient", "kind"],
    ))

    # Act 1
    world.say(f"{rhino.id} was a small rhino who loved adventures in {setting}.")
    world.say(f"One day, {rhino.id} got a quest: {quest.goal}.")
    world.say(f"{rhino.id} found {lemon.phrase} and wanted to hurry off right away.")
    world.facts["setup"] = True

    # Act 2
    world.para()
    world.say(f"But the quest was not so simple, because {quest.risk}.")
    world.say(f"{rhino.id} acted a little dumb and tried to carry the lemon in its trunk without thinking.")
    world.facts["problem"] = True
    rhino.memes["stubborn"] += 1.0
    rhino.memes["embarrassment"] += 1.0

    # The mistake: the lemon gets at risk.
    lemon.meters["damage"] += 1.0
    world.say("The lemon rolled, bumped a stone, and got a little squished.")
    world.say(f"{params.friend} watched patiently and pointed at a better plan.")
    world.facts["turn"] = True

    # Act 3
    world.para()
    world.say(f"{rhino.id} stopped, took a breath, and learned a lesson.")
    world.say(f"So {rhino.id} used {quest.safe_method} and walked carefully.")
    world.say(f"At last, {rhino.id} delivered the lemon to {params.friend} with a proud smile.")
    rhino.memes["joy"] += 1.0
    rhino.memes["lesson"] += 1.0
    world.facts["resolution"] = True

    world.facts.update(
        rhino=rhino,
        lemon=lemon,
        friend=friend,
        quest=quest,
        setting_name=params.setting,
    )
    return world


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    prompts = [
        f"Write a gentle animal story about a rhino on a quest involving a lemon.",
        f"Tell a short story where a rhino starts off a little dumb, makes a mistake, and learns a lesson.",
        f"Write a child-friendly quest story with a rhino, a lemon, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {params.name}, a rhino who went on a quest with a lemon.",
        ),
        QAItem(
            question=f"What went wrong when {params.name} hurried?",
            answer=f"{params.name} acted a little dumb, carried the lemon the wrong way, and the lemon got squished.",
        ),
        QAItem(
            question=f"What lesson did {params.name} learn?",
            answer=f"{params.name} learned that it is smart to ask for help and use the right tool.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a lemon like?",
            answer="A lemon is a bright yellow fruit with a sour taste.",
        ),
        QAItem(
            question="What does a quest mean?",
            answer="A quest is a special journey to reach a goal or solve a problem.",
        ),
        QAItem(
            question="Why should someone carry something fragile carefully?",
            answer="Because bumping or dropping it can damage it, and gentle hands help keep it safe.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is valid when it has a goal, a risk, a safer method, and a lesson.
valid_quest(Q) :- quest(Q), goal(Q,_), risk(Q,_), safe_method(Q,_), lesson(Q,_).

% A story is valid when the rhino, lemon, and lesson are all present.
valid_story(S) :- story(S), has_rhino(S), has_lemon(S), has_lesson(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_name", sid, setting))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("risk", qid, q.risk))
        lines.append(asp.fact("safe_method", qid, q.safe_method))
        lines.append(asp.fact("lesson", qid, q.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_quest/1.")
    model = asp.one_model(program)
    asp_valid = sorted(set(asp.atoms(model, "valid_quest")))
    py_valid = [(qid,) for qid in QUESTS if quest_is_reasonable(QUESTS[qid])]
    if asp_valid != py_valid:
        print("MISMATCH between ASP and Python reasoning.")
        print("ASP:", asp_valid)
        print("PY :", py_valid)
        return 1
    for setting, qid in CURATED:
        params = StoryParams(setting=setting, quest=qid, name="Roo", friend="a mouse friend")
        sample = generate_story(params)
        if not sample.story or not story_shape_ok(sample.world):
            print("Story verification failed.")
            return 1
    print(f"OK: ASP and Python agree; verified {len(CURATED)} sample stories.")
    return 0


# ---------------------------------------------------------------------------
# Parameters / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a rhino, a lemon, and a lesson learned.",
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(setting=setting, quest=quest, name=name, friend=friend)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting}")
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_quest/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_quest/1."))
        vals = sorted(set(asp.atoms(model, "valid_quest")))
        print(f"{len(vals)} valid quests:")
        for (qid,) in vals:
            print(f"  {qid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (setting, quest) in enumerate(CURATED):
            params = StoryParams(
                setting=setting,
                quest=quest,
                name=NAMES[i % len(NAMES)],
                friend=FRIENDS[i % len(FRIENDS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
