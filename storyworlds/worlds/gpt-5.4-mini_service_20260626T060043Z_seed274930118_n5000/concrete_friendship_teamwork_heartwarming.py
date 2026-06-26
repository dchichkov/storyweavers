#!/usr/bin/env python3
"""
A tiny heartwarming story world about friends working together on a concrete
project.

Seed premise:
- A child wants to do a small concrete job.
- A friend comes over and helps.
- They make a little mistake or face a challenge.
- Together they fix it, and the finished concrete becomes a proof of teamwork.

The world is intentionally small and constraint-checked so every generated story
feels like a complete little tale.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

REGIONS = {"hands", "feet", "torso", "face"}

# When concrete gets on clothing or skin, it is a problem.
MESS_KINDS = {"dusty", "splashed", "streaked"}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dusty", "splashed", "streaked", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "worry", "helpfulness", "frustration", "pride", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "concrete"
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


# ---------------------------------------------------------------------------
# Story rules
# ---------------------------------------------------------------------------


def _r_concrete_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for task in TASKS.values():
            if actor.meters[task.mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", actor.id, item.id, task.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[task.mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy with concrete.")
    return out


def _r_helpfulness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["helpfulness"] < THRESHOLD:
            continue
        sig = ("helpfulness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["pride"] += 1
        out.append(f"{actor.id} felt proud to be helping.")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("cleanup", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That meant a little more cleaning for {carer.label}.")
    return out


CAUSAL_RULES = [
    Rule("concrete_mess", _r_concrete_mess),
    Rule("helpfulness", _r_helpfulness),
    Rule("cleanup", _r_cleanup),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "driveway": Setting(place="the driveway", indoor=False, affords={"mix", "patch"}),
    "garden": Setting(place="the garden path", indoor=False, affords={"patch"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"mix"}),
}

TASKS = {
    "mix": Task(
        id="mix",
        verb="mix the concrete",
        gerund="mixing concrete",
        rush="run to the bucket",
        mess="dusty",
        soil="dusty",
        zone={"hands", "torso"},
        tags={"concrete"},
    ),
    "patch": Task(
        id="patch",
        verb="patch the crack",
        gerund="patching the crack",
        rush="kneel by the crack",
        mess="splashed",
        soil="splashed",
        zone={"hands", "feet"},
        tags={"concrete"},
    ),
}

PROJECTS = {
    "apron": Project(
        label="apron",
        phrase="a sturdy apron",
        type="apron",
        region="torso",
        genders={"girl", "boy"},
    ),
    "gloves": Project(
        label="gloves",
        phrase="a pair of work gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
    "boots": Project(
        label="boots",
        phrase="a pair of rubber boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="work gloves",
        covers={"hands"},
        guards={"dusty"},
        prep="put on the work gloves first",
        tail="went back for the work gloves",
        plural=True,
    ),
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"dusty", "splashed"},
        prep="tie on an apron first",
        tail="went back for the apron",
    ),
    Gear(
        id="boots",
        label="rubber boots",
        covers={"feet"},
        guards={"splashed"},
        prep="pull on rubber boots first",
        tail="went back for the rubber boots",
        plural=True,
    ),
]

FRIEND_NAMES = ["Maya", "Nina", "Owen", "Ben", "Lila", "Zoe", "Eli", "Milo"]
CHILD_NAMES = ["Ava", "Noah", "Mia", "Leo", "Iris", "Theo", "Luna", "Max"]
TRAITS = ["kind", "curious", "gentle", "cheerful", "helpful", "patient"]


@dataclass
class StoryParams:
    place: str
    task: str
    project: str
    name: str
    friend: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------


def task_at_risk(task: Task, project: Project) -> bool:
    return project.region in task.zone


def select_gear(task: Task, project: Project) -> Optional[Gear]:
    for gear in GEAR:
        if task.mess in gear.guards and project.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for proj_id, proj in PROJECTS.items():
                if task_at_risk(task, proj) and select_gear(task, proj):
                    combos.append((place, task_id, proj_id))
    return combos


def explain_rejection(task: Task, project: Project) -> str:
    if not task_at_risk(task, project):
        return (
            f"(No story: {task.gerund} does not reach the {project.region}, so "
            f"the project would stay safe and there is no honest problem to solve.)"
        )
    return (
        f"(No story: no gear in this world both protects {project.label} and "
        f"matches {task.mess}. The compromise would be fake, so this pairing is rejected.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------


def predict_mess(world: World, actor: Entity, task: Task, project_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    project = sim.entities.get(project_id)
    return {"soiled": bool(project and project.meters["dirty"] >= THRESHOLD)}


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        return
    world.zone = set(task.zone)
    actor.meters[task.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved helping with things that mattered.")


def love_story(world: World, hero: Entity, friend: Entity, task: Task) -> None:
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(f"{hero.id} and {friend.id} liked to do things together, and {task.gerund} felt like a big adventure.")


def bring_project(world: World, parent: Entity, hero: Entity, project: Entity) -> None:
    world.say(f"One morning, {hero.id}'s {parent.label_word} brought home {hero.pronoun('object')} {project.phrase}.")
    project.worn_by = hero.id


def want_to_work(world: World, hero: Entity, task: Task, place: str) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.id} wanted to {task.verb} at {place}, because the idea of making something useful felt wonderful.")


def warn(world: World, parent: Entity, hero: Entity, task: Task, project: Entity) -> bool:
    pred = predict_mess(world, hero, task, project.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you {task.verb}, your {project.label} will get {task.soil}," '
        f"{hero.pronoun('possessive')} {parent.label_word} said softly."
    )
    return True


def invite_friend(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 0.5
    friend.memes["helpfulness"] += 1
    world.say(f"{friend.id} came over and said, \"I'll help you.\"")


def little_problem(world: World, hero: Entity, task: Task) -> None:
    hero.memes["frustration"] += 1
    world.say(f"{hero.id} tried to {task.rush}, but the work was trickier than it looked.")


def compromise(world: World, parent: Entity, hero: Entity, task: Task, project: Entity) -> Optional[Gear]:
    gear_def = select_gear(task, project)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, task, project.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} smiled and said, "
        f"\"How about we {gear_def.prep} and do it together?\""
    )
    return gear_def


def accept(world: World, hero: Entity, friend: Entity, parent: Entity, task: Task, project: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0
    friend.memes["joy"] += 1
    world.say(f"{hero.id} grinned and nodded, and {friend.id} picked up the other side of the work.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} and {friend.id} were {task.gerund}, "
        f"and the {project.label} stayed clean and safe."
    )
    world.say(f"At the end, {hero.id}'s {parent.label_word} gave both friends a proud hug.")


def tell(
    setting: Setting,
    task: Task,
    project_cfg: Project,
    hero_name: str = "Ava",
    friend_name: str = "Mia",
    hero_type: str = "girl",
    parent_type: str = "mother",
    hero_traits: Optional[list[str]] = None,
) -> World:
    world = World(setting)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little"] + (hero_traits or ["kind", "helpful"]),
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type="girl" if friend_name in {"Mia", "Lila", "Zoe", "Iris", "Luna"} else "boy",
            traits=["little", "kind"],
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    project = world.add(
        Entity(
            id="project",
            type=project_cfg.type,
            label=project_cfg.label,
            phrase=project_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=project_cfg.region,
            plural=project_cfg.plural,
        )
    )

    intro(world, hero)
    love_story(world, hero, friend, task)
    bring_project(world, parent, hero, project)

    world.para()
    want_to_work(world, hero, task, setting.place)
    warn(world, parent, hero, task, project)
    invite_friend(world, hero, friend)
    little_problem(world, hero, task)

    world.para()
    gear_def = compromise(world, parent, hero, task, project)
    if gear_def:
        accept(world, hero, friend, parent, task, project, gear_def)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        project=project,
        task=task,
        setting=setting,
        gear=gear_def,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "concrete": [
        (
            "What is concrete?",
            "Concrete is a hard building material made by mixing cement, sand, gravel, and water. It starts soft and then becomes strong.",
        )
    ],
    "gloves": [
        (
            "Why do people wear work gloves?",
            "Work gloves help protect hands from dirt, rough surfaces, and messy materials while people work.",
        )
    ],
    "apron": [
        (
            "What does an apron do?",
            "An apron covers your clothes so they stay cleaner when you cook, paint, or do messy work.",
        )
    ],
    "boots": [
        (
            "Why wear rubber boots?",
            "Rubber boots help keep your feet dry and clean when the ground is wet or messy.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and do a job together so it becomes easier and better.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people care about each other, spend time together, and try to help one another.",
        )
    ],
}

KNOWLEDGE_ORDER = ["concrete", "gloves", "apron", "boots", "teamwork", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, task, project = f["hero"], f["friend"], f["task"], f["project"]
    return [
        f'Write a heartwarming short story for a child about "{task.keyword}" and a {project.label}.',
        f"Tell a gentle story where {hero.id} and {friend.id} work together on {task.verb} and keep {hero.pronoun('possessive')} {project.label} clean.",
        f'Write a simple friendship story that includes the word "{task.keyword}" and ends with teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, parent, task, project = f["hero"], f["friend"], f["parent"], f["task"], f["project"]
    place = f["setting"].place
    trait = next((t for t in hero.traits if t != "little"), "kind")
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} and {friend.id} go to {place}?",
            answer=f"It is about {hero.id}, a little {trait} {hero.type}, and {friend.id}, who helps as a good friend.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {project.label}?",
            answer=f"{hero.id} wanted to {task.verb} while keeping the {project.label} safe and clean.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label_word} speak up?",
            answer=f"{parent.label_word} worried the {project.label} would get {task.soil} if they worked without being careful.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id}?",
            answer=f"{friend.id} came over, offered help, and made the job feel like teamwork instead of a hard problem.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the story?",
                answer=f"The {gear.label} kept {hero.id}'s {project.label} safe while they worked on {task.verb}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["task"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_at_risk(T, P) :- zone(T, R), region(P, R).
protects(G, T, P) :- gear(G), task_at_risk(T, P), mess(T, M), guards(G, M), covers(G, R), region(P, R).
has_fix(T, P) :- protects(_, T, P).
valid(Place, T, P) :- affords(Place, T), task_at_risk(T, P), has_fix(T, P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("project_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
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
# Params / generation / emit
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="driveway", task="mix", project="apron", name="Ava", friend="Mia", parent="mother", trait="kind"),
    StoryParams(place="garden", task="patch", project="boots", name="Leo", friend="Owen", parent="father", trait="helpful"),
    StoryParams(place="workshop", task="mix", project="gloves", name="Iris", friend="Nina", parent="mother", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming concrete teamwork story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.project:
        task, proj = TASKS[args.task], PROJECTS[args.project]
        if not (task_at_risk(task, proj) and select_gear(task, proj)):
            raise StoryError(explain_rejection(task, proj))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.project is None or c[2] == args.project)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task_id, project_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES if gender == "girl" else CHILD_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, project=project_id, name=name, friend=friend, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        PROJECTS[params.project],
        hero_name=params.name,
        friend_name=params.friend,
        parent_type=params.parent,
        hero_traits=[params.trait, "stubborn"],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for row in triples:
            print(" ", row)
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
            header = f"### {p.name}: {p.task} at {p.place} (project: {p.project})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
