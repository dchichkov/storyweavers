#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/knick_mistake_problem_solving_lesson_learned_detective.py
===============================================================================================================

A compact detective-style storyworld about a small mistake, careful problem
solving, and a lesson learned.

Seed-tale premise:
---
Knick was a young detective who loved solving little mysteries. One morning, a
tiny bell went missing from the club room. Knick found a muddy smudge and made
a mistake by blaming the janitor right away. Then Knick slowed down, checked
the room, and followed the clue trail. The missing bell turned up inside a
paper box that had been knocked behind the shelf. Knick apologized, fixed the
mix-up, and learned to look twice before guessing.

This world keeps the story grounded in:
- physical meters: clues, mess, order, repair
- emotional memes: worry, embarrassment, relief, trust

The story arc is always:
1) setup with a detective and a small problem
2) a mistaken guess that creates tension
3) active problem solving with real clues
4) a lesson learned and a tidy ending image
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
# Core world constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

CLUE_KINDS = {"dust", "mud", "scratch", "paper", "tape"}
EMOTION_KEYS = {"worry", "trust", "embarrassment", "relief", "pride", "curiosity"}

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the detective club room"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    item_label: str
    item_phrase: str
    culprit_kind: str
    culprit_label: str
    culprit_phrase: str
    mistaken_guess: str
    right_guess: str
    evidence: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    reveals: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "club_room": Setting(place="the detective club room", indoor=True, affords={"search", "sort", "inspect"}),
    "library": Setting(place="the library corner", indoor=True, affords={"search", "sort", "inspect"}),
    "workshop": Setting(place="the repair workshop", indoor=True, affords={"search", "sort", "inspect"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing="missing",
        item_label="bell",
        item_phrase="a tiny brass bell",
        culprit_kind="box",
        culprit_label="paper box",
        culprit_phrase="a paper box behind the shelf",
        mistaken_guess="janitor",
        right_guess="the box",
        evidence="a dusty footprint and a torn scrap of paper",
        lesson="look twice before guessing",
        tags={"knick", "mistake", "detective", "problem_solving", "lesson_learned"},
    ),
    "stamp": Mystery(
        id="stamp",
        missing="missing",
        item_label="stamp",
        item_phrase="a shiny library stamp",
        culprit_kind="drawer",
        culprit_label="desk drawer",
        culprit_phrase="a desk drawer that had slid shut",
        mistaken_guess="helper",
        right_guess="the drawer",
        evidence="a stuck label and a line of scratch marks",
        lesson="follow the clues before pointing a finger",
        tags={"knick", "mistake", "detective", "problem_solving", "lesson_learned"},
    ),
    "key": Mystery(
        id="key",
        missing="missing",
        item_label="key",
        item_phrase="a small silver key",
        culprit_kind="rug",
        culprit_label="rolled rug",
        culprit_phrase="a rolled rug by the back wall",
        mistaken_guess="cat",
        right_guess="the rug",
        evidence="a bent corner and a thread of lint",
        lesson="careful checking beats fast guessing",
        tags={"knick", "mistake", "detective", "problem_solving", "lesson_learned"},
    ),
}

TOOLS = {
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a little notebook",
        action="write down clues",
        reveals={"paper", "dust"},
    ),
    "lamp": Tool(
        id="lamp",
        label="lamp",
        phrase="a bright desk lamp",
        action="shine on the shadows",
        reveals={"scratch", "dust"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifier",
        phrase="a small magnifying glass",
        action="inspect tiny marks",
        reveals={"dust", "scratch", "paper"},
    ),
}

