#!/usr/bin/env python3
"""
carbon_dialogue_humor_problem_solving_adventure.py

A small standalone story world about a child explorer, a carbon problem,
some light humor, and a careful solution.

The world is built around one simple adventure pattern:
- a hero wants to carry or use carbon for an important task,
- something makes the carbon risky to handle,
- the characters talk it through,
- they solve the problem with a sensible tool,
- the ending proves the carbon is safe and useful.

The prose is generated from simulated state, not from a fixed paragraph shell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "risk": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "humor": 0.0, "resolve": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class CarbonTask:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cave": Setting("the chalk cave", affords={"gather", "cross", "explore"}),
    "lab": Setting("the little science lab", indoors=True, affords={"mix", "test", "gather"}),
    "harbor": Setting("the windy harbor", affords={"cross", "gather"}),
    "forest": Setting("the forest trail", affords={"cross", "gather", "explore"}),
}

TASKS = {
    "gather": CarbonTask(
        id="gather",
        verb="gather carbon chips",
        gerund="gathering carbon chips",
        rush="dash after the black chips",
        hazard="windy",
        effect="scatter",
        keyword="carbon",
        tags={"carbon", "wind"},
    ),
    "mix": CarbonTask(
        id="mix",
        verb="mix carbon dust into the filter",
        gerund="mixing carbon dust",
        rush="stir the carbon too fast",
        hazard="bumpy",
        effect="spill",
        keyword="carbon",
        tags={"carbon", "dust"},
    ),
    "cross": CarbonTask(
        id="cross",
        verb="carry the carbon canister across the path",
        gerund="carrying the carbon canister",
        rush="run across the ridge with the carbon canister",
        hazard="windy",
        effect="blow open",
        keyword="carbon",
        tags={"carbon", "wind"},
    ),
    "explore": CarbonTask(
        id="explore",
        verb="explore for carbon markers",
        gerund="exploring for carbon markers",
        rush="peek into every dark nook",
        hazard="dark",
        effect="lose track of",
        keyword="carbon",
        tags={"carbon", "cave"},
    ),
    "test": CarbonTask(
        id="test",
        verb="test the carbon filter",
        gerund="testing the carbon filter",
        rush="tap the filter before it was ready",
        hazard="messy",
        effect="jam",
        keyword="carbon",
        tags={"carbon", "lab"},
    ),
}

CARGOS = {
    "sample_bag": Cargo(
        id="sample_bag",
        label="sample bag",
        phrase="a plain paper sample bag",
        region="hand",
        genders={"girl", "boy"},
    ),
    "canister": Cargo(
        id="canister",
        label="carbon canister",
        phrase="a small carbon canister with a loose lid",
        region="hand",
    ),
    "filter": Cargo(
        id="filter",
        label="carbon filter",
        phrase="a carbon filter for cleaning water",
        region="torso",
    ),
    "jar": Cargo(
        id="jar",
        label="carbon jar",
        phrase="a clear jar for carbon dust",
        region="hand",
    ),
}

GEAR = [
    Gear(
        id="tin",
        label="a snap-lid tin",
        prep="put the carbon in a snap-lid tin first",
        tail="sealed the tin with a happy click",
        guards={"wind", "dust"},
        covers={"hand"},
    ),
    Gear(
        id="strap",
        label="a cloth strap",
        prep="thread the canister through a cloth strap",
        tail="slung the canister safely over the shoulder",
        guards={"wind"},
        covers={"hand", "torso"},
    ),
    Gear(
        id="funnel",
        label="a wide funnel",
        prep="set a wide funnel under the jar",
        tail="kept the dust where it belonged",
        guards={"dust"},
        covers={"hand"},
    ),
]

GIRL_NAMES = ["Mina", "Lia", "Zoe", "Ava", "Nora", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Timo", "Eli", "Noah", "Finn"]
TRAITS = ["curious", "brave", "cheerful", "clever", "bouncy", "lively"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def task_is_risky(task: CarbonTask, cargo: Cargo) -> bool:
    return cargo.region in {"hand", "torso"} and task.keyword == "carbon"


def choose_gear(task: CarbonTask, cargo: Cargo) -> Optional[Gear]:
    for gear in GEAR:
        if any(tag in task.tags for tag in gear.guards) and cargo.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = TASKS[task_id]
            for cargo_id, cargo in CARGOS.items():
                if task_is_risky(task, cargo) and choose_gear(task, cargo):
                    out.append((place, task_id, cargo_id))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def foresee_problem(world: World, hero: Entity, task: CarbonTask, cargo: Entity) -> dict:
    sim = world.copy()
    simulate_task(sim, sim.get(hero.id), task, cargo, narrate=False)
    return {
        "mess": cargo.meters.get("mess", 0.0),
        "work": sum(e.meters.get("work", 0.0) for e in sim.characters()),
    }


def simulate_task(world: World, hero: Entity, task: CarbonTask, cargo: Entity, narrate: bool = True) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["risk"] += 1
    cargo.meters["mess"] += 1
    if task.hazard == "windy":
        cargo.meters["risk"] += 1
    if narrate:
        world.say(f"{hero.id} tried to {task.verb}, and the carbon looked ready to misbehave.")


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.memes if t == 'curiosity' or True)} adventurer who loved odd black things and bright ideas.")


def opening(world: World, hero: Entity, helper: Entity, cargo: Entity, task: CarbonTask) -> None:
    world.say(
        f"{hero.id} and {helper.label} set out for {world.setting.place} because they needed {cargo.phrase}."
    )
    world.say(
        f'{hero.id} smiled. "Carbon always looks like tiny night pieces," {hero.pronoun()} said. '
        f'{helper.pronoun().capitalize()} grinned back. "Then let us not let the night pieces escape," {helper.pronoun()} said.'
    )
    world.say(
        f"They wanted to {task.verb}, and {task.keyword} mattered for the trip."
    )


def warning(world: World, helper: Entity, hero: Entity, cargo: Entity, task: CarbonTask) -> None:
    forecast = foresee_problem(world, hero, task, cargo)
    if forecast["mess"] < THRESHOLD:
        return
    world.facts["predicted_mess"] = task.effect
    helper.memes["worry"] += 1
    world.say(
        f'"If we just rush in, the carbon will {task.effect}," {helper.label} said.'
    )
    world.say(
        f'"Then we will look like a chimney with shoes," {hero.id} joked.'
    )


def choice(world: World, hero: Entity, helper: Entity, cargo: Entity, task: CarbonTask) -> Optional[Gear]:
    gear = choose_gear(task, cargo)
    if gear is None:
        return None
    world.say(
        f'{helper.label} pointed at {gear.label} and said, "{gear.prep}."'
    )
    hero.memes["humor"] += 1
    return gear


def resolve(world: World, hero: Entity, helper: Entity, cargo: Entity, task: CarbonTask, gear: Gear) -> None:
    hero.memes["resolve"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    cargo.meters["mess"] = 0.0
    world.say(
        f'{hero.id} nodded. "That is the smartest tiny tin in the whole cave," {hero.pronoun()} said.'
    )
    world.say(
        f"{helper.label} laughed, then {gear.tail}. Soon {hero.id} could {task.verb} without the carbon getting loose."
    )
    world.say(
        f"In the end, the carbon stayed tidy, and the adventure moved forward with both of them smiling."
    )


def build_world(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    cargo = CARGOS[params.cargo]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"risk": 0.0, "mess": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "humor": 0.0, "resolve": 0.0, "curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_label,
        meters={"risk": 0.0, "mess": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "humor": 0.0, "resolve": 0.0, "curiosity": 0.0},
    ))
    item = world.add(Entity(
        id=cargo.id,
        type="thing",
        label=cargo.label,
        phrase=cargo.phrase,
        carried_by=hero.id,
        owner=hero.id,
        plural=cargo.plural,
        meters={"risk": 0.0, "mess": 0.0},
    ))

    intro(world, hero)
    world.para()
    opening(world, hero, helper, item, task)
    warning(world, helper, hero, item, task)
    world.para()
    gear = choice(world, hero, helper, item, task)
    if gear is None:
        raise StoryError("No reasonable carbon-gear match for this configuration.")
    resolve(world, hero, helper, item, task, gear)

    world.facts.update(
        hero=hero,
        helper=helper,
        cargo=item,
        task=task,
        gear=gear,
        place=params.place,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    cargo: str
    name: str
    gender: str
    helper_type: str
    helper_label: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("cave", "gather", "sample_bag", "Mina", "girl", "fox", "a fox guide", "curious"),
    StoryParams("harbor", "cross", "canister", "Leo", "boy", "uncle", "an uncle", "brave"),
    StoryParams("lab", "test", "filter", "Ava", "girl", "robot", "a robot helper", "clever"),
    StoryParams("forest", "explore", "jar", "Finn", "boy", "crow", "a crow guide", "lively"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "carbon": [
        ("What is carbon?", "Carbon is a real element found in things like charcoal, graphite, and living things."),
        ("Why can carbon be useful?", "Carbon can help clean water in filters and can also be part of pencils and fuel."),
    ],
    "wind": [
        ("Why does wind make loose things hard to carry?", "Wind can blow light things around, so a loose lid or open bag may spill."),
    ],
    "dust": [
        ("Why is dust hard to keep tidy?", "Dust is made of tiny bits, so it can puff up and spread when something bumps it."),
    ],
    "lab": [
        ("What do people do in a science lab?", "People test ideas in a science lab by mixing, measuring, and checking results carefully."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    task: CarbonTask = f["task"]
    cargo: Entity = f["cargo"]
    return [
        f'Write a short adventure story for a child about {hero.id} and carbon.',
        f"Tell a story where {hero.id} wants to {task.verb} but must solve a carbon problem first.",
        f'Create a funny, gentle tale that includes dialogue and the word "carbon" and ends with a smart fix for {cargo.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: CarbonTask = f["task"]
    cargo: Entity = f["cargo"]
    gear: Gear = f["gear"]

    return [
        QAItem(
            question=f"What did {hero.id} want to do with the carbon?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think of a safer plan?",
            answer=f"{helper.label} helped {hero.id} think of a safer plan.",
        ),
        QAItem(
            question=f"What solved the carbon problem?",
            answer=f"{gear.label} solved the problem by keeping the carbon safe and tidy.",
        ),
        QAItem(
            question=f"Why was the carbon tricky at first?",
            answer=f"It was tricky because loose carbon could {task.effect} if they rushed.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and proud because the carbon stayed under control.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    if world.facts.get("gear"):
        tags |= set(world.facts["gear"].guards)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_risky(T,C) :- task(T), cargo(C), cargo_region(C,R), task_tag(T,carbon), cargo_region(C,R).

gear_fits(G,T,C) :- gear(G), task(T), cargo(C), cargo_region(C,R), covers(G,R), guards(G,carbon), task_tag(T,carbon).
valid(Place,T,C) :- affords(Place,T), task_risky(T,C), gear_fits(G,T,C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if s.indoors:
            lines.append(asp.fact("indoors", place))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", place, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_tag", tid, "carbon"))
        lines.append(asp.fact("task_tag", tid, t.hazard))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_region", cid, c.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
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
    print("MISMATCH between clingo and python valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A carbon-themed adventure world with dialogue, humor, and problem solving.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--cargo", choices=sorted(CARGOS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-type", choices=["fox", "crow", "robot", "uncle"], dest="helper_type")
    ap.add_argument("--helper-label")
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
    if args.task and args.cargo:
        task = TASKS[args.task]
        cargo = CARGOS[args.cargo]
        if not (task_is_risky(task, cargo) and choose_gear(task, cargo)):
            raise StoryError("That carbon task and cargo combination has no reasonable fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("No valid carbon adventure matches the given options.")
    place, task, cargo = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["fox", "crow", "robot", "uncle"])
    helper_label = args.helper_label or {"fox": "a fox guide", "crow": "a crow guide", "robot": "a robot helper", "uncle": "an uncle"}[helper_type]
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, task, cargo, name, gender, helper_type, helper_label, trait)


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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, cargo) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.task} at {p.place} with {p.cargo}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
