#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/maintenance_consist_hygienist_humor_twist_surprise_slice.py
==========================================================================================

A small slice-of-life storyworld about a child, a hygienist, and a routine
maintenance day that turns into a funny little surprise.

Seed words:
- maintenance
- consist
- hygienist

Style:
- Slice of life

Features:
- Humor
- Twist
- Surprise

The world is built around a simple everyday setting: a neighborhood clinic that
needs a few repairs while a child comes in for a checkup. A hygienist notices a
small problem, calls for maintenance, and the day ends with a cheerful surprise
that keeps the routine gentle and concrete.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/maintenance_consist_hygienist_humor_twist_surprise_slice.py
    python storyworlds/worlds/gpt-5.4-mini/maintenance_consist_hygienist_humor_twist_surprise_slice.py --all
    python storyworlds/worlds/gpt-5.4-mini/maintenance_consist_hygienist_humor_twist_surprise_slice.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/maintenance_consist_hygienist_humor_twist_surprise_slice.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hygienist"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    mood: str
    rooms: list[str]
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Task:
    id: str
    name: str
    consist: str
    mess: str
    fix: str
    joke: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

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
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_dirty(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("dirty", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["need_maintenance"] += 1
        out.append("__dirty__")
    return out


def _r_mood(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["need_maintenance"] >= THRESHOLD:
        for e in world.characters():
            e.memes["curious"] += 1
        out.append("__curious__")
    return out


RULES = [Rule("dirty", "physical", _r_dirty), Rule("mood", "social", _r_mood)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def maintenance_at_risk(task: Task) -> bool:
    return True


def best_tool(task: Task) -> str:
    return task.fix


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in TASKS:
            for tool in TOOLS:
                if task_tool_matches(TASKS[tid], TOOLS[tool]):
                    combos.append((sid, tid, tool))
    return combos


def task_tool_matches(task: Task, tool: Tool) -> bool:
    return task.fix == tool.id


def predict(world: World, task: Task) -> dict:
    sim = world.copy()
    do_task(sim, task, narrate=False)
    return {
        "maintenance": sim.get("room").meters["need_maintenance"],
        "surprise": sim.facts.get("surprise", False),
    }


def do_task(world: World, task: Task, narrate: bool = True) -> None:
    worker = world.get("hygienist")
    worker.memes["purpose"] += 1
    worker.meters["mess"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, hygienist: Entity, task: Task) -> None:
    child.memes["comfort"] += 1
    hygienist.memes["calm"] += 1
    world.say(
        f"On a bright morning at {world.setting.place}, {child.id} came in with "
        f"{child.pronoun('possessive')} {hygienist.label_word} for a routine visit. "
        f"{world.setting.mood.capitalize()} and tidy, the place was the kind of room "
        f"where small jobs could quietly get done."
    )
    world.say(
        f'"The day can consist of a checkup, a little waiting, and a lot of smiling," '
        f'{hygienist.id} said, and {child.id} giggled at the word consist.'
    )
    world.say(
        f"Behind them, the clinic needed {task.name}, but nobody had made a fuss about it yet."
    )


def notice(world: World, hygienist: Entity, task: Task, tool: Tool) -> None:
    world.say(
        f"{hygienist.id} heard a tiny squeak from the chair and noticed the room needed {task.name}. "
        f"That made {hygienist.pronoun('subject')} call for {tool.phrase} right away."
    )


def humor(world: World, child: Entity, task: Task) -> None:
    world.say(
        f'{child.id} whispered, "Does maintenance mean the chair is trying to tell a joke?" '
        f'and {hygienist_name(world)} laughed so hard {task.joke} made the whole room feel lighter.'
    )


def hygienist_name(world: World) -> str:
    return world.get("hygienist").id


def surprise(world: World, child: Entity, hygienist: Entity, tool: Tool) -> None:
    world.facts["surprise"] = True
    world.say(
        f"Then came a surprise: the maintenance cart had a sticker of a smiling tooth on it, "
        f"and {hygienist.id} had packed a tiny bubble wand for the waiting room."
    )
    world.say(
        f'{child.id} blew a few bubbles, and even the serious sink seemed to soften up and watch.'
    )
    world.say(
        f"The repair got done, the room stayed calm, and the little joke became part of the visit."
    )


def resolve(world: World, child: Entity, hygienist: Entity, task: Task) -> None:
    child.memes["joy"] += 1
    hygienist.memes["satisfaction"] += 1
    world.say(
        f"By the end, the chair was steady again, the room felt ready for the next patient, "
        f"and {child.id} waved goodbye with a grin."
    )
    world.say(
        f"{hygienist.id} smiled at the clean, quiet hallway. The day had been simple, useful, and a little funny."
    )


SETTINGS = {
    "clinic": Setting("clinic", "the neighborhood clinic", "calm", ["waiting room", "hallway", "exam room"], {"slice", "life"}),
    "school": Setting("school", "the school nurse office", "busy", ["waiting room", "hallway", "exam room"], {"slice", "life"}),
    "library": Setting("library", "the small library clinic corner", "quiet", ["reading nook", "hallway", "corner"], {"slice", "life"}),
}

TASKS = {
    "chair": Task("chair", "chair maintenance", "chair repair", "wobble", "fixed chair", "the chair squeaked like a mouse trying to sing", {"maintenance"}),
    "sink": Task("sink", "sink maintenance", "sink repair", "drip", "tightened sink", "the sink went plink-plink like a tiny drum", {"maintenance"}),
    "lights": Task("lights", "light maintenance", "light repair", "flicker", "fixed lights", "the light blinked like it was winking", {"maintenance"}),
}

TOOLS = {
    "chair": Tool("chair", "wrench", "a small wrench", "repair chairs", {"maintenance"}),
    "sink": Tool("sink", "spanner", "a little spanner", "repair sinks", {"maintenance"}),
    "lights": Tool("lights", "ladder", "a short ladder", "reach lights", {"maintenance"}),
}

GIRL_NAMES = ["Mina", "Lia", "Tara", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Owen", "Eli"]
TAGS = ["gentle", "curious", "playful", "thoughtful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    child_name: str
    child_gender: str
    hygienist_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def tell(setting: Setting, task: Task, tool: Tool, child_name: str, child_gender: str, hygienist_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["curious"]))
    hygienist = world.add(Entity(id=hygienist_name, kind="character", type="hygienist", role="hygienist", label="the hygienist"))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="tool", type="tool", label=tool.label))
    setup(world, child, hygienist, task)
    world.para()
    notice(world, hygienist, task, tool)
    humor(world, child, task)
    do_task(world, task)
    world.para()
    surprise(world, child, hygienist, tool)
    resolve(world, child, hygienist, task)
    world.facts.update(child=child, hygienist=hygienist, task=task, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the word "maintenance" and the word "consist".',
        f'Tell a gentle clinic story where {f["child"].id} visits {f["hygienist"].id}, hears a funny maintenance problem, and gets a small surprise.',
        f'Write a story with humor, a twist, and a surprise about a hygienist doing {f["task"].name}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, hygienist, task = f["child"], f["hygienist"], f["task"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {hygienist.id}, who had an ordinary visit that turned into a funny maintenance day."),
        ("What word did the hygienist use about the day?", f'{hygienist.id} said the day could consist of a checkup, a little waiting, and a lot of smiling. That made the word feel playful instead of boring.'),
        ("What problem needed attention?", f"The clinic needed {task.name}, because something in the room was a little noisy and not quite right."),
        ("How did the story end?", f"It ended with the room fixed, {child.id} smiling, and everyone feeling calm after the surprise."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is maintenance?", "Maintenance means fixing or caring for something so it keeps working well."),
        ("What does a hygienist do?", "A hygienist helps keep teeth clean and healthy, usually by cleaning them and checking for problems."),
        ("What does consist mean?", "Consist means to be made up of parts. If a day consists of several things, those things are the parts of the day."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("clinic", "chair", "chair", "Mina", "girl", "Rosa"),
    StoryParams("school", "sink", "sink", "Leo", "boy", "Ivy"),
    StoryParams("library", "lights", "lights", "Nora", "girl", "June"),
]


def explain_rejection(task: Task, tool: Tool) -> str:
    if not task_tool_matches(task, tool):
        return f"(No story: {tool.label} would not help with {task.name}, so the maintenance joke would not have an honest twist.)"
    return "(No story: this combination does not make sense.)"


def valid_combo_for_params(args: argparse.Namespace, rng: random.Random) -> list[tuple[str, str, str]]:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about maintenance, a hygienist, humor, twist, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hygienist-name")
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
    combos = valid_combo_for_params(args, rng)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, tool = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    hygienist_name = args.hygienist_name or rng.choice(["Rosa", "Iris", "June", "Marta", "Celeste"])
    return StoryParams(setting, task, tool, child_name, child_gender, hygienist_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], TOOLS[params.tool], params.child_name, params.child_gender, params.hygienist_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
valid(S, T, U) :- setting(S), task(T), tool(U), task_tool(T, U).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_tool", tid, TASKS[tid].fix))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: story generation failed.")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
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
            header = f"### {p.child_name}: {p.setting} / {p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
