#!/usr/bin/env python3
"""
Bedtime boast storyworld.

A small child boasts about being the bravest at bedtime, then a gentle surprise
turns the moment into a happy ending. The world is modeled with physical meters
and emotional memes, and the story is generated from state changes rather than a
fixed paragraph template.
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
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Room:
    id: str
    label: str
    cozy: bool = True
    dark: bool = True


@dataclass(frozen=True)
class Comfort:
    id: str
    label: str
    helps_with: set[str] = field(default_factory=set)
    glow: bool = False
    soft: bool = False


@dataclass(frozen=True)
class NightTask:
    id: str
    verb: str
    twist: str
    surprise: str
    fear: str
    helped_by: str
    keyword: str = "boast"


ROOMS = {
    "bedroom": Room(id="bedroom", label="the bedroom", cozy=True, dark=True),
}

COMFORTS = {
    "nightlight": Comfort(id="nightlight", label="a little nightlight", helps_with={"dark"}, glow=True),
    "blanket": Comfort(id="blanket", label="a soft blanket", helps_with={"cold"}, soft=True),
    "teddy": Comfort(id="teddy", label="a teddy bear", helps_with={"lonely"}, soft=True),
}

TASKS = {
    "brave_sleep": NightTask(
        id="brave_sleep",
        verb="fall asleep",
        twist="the room went very dark all at once",
        surprise="the little nightlight flicked on by itself",
        fear="the dark felt much bigger than before",
        helped_by="nightlight",
    ),
    "missing_teddy": NightTask(
        id="missing_teddy",
        verb="settle into bed",
        twist="the teddy bear was nowhere under the pillow",
        surprise="the teddy was sitting on the chair with a paper star pinned to its ear",
        fear="the bed felt lonely without teddy",
        helped_by="teddy",
    ),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: bool = False
    glowing: bool = False

    def __post_init__(self):
        if not self.label:
            self.label = self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.room)
        clone.entities = json.loads(json.dumps({k: {
            "id": v.id, "kind": v.kind, "label": v.label, "type": v.type,
            "meters": v.meters, "memes": v.memes, "held": v.held, "glowing": v.glowing
        } for k, v in self.entities.items()}))
        rebuilt: dict[str, Entity] = {}
        for k, v in clone.entities.items():
            rebuilt[k] = Entity(
                id=v["id"], kind=v["kind"], label=v["label"], type=v["type"],
                meters=v["meters"], memes=v["memes"], held=v["held"], glowing=v["glowing"]
            )
        clone.entities = rebuilt
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _meter(entity: Entity, key: str) -> float:
    return float(entity.meters.get(key, 0.0))


def _meme(entity: Entity, key: str) -> float:
    return float(entity.memes.get(key, 0.0))


def _set_meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _set_meme(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = value


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _r_boast(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if _meme(child, "boast") < 1:
        return out
    sig = ("boast",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _set_meme(child, "pride", _meme(child, "pride") + 1)
    _set_meme(child, "careless", _meme(child, "careless") + 1)
    out.append(f"{child.label} puffed up and said {child.pronoun('possessive')} bedtime was easy.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    task = world.facts["task"]
    comfort = world.get(task.helped_by)
    if _meme(child, "worry") < 1:
        return out
    sig = ("surprise", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _set_meme(child, "surprise", _meme(child, "surprise") + 1)
    comfort.held = True
    comfort.glowing = True
    out.append(task.surprise.capitalize() + ".")
    return out


def _r_happy_ending(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    task = world.facts["task"]
    comfort = world.get(task.helped_by)
    if not comfort.held:
        return out
    sig = ("happy", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _set_meme(child, "worry", 0.0)
    _set_meme(child, "joy", _meme(child, "joy") + 2)
    out.append(
        f"{child.label} smiled, cuddled {comfort.label}, and found that the dark felt friendly again."
    )
    return out


RULES = [_r_boast, _r_surprise, _r_happy_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(task: NightTask, comfort: Comfort) -> bool:
    return comfort.id == task.helped_by


def valid_combos() -> list[tuple[str, str]]:
    return [("bedroom", task.id) for task in TASKS.values()]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    task: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    task = TASKS[params.task]
    world = World(room=room)
    child = world.add(Entity(
        id="child", kind="character", label=params.name, type=params.gender,
        meters={"awake": 1.0}, memes={"boast": 1.0, "joy": 1.0},
    ))
    parent = world.add(Entity(id="parent", kind="character", label=f"the {params.parent}", type=params.parent))
    comfort = world.add(Entity(
        id=task.helped_by, kind="thing", label=COMFORTS[task.helped_by].label,
        type="thing",
    ))
    world.facts.update(child=child, parent=parent, comfort=comfort, task=task, room=room)
    return world


def tell(world: World) -> World:
    child = world.get("child")
    parent = world.get("parent")
    task: NightTask = world.facts["task"]
    comfort = world.get(task.helped_by)

    world.say(f"It was bedtime in {world.room.label}, and {child.label} still had one last boast to make.")
    world.say(f"'{child.label} can fall asleep all by {child.pronoun('object')}self,' {child.pronoun('subject')} said.")

    world.para()
    _set_meme(child, "worry", 1.0)
    world.say(f"Then {task.twist}, and {task.fear}.")
    world.say(f"{parent.label} came in quietly and listened.")
    propagate(world)

    world.para()
    world.say(f"{parent.label} reached for {comfort.label} and showed {child.label} the little surprise.")
    propagate(world)

    world.para()
    world.say(
        f"In the end, {child.label} held {comfort.label}, the room glowed softly, and "
        f"{child.pronoun('subject')} fell asleep feeling brave for real."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    task: NightTask = world.facts["task"]
    child: Entity = world.facts["child"]
    return [
        'Write a gentle bedtime story where a child makes a boast, meets a surprise, and gets a happy ending.',
        f'Write a bedtime story for a young child named {child.label} that includes the word "boast".',
        f"Tell a cozy story where {child.label} says {child.pronoun('possessive')} bedtime is easy, then learns something sweet and comforting.",
        f"Write a short bedtime tale in which a small surprise helps a child feel brave about {task.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    task: NightTask = world.facts["task"]
    comfort = world.get(task.helped_by)
    return [
        QAItem(
            question=f"Why did {child.label} boast at bedtime?",
            answer=f"{child.label} was feeling proud and wanted to act brave before falling asleep.",
        ),
        QAItem(
            question=f"What surprise changed the bedtime mood for {child.label}?",
            answer=f"{task.surprise.capitalize()}. That little surprise made the room feel safer and kinder.",
        ),
        QAItem(
            question=f"How did {parent.label} help {child.label} have a happy ending?",
            answer=f"{parent.label} brought out {comfort.label} and stayed close until {child.label} felt calm again.",
        ),
        QAItem(
            question=f"What did {child.label} hold at the end?",
            answer=f"{child.label} held {comfort.label}, and the room glowed softly beside the bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nightlight for?",
            answer="A nightlight gives a small, soft glow so a room does not feel so dark at bedtime.",
        ),
        QAItem(
            question="Why do people use a blanket at night?",
            answer="A blanket helps keep a sleeper warm and cozy.",
        ),
        QAItem(
            question="What does a teddy bear often help with?",
            answer="A teddy bear can help a child feel safe, cozy, and not so lonely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "",
             "== (2) Story questions =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held:
            bits.append("held=True")
        if e.glowing:
            bits.append("glowing=True")
        lines.append(f"{e.id}: {e.label} ({e.kind}) " + " ".join(bits))
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room(bedroom).
task(brave_sleep).
helped_by(brave_sleep, nightlight).

valid_story(Room, Task) :- room(Room), task(Task).
compatible(Task, nightlight) :- helped_by(Task, nightlight).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("helped_by", tid, task.helped_by))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
# CLI
# ---------------------------------------------------------------------------

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ella", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Theo", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime boast storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    room = args.room or "bedroom"
    task = args.task or rng.choice(list(TASKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(room=room, task=task, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError("Unknown room.")
    if params.task not in TASKS:
        raise StoryError("Unknown bedtime task.")
    task = TASKS[params.task]
    if not valid_combo(task, COMFORTS[task.helped_by]):
        raise StoryError("The task does not have a reasonable comforting surprise.")

    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(room="bedroom", task="brave_sleep", name="Mia", gender="girl", parent="mother"),
            StoryParams(room="bedroom", task="missing_teddy", name="Leo", gender="boy", parent="father"),
        ]
        samples = [generate(p) for p in params_list]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
