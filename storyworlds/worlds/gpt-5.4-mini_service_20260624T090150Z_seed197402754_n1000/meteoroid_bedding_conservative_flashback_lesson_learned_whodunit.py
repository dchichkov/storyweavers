#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a missing bedroom keepsake, a startled
family, a flashback clue, and a lesson learned after a meteoroid leaves an odd
mark in the yard.

The domain is intentionally tiny and classical:
- a child finds a mystery
- a careful, conservative parent worries about the house and the bedding
- a flashback reveals the real clue
- the family solves the whodunit and learns a gentle lesson
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
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

CHARACTER_TYPES = {"girl", "boy", "mother", "father", "grandmother", "grandfather"}
MOODS = {"calm", "worried", "curious", "startled", "relieved", "proud"}

PLACES = {
    "house": {"indoors": True},
    "garden": {"indoors": False},
    "bedroom": {"indoors": True},
    "yard": {"indoors": False},
}

EVENTS = {
    "meteoroid": {
        "verb": "fall from the sky",
        "mark": "a little crater",
        "sound": "a loud thump",
        "clue": "a shiny dark stone",
    },
    "bedding": {
        "verb": "get rumpled",
        "mark": "a messy pile",
        "sound": "the rustle of sheets",
        "clue": "a tucked corner pulled loose",
    },
}

# ---------------------------------------------------------------------------
# Entities / world model
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters or {})
        self.memes = dict(self.memes or {})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the house"
    indoors: bool = True


@dataclass
class StoryParams:
    place: str
    focus: str
    child_name: str
    child_type: str
    parent_type: str
    parent_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.flashback_used = self.flashback_used
        return clone


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def safe_conservative_reasonable(parent: Entity) -> bool:
    return parent.memes.get("careful", 0.0) >= THRESHOLD or parent.memes.get("conservative", 0.0) >= THRESHOLD


def clue_points_to_meteoroid(world: World) -> bool:
    return world.facts.get("clue_kind") == "meteoroid"


def flashback_needed(world: World) -> bool:
    return not world.flashback_used and clue_points_to_meteoroid(world)


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    setting = Setting(place=PLACES[params.place]["name"], indoors=PLACES[params.place]["indoors"])
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        memes={"curious": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        memes={"careful": 1.0, "conservative": 1.0, "worry": 0.5},
    ))
    bedding = world.add(Entity(
        id="bedding",
        type="thing",
        label="bedding",
        phrase="the bed sheets and blanket",
        caretaker=parent.id,
        location="bedroom",
        meters={"rumpled": 0.0, "dirty": 0.0},
    ))
    stone = world.add(Entity(
        id="stone",
        type="thing",
        label="a dark stone",
        phrase="a dark stone with a bright scrape",
        location=params.place,
        meters={"scuffed": 1.0},
    ))
    mystery = world.add(Entity(
        id="mystery",
        type="thing",
        label="the clue",
        phrase="the strange mark by the window",
        location=params.place,
    ))
    world.facts.update(child=child, parent=parent, bedding=bedding, stone=stone, mystery=mystery)
    return world