NAMES = ["Knick", "Mina", "Jules", "Toby", "Nia", "Sage", "Pip", "Lena"]
TYPES = {"girl", "boy"}
PARENTS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    parent_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the detective has a real clue, makes a mistake,
% then fixes it by checking the evidence.
mistake_story(M) :- mystery(M), clue(M, C), evidence(M, C), lesson(M, _).
"""
def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.evidence))
        lines.append(asp.fact("lesson", mid, m.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mistake_story/1."))
    asp_set = set(asp.atoms(model, "mistake_story"))
    py_set = {("bell",), ("stamp",), ("key",)}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python story set ({len(py_set)} mysteries).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        meters={"order": 0.0, "clue_seen": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 0.0, "embarrassment": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        meters={"order": 0.0},
        memes={"trust": 1.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name,
        kind="character",
        type="mother" if params.parent_name == "mother" else "father" if params.parent_name == "father" else "adult",
        label=params.parent_name,
        meters={"order": 0.0},
        memes={"trust": 1.0},
    ))
    item = world.add(Entity(
        id="missing_item",
        type=mystery.item_label,
        label=mystery.item_label,
        phrase=mystery.item_phrase,
        owner=detective.id,
        caretaker=parent.id,
        location="hidden",
        meters={"found": 0.0, "clean": 1.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        type=mystery.culprit_kind,
        label=mystery.culprit_label,
        phrase=mystery.culprit_phrase,
        meters={"hidden": 1.0},
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label="magnifier",
        phrase=TOOLS["magnifier"].phrase,
        meters={"use": 1.0},
    ))
    world.facts.update(
        detective=detective,
        helper=helper,
        parent=parent,
        item=item,
        culprit=culprit,
        tool=tool,
        mystery=mystery,
        setting=setting,
    )
    return world


def tell(world: World) -> None:
    f = world.facts
    d: Entity = f["detective"]
    h: Entity = f["helper"]
    p: Entity = f["parent"]
    m: Mystery = f["mystery"]
    item: Entity = f["item"]
    culprit: Entity = f["culprit"]

    # Setup
    world.say(
        f"{d.id} was a little detective who liked solving knick-sized mysteries."
    )
    world.say(
        f"At {world.setting.place}, {d.id} kept {d.pronoun('possessive')} notebook neat and loved any puzzle with a clear answer."
    )
    world.say(
        f"One morning, {m.item_phrase} went missing, and that made the whole room feel wrong."
    )
    world.para()

    # Mistake
    d.memes["worry"] += 1.0
    world.say(
        f"{d.id} spotted {m.evidence}, then made a mistake and blamed {m.mistaken_guess} right away."
    )
    h.memes["worry"] += 1.0
    p.memes["trust"] -= 0.5
    world.say(
        f"{h.id} frowned, because a quick guess can turn into a big mistake when the clues are still tiny."
    )
    world.say(
        f"{p.label.capitalize()} asked {d.id} to slow down and look again."
    )
    world.para()

    # Problem solving
    d.memes["embarrassment"] += 1.0
    world.say(
        f"{d.id} took a breath, opened {d.pronoun('possessive')} notebook, and started from the clue on the floor."
    )
    world.say(
        f"With the magnifier, {d.id} followed the dusty marks to {m.culprit_phrase}."
    )
    d.meters["clue_seen"] += 1.0
    item.meters["found"] = 1.0
    culprit.meters["hidden"] = 0.0
    world.say(
        f"Inside it sat {m.item_phrase}, safe and sound."
    )
    world.say(
        f"{d.id} lifted the bell, and the room's worry began to shrink."
    )
    world.para()

    # Resolution / lesson learned
    d.memes["relief"] += 1.0
    d.memes["pride"] += 1.0
    d.memes["trust"] += 1.0
    h.memes["trust"] += 1.0
    p.memes["trust"] += 1.0
    world.say(
        f"{d.id} told {mystery_culprit_name(m)} the truth and apologized for the mistake."
    )
    world.say(
        f"Then {d.id} put the bell back, closed {d.pronoun('possessive')} notebook, and remembered the lesson: {m.lesson}."
    )
    world.say(
        f"By the end, the club room was tidy again, and {d.id} smiled at the little case that had taught a big lesson."
    )


def mystery_culprit_name(m: Mystery) -> str:
    return m.mistaken_guess


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts_for(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    d: Entity = world.facts["detective"]
    return [
        f'Write a short detective story for a child about "{m.id}" that includes the words "knick" and "mistake".',
        f"Tell a problem-solving story where {d.id} makes a mistake, then follows clues to find {m.item_phrase}.",
        f"Write a gentle mystery story with a lesson learned ending about looking twice before guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["detective"]
    h: Entity = f["helper"]
    p: Entity = f["parent"]
    m: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"{d.id} was the little detective who tried to solve the missing {m.item_label}.",
        ),
        QAItem(
            question=f"What was the mistake {d.id} made at first?",
            answer=f"{d.id} made a mistake by blaming {m.mistaken_guess} before checking the clues.",
        ),
        QAItem(
            question=f"How did {d.id} solve the problem?",
            answer=f"{d.id} used a magnifier, followed the dusty marks, and found {m.item_phrase} in {m.culprit_phrase}.",
        ),
        QAItem(
            question=f"What lesson did {d.id} learn?",
            answer=f"{d.id} learned to {m.lesson}.",
        ),
        QAItem(
            question=f"How did the helper react?",
            answer=f"{h.id} reminded {d.id} to slow down and trust the clues instead of guessing too fast.",
        ),
        QAItem(
            question=f"Why did the grown-up want {d.id} to slow down?",
            answer=f"{p.label.capitalize()} wanted {d.id} to look carefully because fast guesses can lead to mistakes.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    out = [
        QAItem(
            question="What is a mistake?",
            answer="A mistake is something wrong that happens when someone guesses, does, or says the wrong thing.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why do people use a magnifier?",
            answer="People use a magnifier to look at tiny details more closely.",
        ),
    ]
    if "lesson_learned" in m.tags:
        out.append(
            QAItem(
                question="Why is it good to look twice before guessing?",
                answer="It is good to look twice because the first guess can be a mistake, and careful checking can show the real answer.",
            )
        )
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness and generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            combos.append((sid, mid))
    return combos


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: {setting!r} and {mystery!r} do not form a reasonable detective mystery here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld about a mistake and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    detective_name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != detective_name])
    parent = args.parent or rng.choice(PARENTS)
    detective_type = gender
    helper_type = "boy" if gender == "girl" else "girl"

    if (setting, mystery) not in valid_combos():
        raise StoryError(explain_rejection(setting, mystery))

    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent_name=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program(show: str) -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("valid", sid, "bell"))
        lines.append(asp.fact("valid", sid, "stamp"))
        lines.append(asp.fact("valid", sid, "key"))
    return "\n".join(lines) + "\n" + ASP_RULES + "\n" + show + "\n"


def show_asp_program() -> str:
    return asp_program("#show valid/2.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="club_room", mystery="bell", detective_name="Knick", detective_type="girl", helper_name="Mina", helper_type="boy", parent_name="mother"),
    StoryParams(setting="library", mystery="stamp", detective_name="Jules", detective_type="boy", helper_name="Nia", helper_type="girl", parent_name="father"),
    StoryParams(setting="workshop", mystery="key", detective_name="Pip", detective_type="girl", helper_name="Toby", helper_type="boy", parent_name="uncle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for setting, mystery in combos:
            print(f"  {setting:12} {mystery}")
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
            header = f"### {p.detective_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
