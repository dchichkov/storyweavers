#!/usr/bin/env python3
"""
A small ghost-story world about a haunted knicknack and a child's careful
problem solving.

The premise:
- A child finds a strange knicknack.
- The knicknack makes a ghostly mess in the house at night.
- The child uses a calm plan, small tools, and a kind guess to solve it.
- The ending shows the room quiet again and a lesson learned.

This world keeps the simulation tiny and classical:
physical meters = amounts of noise, glow, cold, fear, dust, order
emotional memes = curiosity, worry, bravery, relief, trust
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
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        for k in ["noise", "glow", "cold", "dust", "order", "mess"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "bravery", "relief", "trust", "lesson"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    night: bool = True
    rooms: tuple[str, ...] = ("hallway", "bedroom", "attic")


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES_GIRL = ["Mina", "Nora", "Lily", "Ava", "Ivy", "Maya"]
NAMES_BOY = ["Theo", "Finn", "Eli", "Ben", "Leo", "Max"]

SETTINGS = {
    "house": Setting(place="the old house", night=True),
    "attic": Setting(place="the dusty attic", night=True),
    "hall": Setting(place="the long hallway", night=True),
}

# The seed words must appear in-world.
KNICKKNACKS = {
    "wxyz": {
        "label": "wxyz knicknack",
        "phrase": "a tiny wxyz knicknack with a silver shine",
        "kind": "knicknack",
        "tags": {"wxyz", "knicknack", "ghost"},
    }
}

TOOLS = {
    "lantern": {
        "label": "a lantern",
        "help": "shine light on the strange corners",
    },
    "string": {
        "label": "a bit of string",
        "help": "tie the little object to a chair so it would stop drifting",
    },
    "cloth": {
        "label": "a soft cloth",
        "help": "cover the knicknack and calm the glow",
    },
}

GHOST_TALES = {
    "ghost": [
        ("What is a ghost story?", "A ghost story is a spooky tale about strange things that seem to move or glow at night."),
        ("Why do old houses feel spooky?", "Old houses can feel spooky because they are dark, quiet, and full of creaks and shadows."),
    ],
    "knicknack": [
        ("What is a knicknack?", "A knicknack is a small decorative object, often kept on a shelf or table."),
    ],
    "wxyz": [
        ("What is wxyz in this story?", "wxyz is the strange name on the little knicknack, like a secret label someone wrote on it."),
    ],
    "problem solving": [
        ("What does problem solving mean?", "Problem solving means thinking carefully, trying a plan, and changing it if needed until things get better."),
    ],
    "lesson": [
        ("What is a lesson learned?", "A lesson learned is a helpful idea you remember after something goes wrong or feels tricky."),
    ],
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"curiosity": 1.0, "worry": 0.0, "bravery": 0.0, "relief": 0.0, "trust": 0.0, "lesson": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="mom" if params.parent == "mother" else "dad",
        memes={"curiosity": 0.0, "worry": 0.0, "bravery": 0.0, "relief": 0.0, "trust": 0.0, "lesson": 0.0},
    ))
    kn = KNICKNACKS["wxyz"]
    knicknack = world.add(Entity(
        id="knicknack",
        kind="thing",
        type="knicknack",
        label=kn["label"],
        phrase=kn["phrase"],
        tags=set(kn["tags"]),
        meters={"noise": 0.0, "glow": 0.0, "cold": 0.0, "dust": 1.0, "order": 0.0, "mess": 0.0},
    ))
    lantern = world.add(Entity(id="lantern", kind="thing", type="tool", label="a lantern"))
    cloth = world.add(Entity(id="cloth", kind="thing", type="tool", label="a soft cloth"))
    string = world.add(Entity(id="string", kind="thing", type="tool", label="a bit of string"))
    world.facts.update(child=child, parent=parent, knicknack=knicknack, lantern=lantern, cloth=cloth, string=string)
    return world


def ghostly_problem(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    kn: Entity = world.facts["knicknack"]  # type: ignore[assignment]

    world.say(f"{child.id} lived in {world.setting.place} and liked curious little things.")
    world.say(f"One evening, {child.id} found {kn.phrase} on a shelf, and the name wxyz was scratched on the bottom.")
    world.say(f"{child.id} carried it to the table because it looked too special to leave alone.")

    world.para()
    kn.meters["glow"] += 1.0
    kn.meters["cold"] += 1.0
    kn.meters["noise"] += 1.0
    child.memes["worry"] += 1.0
    parent.memes["worry"] += 1.0
    world.say(f"After the lights went low, the knicknack gave off a pale glow and a chilly hum.")
    world.say(f"The room felt spooky, and {child.id} heard a tiny tap-tap from the dark hallway.")
    world.say(f"{child.id}'s {parent.label} said, \"Let's think first and solve this gently.\"")

    world.para()
    child.memes["bravery"] += 1.0
    world.say(f"{child.id} took a breath and tried problem solving instead of running away.")
    world.say(f"First {child.id} held up {world.facts['lantern'].label} to look for where the sound came from.")
    world.say(f"Then {child.id} wrapped the wxyz knicknack in {world.facts['cloth'].label} so the glow could not flash in the dark.")
    world.say(f"Last, {child.id} used {world.facts['string'].label} to keep the little thing steady on the table.")

    kn.meters["glow"] = 0.0
    kn.meters["noise"] = 0.0
    kn.meters["cold"] = 0.0
    kn.meters["order"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["trust"] += 1.0
    child.memes["lesson"] += 1.0
    parent.memes["relief"] += 1.0
    parent.memes["trust"] += 1.0

    world.para()
    world.say(f"The hallway grew quiet again.")
    world.say(f"The knicknack stayed on the table, calm and still, and the old house did not feel so spooky anymore.")
    world.say(f"{child.id} smiled and learned that a small, careful plan can solve even a ghostly problem.")
    world.say(f"That night, {child.id} went to bed feeling brave, and the wxyz knicknack only shone softly beside the lamp.")


def generate_story(world: World) -> None:
    ghostly_problem(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    return [
        f"Write a short ghost story for a young child about {child.id}, a wxyz knicknack, and a calm problem-solving plan.",
        "Tell a spooky but gentle story that begins with a strange knicknack, adds a nighttime problem, and ends with a lesson learned.",
        "Write a child-friendly ghost story using the words knicknack and wxyz, where a child solves the mystery without being mean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    kn: Entity = f["knicknack"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What strange thing did {child.id} find in {world.setting.place}?",
            answer=f"{child.id} found {kn.phrase}, a tiny knicknack with the name wxyz on it.",
        ),
        QAItem(
            question=f"What made the room feel spooky at night?",
            answer=f"The knicknack gave off a pale glow, a chilly feeling, and a tiny tapping sound, so the room felt spooky.",
        ),
        QAItem(
            question=f"How did {child.id} solve the problem?",
            answer=f"{child.id} used problem solving by looking with a lantern, covering the knicknack with a soft cloth, and tying it down with string so it would stay still.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that a calm plan and careful thinking can solve a scary problem.",
        ),
        QAItem(
            question=f"How did {child.id}'s {parent.label} help?",
            answer=f"{child.id}'s {parent.label} stayed calm and reminded {child.id} to think first and solve the problem gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["knicknack"].tags)  # type: ignore[index]
    out: list[QAItem] = []
    for key, items in GHOST_TALES.items():
        if key == "problem solving":
            if True:
                out.extend(QAItem(question=q, answer=a) for q, a in items)
        elif key == "lesson":
            out.extend(QAItem(question=q, answer=a) for q, a in items)
        elif key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:9} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
knicknack(k1).
has_word(k1,wxyz).
spooky(k1).
problem(k1) :- spooky(k1).
solved(k1) :- problem(k1), tool(lantern), tool(cloth), tool(string).
lesson_learned(k1) :- solved(k1).

tool(lantern).
tool(cloth).
tool(string).

#show problem/1.
#show solved/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("knicknack", "k1"),
        asp.fact("has_word", "k1", "wxyz"),
        asp.fact("spooky", "k1"),
        asp.fact("tool", "lantern"),
        asp.fact("tool", "cloth"),
        asp.fact("tool", "string"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    probs = set(asp.atoms(model, "problem"))
    solved = set(asp.atoms(model, "solved"))
    lessons = set(asp.atoms(model, "lesson_learned"))
    ok = probs == {("k1",)} and solved == {("k1",)} and lessons == {("k1",)}
    if ok:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("problem:", probs)
    print("solved:", solved)
    print("lesson_learned:", lessons)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_names(gender: str) -> list[str]:
    return NAMES_GIRL if gender == "girl" else NAMES_BOY


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a knicknack and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(valid_names(gender))
    parent = args.parent or rng.choice(["mother", "father"])
    place = args.place or rng.choice(list(SETTINGS.keys()))
    return StoryParams(name=name, gender=gender, parent=parent, place=place)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
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
    StoryParams(name="Mina", gender="girl", parent="mother", place="house"),
    StoryParams(name="Theo", gender="boy", parent="father", place="attic"),
    StoryParams(name="Ivy", gender="girl", parent="mother", place="hall"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