def introduce(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    world.say(f"{child.id} was a curious little {child.type} who loved noticing strange details.")
    world.say(f"At home, {parent.label} was careful and conservative, and {parent.pronoun('subject')} liked everything tidy and in place.")


def disturb_bedding(world: World) -> None:
    bedding = world.facts["bedding"]
    bedding.meters["rumpled"] += 1.0
    world.say("One morning, the bedding looked odd, as if someone had tugged it in a hurry.")


def mystery_scene(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    place = world.setting.place
    world.para()
    world.say(f"In the {place}, {child.id} found a strange mark near the window and called for {parent.label}.")
    world.say(f"{parent.label} looked at the mark, then at the rumpled bedding, and frowned.")
    world.say("“Who made this mess?” the parent asked.")


def inspect_clues(world: World) -> None:
    child = world.facts["child"]
    bedding = world.facts["bedding"]
    stone = world.facts["stone"]
    parent = world.facts["parent"]

    child.memes["curious"] += 1.0
    parent.memes["worry"] += 1.0

    world.say(f"{child.id} leaned closer and noticed {stone.phrase}.")
    world.say(f"The bedding had a pulled corner, and that made the room feel more like a whodunit than a simple accident.")

    if flashback_needed(world):
        world.para()
        world.flashback_used = True
        world.say("Flashback: the night before, there had been a quick clatter on the roof and a tiny bounce near the garden.")
        world.say("Now the clue made sense: something had fallen from the sky, bounced once, and nudged the window frame.")
        world.facts["clue_kind"] = "meteoroid"
        world.facts["lesson"] = "look closely before guessing"

    world.say("The parent paused, and the careful look on {0} softened.".format(parent.label))


def solve_whodunit(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    bedding = world.facts["bedding"]
    stone = world.facts["stone"]

    world.say(f"{child.id} pointed to the dark stone and said, “It wasn't a person. It was a meteoroid!”")
    world.say(f"{parent.label} picked up the bedding, saw the little tear, and understood that the odd mark had come from the meteoroid's tumble.")
    bedding.meters["rumpled"] = 0.0
    bedding.meters["dirty"] = 0.0
    child.memes["relief"] += 1.0
    parent.memes["worry"] = 0.0
    parent.memes["pride"] = 1.0
    world.say("Together they put the bedding back in order, and the room felt calm again.")
    world.say(f"{parent.label} smiled and said the best clue had been to slow down and look carefully.")
    world.say(f"{child.id} remembered the lesson learned: not every mystery is mischief, and good clues can solve a whodunit.")


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.focus not in EVENTS:
        raise StoryError("Unknown focus event.")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("Child must be a girl or a boy.")
    if params.parent_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError("Parent type must be a parent or grandparent.")
    if params.parent_trait != "conservative":
        raise StoryError("This world expects a conservative parent trait for the mystery tone.")

    world = setup_world(params)
    introduce(world)
    disturb_bedding(world)
    mystery_scene(world)
    inspect_clues(world)
    solve_whodunit(world)

    world.facts.update(params=params, setting=world.setting)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING_REGISTRY = {
    "house": Setting(place="the house", indoors=True),
    "garden": Setting(place="the garden", indoors=False),
    "bedroom": Setting(place="the bedroom", indoors=True),
}

FOCUS_REGISTRY = {
    "meteoroid": EVENTS["meteoroid"],
    "bedding": EVENTS["bedding"],
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Theo", "Max", "Noah"]
PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTING_REGISTRY:
        for focus in FOCUS_REGISTRY:
            out.append((place, focus))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    child = world.facts["child"]
    return [
        f"Write a whodunit for a small child named {child.id} about a strange clue in {world.setting.place}.",
        f"Tell a short story with a flashback and a lesson learned after a meteoroid leaves a mystery behind.",
        f"Write a gentle mystery where a conservative {p.parent_type} helps solve what happened to the bedding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    bedding = world.facts["bedding"]
    qa = [
        QAItem(
            question=f"Who found the strange clue in the story?",
            answer=f"{child.id} found the strange clue and called for {parent.label}."
        ),
        QAItem(
            question=f"What was the parent like?",
            answer=f"{parent.label} was careful and conservative, so {parent.pronoun('subject')} wanted to know exactly what had happened."
        ),
        QAItem(
            question=f"What got rumpled in the mystery?",
            answer=f"The bedding got rumpled, which helped turn the scene into a whodunit."
        ),
        QAItem(
            question=f"What did the flashback reveal?",
            answer="The flashback showed a quick clatter on the roof and a bounce near the garden, which pointed to a meteoroid."
        ),
        QAItem(
            question=f"What lesson was learned at the end?",
            answer="The lesson learned was to look closely before guessing, because good clues can solve a mystery."
        ),
    ]
    if bedding.meters.get("dirty", 0.0) <= 0.0:
        qa.append(QAItem(
            question="Was the bedding left messy at the end?",
            answer="No. The bedding was put back in order, and the room felt calm again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meteoroid?",
            answer="A meteoroid is a small space rock that can travel through space and sometimes fall toward Earth."
        ),
        QAItem(
            question="What is bedding?",
            answer="Bedding is the sheets, blanket, and other soft things that make a bed cozy."
        ),
        QAItem(
            question="What does conservative mean here?",
            answer="In this story, conservative means careful and not quick to jump to conclusions."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something from before the main moment in the story."
        ),
        QAItem(
            question="What does lesson learned mean?",
            answer="A lesson learned is the helpful idea the characters understand by the end of the story."
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
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(house). place(garden). place(bedroom).
indoors(house). indoors(bedroom).

focus(meteoroid). focus(bedding).

valid(Place, Focus) :- place(Place), focus(Focus).

story_kind(whodunit) :- valid(_, _).
needs_flashback(Focus) :- focus(Focus), Focus = meteoroid.
lesson_learned(Focus) :- focus(Focus), valid(_, Focus).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTING_REGISTRY:
        lines.append(asp.fact("place", place))
        if SETTING_REGISTRY[place].indoors:
            lines.append(asp.fact("indoors", place))
    for focus in FOCUS_REGISTRY:
        lines.append(asp.fact("focus", focus))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a meteoroid, bedding, and a conservative parent.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--focus", choices=FOCUS_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    focus = args.focus or rng.choice(list(FOCUS_REGISTRY))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    if parent_type not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError("Unsupported parent type.")
    return StoryParams(
        place=place,
        focus=focus,
        child_name=name,
        child_type=child_type,
        parent_type=parent_type,
        parent_trait="conservative",
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", focus="meteoroid", child_name="Mia", child_type="girl", parent_type="mother", parent_trait="conservative"),
    StoryParams(place="garden", focus="meteoroid", child_name="Leo", child_type="boy", parent_type="father", parent_trait="conservative"),
    StoryParams(place="bedroom", focus="bedding", child_name="Nora", child_type="girl", parent_type="grandmother", parent_trait="conservative"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, focus in combos:
            print(f"  {place:8} {focus}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
