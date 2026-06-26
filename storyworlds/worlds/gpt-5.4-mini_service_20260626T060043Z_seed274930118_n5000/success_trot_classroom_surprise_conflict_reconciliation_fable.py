#!/usr/bin/env python3
"""
storyworlds/worlds/success_trot_classroom_surprise_conflict_reconciliation_fable.py
===================================================================================

A tiny classroom fable world about a proud trot, a sudden surprise, a small
conflict, and a gentle reconciliation that ends in success.

Seed tale:
---
In a classroom, a small rabbit named Pip loved to trot to the front when it was
time to share stories. One day, the teacher placed a surprise gold star under
Pip's notebook and asked Pip to explain the class garden drawing. Pip trotted
up happily, but another pupil said the drawing should have been his. The room
grew tense until Pip offered to add the pupil's flower to the picture. The
teacher smiled, the class quieted, and Pip earned success by turning the
conflict into a shared win.

Design notes:
---
* The world uses typed entities with physical ``meters`` and emotional ``memes``.
* The prose is driven by state changes: surprise, conflict, reconciliation, and
  the final success image.
* The inline ASP twin mirrors the Python reasonableness gate.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the classroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_word: str = "class"
    value: str = "gold star"


@dataclass
class StoryParams:
    name: str
    species: str
    classmate: str
    teacher: str
    action: str
    surprise: str
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    rival = world.get("classmate")
    if hero.memes.get("hurt", 0) < THRESHOLD:
        return out
    if rival.memes.get("envy", 0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    out.append("The room turned tight with a small conflict.")
    return out


def _r_reconcile(world: World) -> list[str]:
    hero = world.get("hero")
    rival = world.get("classmate")
    teacher = world.get("teacher")
    if hero.memes.get("kindness", 0) < THRESHOLD:
        return []
    if hero.memes.get("conflict", 0) < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    rival.memes["joy"] = rival.memes.get("joy", 0) + 1
    teacher.memes["pride"] = teacher.memes.get("pride", 0) + 1
    return ["__reconcile__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_conflict, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__reconcile__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the classroom", affords={"trot", "share", "show_and_tell"})

ACTIONS = {
    "trot": Action(
        id="trot",
        verb="trot to the front",
        gerund="trotting to the front",
        rush="trot forward",
        keyword="trot",
        tags={"trot", "success"},
    ),
    "share": Action(
        id="share",
        verb="share the drawing",
        gerund="sharing the drawing",
        rush="reach out the paper",
        keyword="share",
        tags={"share", "kindness"},
    ),
    "show_and_tell": Action(
        id="show_and_tell",
        verb="show the class the picture",
        gerund="showing the class the picture",
        rush="hold up the page",
        keyword="show",
        tags={"show", "classroom"},
    ),
}

SURPRISES = {
    "star": Prize(label="star", phrase="a hidden gold star", type="star", owner_word="teacher", value="gold star"),
    "flower": Prize(label="flower", phrase="a little paper flower", type="flower", owner_word="classmate", value="paper flower"),
    "book": Prize(label="book", phrase="a bright reading book", type="book", owner_word="class", value="reading book"),
}

NAMES = ["Pip", "Mina", "Toby", "Luna", "Ned", "Iris"]
SPECIES = ["rabbit", "mouse", "fox", "goat", "duck"]
CLASSMATE_NAMES = ["Jun", "Sara", "Ben", "Kia", "Owen"]
TEACHER_NAMES = ["Ms. Reed", "Mr. Bell", "Mrs. Finch"]


def reasonableness_gate(action: Action, surprise: Prize) -> bool:
    return action.id in SETTING.affords and surprise.label in {"star", "flower", "book"}


def explain_rejection(action: Action, surprise: Prize) -> str:
    return f"(No story: the classroom can support {action.verb}, but not this surprise pairing.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A classroom fable about a trot, a surprise, a conflict, and reconciliation."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--classmate", choices=CLASSMATE_NAMES)
    ap.add_argument("--teacher", choices=TEACHER_NAMES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
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
    action = args.action or rng.choice(list(ACTIONS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    if not reasonableness_gate(ACTIONS[action], SURPRISES[surprise]):
        raise StoryError(explain_rejection(ACTIONS[action], SURPRISES[surprise]))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        species=args.species or rng.choice(SPECIES),
        classmate=args.classmate or rng.choice(CLASSMATE_NAMES),
        teacher=args.teacher or rng.choice(TEACHER_NAMES),
        action=action,
        surprise=surprise,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id="hero", kind="character", type=params.species, label=params.name,
        memes={"joy": 1.0, "curiosity": 1.0, "kindness": 0.0},
        meters={"energy": 1.0},
    ))
    classmate = world.add(Entity(
        id="classmate", kind="character", type="child", label=params.classmate,
        memes={"envy": 1.0, "curiosity": 1.0},
    ))
    teacher = world.add(Entity(
        id="teacher", kind="character", type="teacher", label=params.teacher,
        memes={"patience": 1.0, "pride": 0.0},
    ))
    prize = world.add(Entity(
        id="surprise", type="thing", label=SURPRISES[params.surprise].label,
        phrase=SURPRISES[params.surprise].phrase, owner=teacher.id,
    ))

    action = ACTIONS[params.action]

    # Act 1: setup
    world.say(f"In the classroom, {hero.label} the little {params.species} loved to {action.verb}.")
    world.say(f"{hero.label} believed a good day could begin with a brave {action.keyword}.")
    world.say(f"{teacher.label} watched with a smile, and {classmate.label} sat nearby with neat papers.")

    # Surprise
    world.para()
    world.say(
        f"Then came a surprise: {teacher.label} placed {prize.phrase} on the desk and asked "
        f"{hero.label} to {action.verb} first."
    )
    hero.memes["surprise"] = 1.0
    hero.memes["hope"] = 1.0
    hero.meters["interest"] = hero.meters.get("interest", 0.0) + 1.0
    world.say(f"{hero.label} felt a bright surprise and trotted up at once.")

    # Conflict
    world.para()
    hero.memes["hurt"] = 1.0
    classmate.memes["envy"] = 1.0
    world.say(
        f"But {classmate.label} frowned and said that the drawing, or the prize, should have been theirs."
    )
    world.say(f"{hero.label} held the page a little tighter, and the room fell into conflict.")
    propagate(world, narrate=True)

    # Reconciliation
    world.para()
    hero.memes["kindness"] = 1.0
    world.say(
        f"{hero.label} took a small breath, then offered to {ACTIONS['share'].verb} and add {classmate.label}'s flower."
    )
    world.say(
        f"{teacher.label} nodded, because a fable grows best when pride softens into sharing."
    )
    propagate(world, narrate=True)

    # Success
    world.para()
    hero.meters["success"] = 1.0
    hero.memes["success"] = 1.0
    world.say(
        f"In the end, {hero.label} trotted to the front with a calmer smile, and the class admired the finished picture."
    )
    world.say(
        f"The surprise had become a shared joy, the conflict had passed, and the reconciliation made the little success shine."
    )

    world.facts = {
        "hero": hero,
        "classmate": classmate,
        "teacher": teacher,
        "prize": prize,
        "action": action,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    action: Action = f["action"]
    return [
        f'Write a short classroom fable for children that includes the words "{action.keyword}", "surprise", and "success".',
        f"Tell a gentle story where {p.name} the {p.species} trots in a classroom, meets a surprise, has a conflict, and reaches reconciliation.",
        f"Write a fable set in a classroom about {p.name} learning that sharing can turn conflict into success.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    action: Action = f["action"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a little {p.species} who loves to {action.verb} in the classroom.",
        ),
        QAItem(
            question=f"What was the surprise in the classroom?",
            answer=f"The surprise was {SURPRISES[p.surprise].phrase}, which the teacher placed on the desk.",
        ),
        QAItem(
            question=f"How did the conflict get fixed?",
            answer=f"{p.name} chose to share and add {p.classmate}'s flower, so the class could move from conflict to reconciliation.",
        ),
        QAItem(
            question=f"What showed success at the end?",
            answer=f"Success showed up when {p.name} trotted to the front again and the class admired the finished picture together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a classroom?",
            answer="A classroom is a room where children learn, listen, and work together with a teacher.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people open their eyes wide or stop and look.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement so people can be kind to one another.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
setting(classroom).
affords(classroom,trot).
affords(classroom,share).
affords(classroom,show_and_tell).

action(trot).
action(share).
action(show_and_tell).

surprise(star).
surprise(flower).
surprise(book).

valid(A,S) :- affords(classroom,A), surprise(S).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "classroom"))
    for a in sorted(SETTING.affords):
        lines.append(asp.fact("affords", "classroom", a))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_pairs = set(asp.atoms(model, "valid"))
    py_pairs = {(a, s) for a in ACTIONS for s in SURPRISES if reasonableness_gate(ACTIONS[a], SURPRISES[s])}
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python gate ({len(py_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in clingo:", sorted(asp_pairs - py_pairs))
    print("only in python:", sorted(py_pairs - asp_pairs))
    return 1


CURATED = [
    StoryParams(name="Pip", species="rabbit", classmate="Jun", teacher="Ms. Reed", action="trot", surprise="star"),
    StoryParams(name="Mina", species="mouse", classmate="Sara", teacher="Mr. Bell", action="show_and_tell", surprise="flower"),
    StoryParams(name="Toby", species="goat", classmate="Kia", teacher="Mrs. Finch", action="share", surprise="book"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        pairs = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(pairs)} compatible action/surprise pairs:")
        for pair in pairs:
            print(" ", pair)
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
