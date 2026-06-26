#!/usr/bin/env python3
"""
storyworlds/worlds/fix_gerund_cautionary_suspense_lesson_learned_space.py
==========================================================================

A small space-adventure storyworld about a cautious repair mission in a tiny
ship, with suspense and a lesson learned.

Seed premise:
- A young crew member wants to fix a broken rover / antenna / gate in space.
- The captain warns that rushing in space is dangerous.
- A suspense beat follows when something drifts loose or power dips.
- The crew learns to slow down, use a tether, and finish safely.

The world model tracks physical meters and emotional memes. The prose is driven
by state changes, not a frozen template.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    name: str
    place: str
    low_gravity: bool = True
    has_vacuum: bool = True
    hazards: set[str] = field(default_factory=set)


@dataclass
class FixTask:
    id: str
    verb: str
    gerund: str
    caution: str
    risk: str
    lesson: str
    suspense: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BrokenThing:
    id: str
    label: str
    phrase: str
    location: str
    size: str
    fixed_by: str
    helps: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    needed_for: set[str]
    phrase: str
    plural: bool = False


SETTINGS = {
    "orbital_hub": Setting(
        name="Orbital Hub",
        place="the Orbital Hub",
        hazards={"drift", "dark_tunnel", "flicker"},
    ),
    "moon_garage": Setting(
        name="Moon Garage",
        place="the Moon Garage",
        hazards={"dust", "drift"},
    ),
    "deep_ship": Setting(
        name="Deep Ship",
        place="the deep ship",
        hazards={"flicker", "drift", "alarm"},
    ),
}

TASKS = {
    "antenna": FixTask(
        id="antenna",
        verb="fix the antenna",
        gerund="fixing the antenna",
        caution="the captain said to slow down because loose tools can float away",
        risk="a drifting wrench could knock the signal dish sideways",
        lesson="They learned that careful hands keep space repairs safe.",
        suspense="Then the lights flickered, and the antenna's red blink went out for one long breath.",
        keyword="antenna",
        tags={"signal", "repair", "space"},
    ),
    "rover": FixTask(
        id="rover",
        verb="fix the rover",
        gerund="fixing the rover",
        caution="the mechanic warned that a rushed repair could leave the rover stuck",
        risk="one wrong bolt could make the rover slide off the docking pad",
        lesson="They learned to check each part before calling a job finished.",
        suspense="For a moment, the rover rolled one wheel, stopped, and then went quiet again.",
        keyword="rover",
        tags={"repair", "wheel", "space"},
    ),
    "door": FixTask(
        id="door",
        verb="fix the cargo door",
        gerund="fixing the cargo door",
        caution="the engineer reminded them that a jammed door in space can trap supplies",
        risk="a loose latch could let supplies drift into the dark bay",
        lesson="They learned that slow work is the best way to finish a tricky task.",
        suspense="The door shuddered halfway open, then caught with a soft metallic groan.",
        keyword="door",
        tags={"cargo", "repair", "space"},
    ),
}

BROKEN_THINGS = {
    "antenna": BrokenThing(
        id="antenna",
        label="antenna",
        phrase="a tall silver antenna",
        location="the roof dock",
        size="tall",
        fixed_by="signal patch",
        helps="calls can travel far again",
    ),
    "rover": BrokenThing(
        id="rover",
        label="rover",
        phrase="a small moon rover",
        location="the landing bay",
        size="small",
        fixed_by="wheel clamp",
        helps="the rover can roll again",
    ),
    "door": BrokenThing(
        id="door",
        label="cargo door",
        phrase="a heavy cargo door",
        location="the storage bay",
        size="heavy",
        fixed_by="latch key",
        helps="the bay can close safely",
    ),
}

GEAR = {
    "tether": Gear(
        id="tether",
        label="a safety tether",
        helps={"drift"},
        needed_for={"antenna", "rover", "door"},
        phrase="a safety tether",
    ),
    "gloves": Gear(
        id="gloves",
        label="grippy gloves",
        helps={"toolslip"},
        needed_for={"antenna", "door"},
        phrase="grippy gloves",
    ),
    "lamp": Gear(
        id="lamp",
        label="a small lamp",
        helps={"dark"},
        needed_for={"door"},
        phrase="a small lamp",
    ),
}

CREW_NAMES = ["Nova", "Milo", "Rin", "Pip", "Tala", "Juno", "Kai", "Zed"]
CREW_ROLES = ["cadet", "helper", "pilot", "mechanic", "messenger"]


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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    task: str
    broken: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def is_reasonable(setting: Setting, task: FixTask, broken: BrokenThing) -> bool:
    if setting.name == "Moon Garage" and task.id == "antenna" and broken.id == "door":
        return False
    return True


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for h in sorted(s.hazards):
            lines.append(asp.fact("hazard", sid, h))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for bid, b in BROKEN_THINGS.items():
        lines.append(asp.fact("broken", bid))
        lines.append(asp.fact("fixed_by", bid, b.fixed_by))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,T,B) :- setting(S), task(T), broken(B), not bad_combo(S,T,B).
bad_combo("moon_garage","antenna","door").
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def choose_gear(task: FixTask, broken: BrokenThing) -> Optional[Gear]:
    if task.id == "antenna":
        return GEAR["tether"]
    if task.id == "rover":
        return GEAR["tether"]
    if task.id == "door":
        return GEAR["tether"]
    return None


def tell(setting: Setting, task: FixTask, broken: BrokenThing, name: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="child", label=name))
    captain = world.add(Entity(id="captain", kind="character", type="adult", label="captain"))
    tool = world.add(Entity(id="tool", type="tool", label=task.keyword, phrase=task.keyword))
    thing = world.add(Entity(id=broken.id, type="thing", label=broken.label, phrase=broken.phrase))
    gear = choose_gear(task, broken)
    if gear:
        world.add(Entity(id=gear.id, type="gear", label=gear.label, phrase=gear.phrase))

    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 0.0
    captain.memes["worry"] = 1.0

    world.say(
        f"{name} was a small {role} aboard {setting.place}, and {name} loved the hum of ship engines."
    )
    world.say(
        f"One day, {name} wanted to {task.verb} so the {broken.label} could work again."
    )
    world.say(
        f"But {captain.label} held up a hand and said, \"{task.caution}. {task.risk.capitalize()}.\""
    )

    world.para()
    world.say(
        f"{name} still crept toward {broken.location}, carrying the little tool for {task.keyword}."
    )
    hero.memes["suspense"] = 1.0
    world.say(task.suspense)

    if gear:
        hero.memes["lesson"] = 1.0
        world.say(
            f"Then {name} noticed {gear.label} clipped to the wall and put it on first."
        )
        world.say(
            f"With the tether steady and careful hands, {name} kept every part from drifting."
        )
        world.say(
            f"At last, {name} finished {task.gerund}, and the {broken.label} worked again."
        )
        world.para()
        world.say(
            f"{task.lesson} The ship felt calm, and the little crew member smiled at the glowing panel."
        )
        thing.meters["fixed"] = 1.0
        thing.memes["safe"] = 1.0
        hero.memes["lesson"] = 1.0
        hero.memes["joy"] = 1.0
    else:
        world.say(
            f"Without the right gear, the repair could not be finished safely, so {name} stepped back."
        )

    world.facts = {
        "hero": hero,
        "captain": captain,
        "task": task,
        "broken": thing,
        "gear": gear,
        "role": role,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    broken = f["broken"]
    return [
        f'Write a short space-adventure story for a young child about {hero.id} and {task.keyword}.',
        f"Tell a cautious, suspenseful story where a small crew member wants {task.gerund} but learns to slow down.",
        f"Write a lesson-learned story in space where the {broken.label} is repaired safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    task: FixTask = f["task"]
    broken: Entity = f["broken"]
    role = f["role"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {task.verb} so the {broken.label} could work again.",
        ),
        QAItem(
            question=f"Why did the captain warn {hero.id} before the repair?",
            answer=f"The captain warned {hero.id} because {task.caution.lower()}. {task.risk.capitalize()}.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay safe during the repair?",
            answer=f"{gear.label.capitalize()} helped {hero.id} stay steady while {task.gerund}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=task.lesson,
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "tether": (
        "What is a safety tether?",
        "A safety tether is a strong strap or line that helps someone stay attached so they do not drift away in a place with low gravity.",
    ),
    "space": (
        "Why do people use careful tools in space?",
        "People use careful tools in space because floating parts and tiny mistakes can cause bigger problems when everything is drifting slowly.",
    ),
    "signal": (
        "What is a signal?",
        "A signal is a message or sound that carries information, like a radio call or a blinking light.",
    ),
    "repair": (
        "Why do things need repairs?",
        "Things need repairs when a part breaks or stops working, and fixing them helps the whole machine work again.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: FixTask = f["task"]
    out: list[QAItem] = []
    for key, (q, a) in WORLD_KNOWLEDGE.items():
        if key in task.tags or key == "space":
            out.append(QAItem(question=q, answer=a))
    return out


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about a careful repair and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--broken", choices=BROKEN_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=CREW_ROLES)
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


CURATED = [
    StoryParams(setting="orbital_hub", task="antenna", broken="antenna", name="Nova", role="cadet"),
    StoryParams(setting="moon_garage", task="rover", broken="rover", name="Milo", role="mechanic"),
    StoryParams(setting="deep_ship", task="door", broken="door", name="Rin", role="helper"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    broken = args.broken or task
    s = SETTINGS[setting]
    t = TASKS[task]
    b = BROKEN_THINGS[broken]
    if not is_reasonable(s, t, b):
        raise StoryError("That combination is not reasonable for this space story.")
    name = args.name or rng.choice(CREW_NAMES)
    role = args.role or rng.choice(CREW_ROLES)
    return StoryParams(setting=setting, task=task, broken=broken, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], BROKEN_THINGS[params.broken], params.name, params.role)
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set()
    for sid in SETTINGS:
        for tid in TASKS:
            for bid in BROKEN_THINGS:
                if is_reasonable(SETTINGS[sid], TASKS[tid], BROKEN_THINGS[bid]):
                    py.add((sid, tid, bid))
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} reasonable combos:")
        for combo in combos:
            print(" ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
