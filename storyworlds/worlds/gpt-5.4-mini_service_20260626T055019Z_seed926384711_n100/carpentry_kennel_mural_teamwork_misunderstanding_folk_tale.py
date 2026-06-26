#!/usr/bin/env python3
"""
A small folk-tale storyworld about carpentry, a kennel, and a mural.

A short seed tale:
---
In a little village by the pine trees, a woodworker and a painter were asked to
help the same town square. The woodworker wanted to build a sturdy kennel for
the baker's dog, while the painter wanted to brighten the wall with a mural of
the old forest and the moon. They both cared about the village, but they kept
getting in each other's way. The woodworker thought the painter would splatter
paint on the fresh boards, and the painter thought the woodworker would cover
the wall with sawdust. After a misunderstanding, they stopped, looked, and
listened. Then they realized they could work together: the kennel could sit
beneath the mural, and each would protect the other's work. By sunset, the dog
had a new home and the town had a kind picture on the wall.

This script turns that premise into a small causal simulation with state-driven
prose, grounded QA, and an inline ASP twin for the reasonableness gate.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    placed_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wood": 0.0, "paint": 0.0, "dust": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "worry": 0.0,
                "conflict": 0.0,
                "trust": 0.0,
                "misunderstanding": 0.0,
                "teamwork": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "painter"}
        male = {"boy", "man", "father", "woodworker", "carpenter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    noun: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Structure:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    type: str = "thing"


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_character()]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village_square": Setting(place="the village square", outdoors=True, affords={"carpentry", "mural"}),
    "barnyard": Setting(place="the old barnyard", outdoors=True, affords={"carpentry", "mural"}),
    "workyard": Setting(place="the workyard by the lane", outdoors=True, affords={"carpentry", "mural"}),
}

TASKS = {
    "carpentry": Task(
        id="carpentry",
        noun="carpentry",
        verb="build a kennel",
        gerund="building the kennel",
        mess="wood_dust",
        soil="full of sawdust",
        zone={"ground", "wall", "hands"},
        keyword="carpentry",
        tags={"wood", "teamwork"},
    ),
    "mural": Task(
        id="mural",
        noun="mural",
        verb="paint a mural",
        gerund="painting the mural",
        mess="paint",
        soil="spattered with paint",
        zone={"wall", "hands"},
        keyword="mural",
        tags={"paint", "teamwork"},
    ),
}

STRUCTURES = {
    "kennel": Structure(
        id="kennel",
        label="kennel",
        phrase="a sturdy kennel for the dog",
        region="ground",
        genders={"girl", "boy"},
        type="kennel",
    ),
    "mural": Structure(
        id="mural_art",
        label="mural",
        phrase="a bright mural of the moon and the pines",
        region="wall",
        genders={"girl", "boy"},
        type="mural",
    ),
}

GEAR = [
    Gear(
        id="dropcloth",
        label="a drop cloth",
        covers={"ground"},
        guards={"paint"},
        prep="lay down a drop cloth",
        tail="spread the drop cloth and kept the boards clean",
    ),
    Gear(
        id="coverboard",
        label="a cover board",
        covers={"wall"},
        guards={"wood_dust"},
        prep="set up a cover board",
        tail="stood the board by the wall and kept the mural space clear",
    ),
    Gear(
        id="screen",
        label="a simple screen",
        covers={"ground", "wall"},
        guards={"paint", "wood_dust"},
        prep="put up a simple screen",
        tail="raised the screen so neither job would spoil the other",
    ),
]

GIRL_NAMES = ["Mina", "Tessa", "Lina", "Mara", "Nora"]
BOY_NAMES = ["Bram", "Otto", "Pavel", "Joren", "Ivo"]
TRAITS = ["kindly", "careful", "patient", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for structure_id, struct in STRUCTURES.items():
                if task_id == "carpentry" and structure_id == "kennel":
                    combos.append((place, task_id, structure_id))
                if task_id == "mural" and structure_id == "mural":
                    combos.append((place, task_id, structure_id))
    return combos


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    structure: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Causal engine
# ---------------------------------------------------------------------------

def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        task = world.facts.get("task")
        if not task:
            continue
        if actor.meters[task.mess] < THRESHOLD:
            continue
        for ent in world.entities.values():
            if ent.kind != "thing" or ent.id == task.id:
                continue
            if ent.region not in world.zone:
                continue
            sig = ("spoil", actor.id, ent.id, task.mess)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters[task.mess] = ent.meters.get(task.mess, 0.0) + 1
            ent.meters["damage"] = ent.meters.get("damage", 0.0) + 1
            out.append(f"The {ent.label} got {task.soil}.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    pair = world.facts.get("pair")
    if not pair:
        return out
    a = world.get(pair[0])
    b = world.get(pair[1])
    if a.memes["worry"] >= THRESHOLD and b.memes["worry"] >= THRESHOLD:
        sig = ("misunderstanding", a.id, b.id)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["misunderstanding"] += 1
            b.memes["misunderstanding"] += 1
            a.memes["conflict"] += 1
            b.memes["conflict"] += 1
            out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [_r_spoil, _r_misunderstanding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__misunderstanding__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def task_risks_structure(task: Task, structure: Structure) -> bool:
    return structure.region in task.zone


def select_gear(task: Task, structure: Structure) -> Optional[Gear]:
    for gear in GEAR:
        if task.mess in gear.guards and structure.region in gear.covers:
            return gear
    return None


def predict_spoil(world: World, actor: Entity, task: Task, structure_id: str) -> bool:
    sim = world.copy()
    sim_actor = sim.get(actor.id)
    sim_actor.meters[task.mess] += 1
    sim.zone = set(task.zone)
    ent = sim.entities[structure_id]
    return ent.region in sim.zone


def folk_opening(hero: Entity, helper: Entity, setting: Setting) -> str:
    return f"In {setting.place}, {hero.id} and {helper.id} were known for kind hands and careful eyes."


def story_setup(hero: Entity, helper: Entity, task: Task, structure: Structure) -> str:
    return f"{hero.pronoun().capitalize()} loved {task.gerund}, while {helper.id} loved making sure {structure.label}s stood proud and useful."


def build_and_paint(world: World, hero: Entity, helper: Entity, task: Task, structure: Structure) -> None:
    world.zone = set(task.zone)
    hero.meters[task.mess] += 1
    hero.memes["joy"] += 1
    helper.memes["worry"] += 1
    propagate(world)


def warn(world: World, hero: Entity, helper: Entity, task: Task, structure: Structure) -> None:
    if predict_spoil(world, hero, task, structure.id):
        helper.memes["worry"] += 1
        world.say(f'"If we rush," {helper.id} said, "the {structure.label} will be {task.soil}."')


def misunderstand(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.memes["worry"] += 1
    hero.memes["trust"] += 0.5
    helper.memes["worry"] += 1
    world.say(f"{hero.id} thought {helper.id} did not care about the work, and {helper.id} thought the same.")
    world.say(f"That was a misunderstanding, and it sat between them like a cold stone.")


def teamwork_fix(world: World, hero: Entity, helper: Entity, task: Task, structure: Structure) -> Optional[Gear]:
    gear = select_gear(task, structure)
    if not gear:
        return None
    item = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.label,
        protective=True,
        covers=set(gear.covers),
        owner=hero.id,
    ))
    if task.mess == "paint":
        item.meters["paint"] = 0.0
    world.say(f"Then {helper.id} pointed to {gear.label} and smiled. " f'"{gear.prep}, and we can share the space," {helper.id} said.')
    return gear


def resolve(world: World, hero: Entity, helper: Entity, task: Task, structure: Structure, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    helper.memes["joy"] += 1
    helper.memes["trust"] += 1
    helper.memes["conflict"] = 0.0
    world.say(f"{hero.id} nodded, and the misunderstanding melted away.")
    world.say(f"Together they {gear.tail}; soon {task.gerund} and {structure.phrase} fit the same little place like two verses of one song.")


def tell(setting: Setting, task: Task, structure_cfg: Structure, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    structure = world.add(Entity(
        id=structure_cfg.id,
        kind="thing",
        type=structure_cfg.type,
        label=structure_cfg.label,
        phrase=structure_cfg.phrase,
        region=structure_cfg.region,
    ))
    world.facts.update(hero=hero, helper=helper, task=task, structure=structure, pair=(hero.id, helper.id))

    world.say(folk_opening(hero, helper, setting))
    world.say(story_setup(hero, helper, task, structure))

    world.para()
    world.say(f"{hero.id} began {task.gerund} near the old wall.")
    warn(world, hero, helper, task, structure)
    build_and_paint(world, hero, helper, task, structure)
    misunderstand(world, hero, helper, task)

    world.para()
    gear = teamwork_fix(world, hero, helper, task, structure)
    if gear:
        resolve(world, hero, helper, task, structure, gear)
    else:
        world.say(f"They could not find a safe way to work together, so the day stayed tangled.")

    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task, structure = f["hero"], f["helper"], f["task"], f["structure"]
    return [
        f"Write a gentle folk tale about {hero.id} and {helper.id} doing {task.noun} and making a {structure.label}.",
        f"Tell a short story where a {hero.type} named {hero.id} wants to {task.verb} while {helper.id} worries about a {structure.label}.",
        f"Write a child-friendly tale about teamwork, a misunderstanding, and a {structure.label} with the word '{task.keyword}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, structure = f["hero"], f["helper"], f["task"], f["structure"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who were the two workers in the village story?",
            answer=f"The story was about {hero.id} and {helper.id}. They both cared about the same little village job.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do first?",
            answer=f"{hero.id} wanted to {task.verb}. That was the main job {hero.id} loved to do.",
        ),
        QAItem(
            question=f"What was the other big project in the story?",
            answer=f"The other project was {structure.phrase}. It was meant to help the village and make the place look bright and useful.",
        ),
        QAItem(
            question=f"Why did the two workers get upset with each other?",
            answer=f"They had a misunderstanding. Each one thought the other would spoil the work, so both grew worried and a little cross.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help them work together?",
            answer=f"{gear.label.capitalize()} helped because it protected the shared space. That let them keep both the {task.noun} and the {structure.label} safe.",
        ))
        qa.append(QAItem(
            question=f"What changed at the end of the story?",
            answer=f"By the end, they trusted each other again and worked as a team. The village got both a strong {structure.label} and a bright finish to the wall.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "carpentry": [
        QAItem(
            question="What is carpentry?",
            answer="Carpentry is the work of shaping and joining wood to make useful things like houses, tables, and little shelters.",
        )
    ],
    "kennel": [
        QAItem(
            question="What is a kennel?",
            answer="A kennel is a small shelter made for a dog, so the dog has a safe place to rest.",
        )
    ],
    "mural": [
        QAItem(
            question="What is a mural?",
            answer="A mural is a big picture painted on a wall for people to see.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing about each other and need to talk to clear it up.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.add(world.facts["structure"].type)
    if world.facts.get("gear"):
        tags.add("teamwork")
    if world.facts["hero"].memes.get("misunderstanding", 0.0) >= THRESHOLD:
        tags.add("misunderstanding")
    out: list[QAItem] = []
    for tag in ["carpentry", "kennel", "mural", "teamwork", "misunderstanding"]:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[tag])
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_valid(P, carpentry, kennel) :- setting(P).
task_valid(P, mural, mural) :- setting(P).

compatible(P, T, S) :- task_valid(P, T, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for sid in STRUCTURES:
        lines.append(asp.fact("structure", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in ASP:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative selection
# ---------------------------------------------------------------------------

def explain_rejection(task: Task, structure: Structure) -> str:
    return f"(No story: {task.gerund} and a {structure.label} do not fit this tale's careful pattern.)"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.structure:
        task = TASKS[args.task]
        structure = STRUCTURES["kennel" if args.structure == "kennel" else "mural"]
        if not task_risks_structure(task, structure):
            raise StoryError(explain_rejection(task, structure))

    combos = [c for c in valid_story_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.structure is None or c[2] == args.structure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task_id, structure_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, structure=structure_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        STRUCTURES[params.structure],
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="village_square", task="carpentry", structure="kennel", name="Mina", gender="girl", helper="woman", trait="patient"),
    StoryParams(place="barnyard", task="mural", structure="mural", name="Bram", gender="boy", helper="man", trait="careful"),
    StoryParams(place="workyard", task="carpentry", structure="kennel", name="Nora", gender="girl", helper="woman", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about carpentry, a kennel, a mural, teamwork, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--structure", choices=STRUCTURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, t, s in combos:
            print(f"  {p:14} {t:10} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.task} at {p.place} ({p.structure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
