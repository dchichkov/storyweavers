#!/usr/bin/env python3
"""
storyworlds/worlds/structure_teamwork_fable.py
==============================================

A small fable-style storyworld about teamwork and structure.

Premise:
- A small animal wants to build a structure.
- The work is too hard to do alone.
- Neighbors help in different ways.
- Together they finish a sturdy little structure, and everyone feels proud.

The world is modeled with physical meters and emotional memes, so the story
is driven by simulated state rather than fixed prose.
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
    role: str = ""
    owner: Optional[str] = None
    helper_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "squirrel", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    structure: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    difficulty: str
    progress_key: str
    risk_key: str
    requires: set[str]
    needs: int
    result_phrase: str
    keyword: str = "structure"


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    boost: float
    phrase: str


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper1: str
    helper2: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_slow_progress(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("work", 0) < THRESHOLD:
            continue
        if ent.meters.get("progress", 0) >= THRESHOLD:
            continue
        sig = ("progress", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["progress"] = ent.meters.get("progress", 0) + 0.5
        out.append(f"{ent.name_or_label()} kept working, but the job still moved slowly.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character" and e.role == "hero"), None)
    if hero is None:
        return out
    helpers = [e for e in world.entities.values() if e.kind == "character" and e.role == "helper"]
    if hero.memes.get("hope", 0) < THRESHOLD:
        return out
    support = sum(h.meters.get("help", 0) for h in helpers)
    if support < 2 * THRESHOLD:
        return out
    sig = ("teamwork", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["progress"] = max(hero.meters.get("progress", 0), 1.5)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    out.append("__teamwork__")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character" and e.role == "hero"), None)
    if hero is None:
        return out
    if hero.meters.get("progress", 0) < 1.5:
        return out
    sig = ("finish", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["done"] = 1
    out.append(f"The structure stood firm at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_slow_progress, _r_teamwork, _r_finish):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__teamwork__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "hill": Setting(place="the hill", structure="stone wall", affords={"build"}),
    "riverbank": Setting(place="the riverbank", structure="small bridge", affords={"build"}),
    "grove": Setting(place="the grove", structure="leaf hut", affords={"build"}),
}

TASKS = {
    "wall": Task(
        id="wall",
        verb="build a stone wall",
        gerund="building a stone wall",
        difficulty="heavy and slow",
        progress_key="stones",
        risk_key="collapse",
        requires={"carry", "stack", "steady"},
        needs=3,
        result_phrase="a sturdy stone wall",
        keyword="structure",
    ),
    "bridge": Task(
        id="bridge",
        verb="build a small bridge",
        gerund="building a small bridge",
        difficulty="wide and wobbly",
        progress_key="planks",
        risk_key="gap",
        requires={"carry", "hold", "tie"},
        needs=3,
        result_phrase="a neat little bridge",
        keyword="structure",
    ),
    "hut": Task(
        id="hut",
        verb="build a leaf hut",
        gerund="building a leaf hut",
        difficulty="tall and tippy",
        progress_key="bundles",
        risk_key="wind",
        requires={"gather", "weave", "pin"},
        needs=3,
        result_phrase="a cozy leaf hut",
        keyword="structure",
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="a rope", helps={"tie", "hold"}, boost=1.0, phrase="tie the parts together"),
    "plank": Tool(id="plank", label="a plank", helps={"carry", "stack"}, boost=1.0, phrase="carry a strong piece"),
    "leafbundle": Tool(id="leafbundle", label="a bundle of leaves", helps={"gather", "weave"}, boost=1.0, phrase="weave the roof"),
}

ANIMALS = {
    "milo": ("Milo", "mouse"),
    "nina": ("Nina", "rabbit"),
    "pip": ("Pip", "squirrel"),
    "toby": ("Toby", "bird"),
    "luna": ("Luna", "mouse"),
    "otto": ("Otto", "rabbit"),
}

HELPERS = list(ANIMALS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable storyworld about teamwork and structure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper1", choices=HELPERS)
    ap.add_argument("--helper2", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    hero = args.hero or rng.choice(list(ANIMALS))
    helper_pool = [k for k in HELPERS if k != hero]
    helper1 = args.helper1 or rng.choice(helper_pool)
    helper_pool2 = [k for k in helper_pool if k != helper1]
    helper2 = args.helper2 or rng.choice(helper_pool2)
    if len({hero, helper1, helper2}) < 3:
        raise StoryError("The hero and two helpers must be different characters.")
    return StoryParams(place=place, task=task, hero=hero, helper1=helper1, helper2=helper2)


def introduce(world: World, hero: Entity, task: Task) -> None:
    world.say(
        f"{hero.name_or_label()} was a small {hero.type} who wanted to {task.verb}."
    )
    world.say(
        f"{hero.name_or_label()} believed a good {task.keyword} should be built with care."
    )


def struggle(world: World, hero: Entity, task: Task) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"At first, {hero.name_or_label()} worked alone, but the task was {task.difficulty}."
    )
    world.say(
        f"Each step only added a little progress, and the {task.risk_key} still seemed near."
    )
    hero.meters["work"] = hero.meters.get("work", 0) + 1
    hero.meters["progress"] = hero.meters.get("progress", 0) + 0.5
    propagate(world)


def ask_for_help(world: World, hero: Entity, helper1: Entity, helper2: Entity, task: Task) -> None:
    world.para()
    world.say(
        f"{hero.name_or_label()} looked at the half-made {task.keyword} and called for help."
    )
    world.say(
        f"{helper1.name_or_label()} came with a {TOOLS['plank'].label}, and {helper2.name_or_label()} came ready to work too."
    )
    hero.memes["hope"] += 1
    helper1.meters["help"] = helper1.meters.get("help", 0) + 1
    helper2.meters["help"] = helper2.meters.get("help", 0) + 1
    helper1.memes["kindness"] = helper1.memes.get("kindness", 0) + 1
    helper2.memes["kindness"] = helper2.memes.get("kindness", 0) + 1


def teamwork_action(world: World, hero: Entity, helper1: Entity, helper2: Entity, task: Task) -> None:
    helper1.meters["help"] = helper1.meters.get("help", 0) + 1
    helper2.meters["help"] = helper2.meters.get("help", 0) + 1
    hero.meters["work"] = hero.meters.get("work", 0) + 1
    hero.meters["progress"] = hero.meters.get("progress", 0) + 1
    world.say(
        f"One helper carried the heavy parts, while the other held them steady."
    )
    world.say(
        f"Together they kept {task.result_phrase} from wobbling."
    )
    propagate(world)


def finish_story(world: World, hero: Entity, helper1: Entity, helper2: Entity, task: Task) -> None:
    world.para()
    if hero.meters.get("done", 0) >= THRESHOLD:
        world.say(
            f"In the end, {task.result_phrase} stood ready for all of them to use."
        )
        world.say(
            f"{hero.name_or_label()} smiled because the best {task.keyword} was the one they built together."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        helper1.memes["pride"] = helper1.memes.get("pride", 0) + 1
        helper2.memes["pride"] = helper2.memes.get("pride", 0) + 1


def tell(setting: Setting, task: Task, hero_name: str, helper1_name: str, helper2_name: str) -> World:
    world = World(setting)
    hero_label, hero_type = ANIMALS[hero_name]
    h1_label, h1_type = ANIMALS[helper1_name]
    h2_label, h2_type = ANIMALS[helper2_name]

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_label, role="hero"))
    helper1 = world.add(Entity(id=helper1_name, kind="character", type=h1_type, label=h1_label, role="helper"))
    helper2 = world.add(Entity(id=helper2_name, kind="character", type=h2_type, label=h2_label, role="helper"))

    world.facts.update(hero=hero, helper1=helper1, helper2=helper2, task=task, setting=setting)

    introduce(world, hero, task)
    struggle(world, hero, task)
    ask_for_help(world, hero, helper1, helper2, task)
    teamwork_action(world, hero, helper1, helper2, task)
    finish_story(world, hero, helper1, helper2, task)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f'Write a short fable for children about "{task.keyword}" and teamwork.',
        f"Tell a gentle story where {hero.name_or_label()} tries to {task.verb} and learns to ask for help.",
        f"Write a simple moral story about a {task.keyword} that becomes stronger when friends work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    h1 = f["helper1"]
    h2 = f["helper2"]
    task = f["task"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who wanted to {task.verb} in {setting.place}?",
            answer=f"{hero.name_or_label()} wanted to {task.verb} in {setting.place}.",
        ),
        QAItem(
            question=f"What made the work easier for {hero.name_or_label()}?",
            answer=f"The work became easier when {h1.name_or_label()} and {h2.name_or_label()} came to help.",
        ),
        QAItem(
            question=f"What did the friends build together?",
            answer=f"They built {task.result_phrase}.",
        ),
        QAItem(
            question=f"What lesson does the story show?",
            answer="It shows that teamwork helps a hard job get finished well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or animals work together and help one another reach a shared goal.",
        ),
        QAItem(
            question="What is a structure?",
            answer="A structure is something built from parts, like a wall, bridge, or hut.",
        ),
        QAItem(
            question="Why is it good to ask for help?",
            answer="Asking for help can make a hard job safer, faster, and stronger.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(Place, Task, Hero) :- setting(Place), task(Task), character(Hero), place_ok(Place, Task), hero_ok(Hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for cid in ANIMALS:
        lines.append(asp.fact("character", cid))
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            lines.append(asp.fact("place_ok", place, task_id))
    for cid in ANIMALS:
        lines.append(asp.fact("hero_ok", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t, h) for p in SETTINGS for t in TASKS for h in ANIMALS if p in SETTINGS and t in TASKS}
    asp_set = set(asp_valid())
    if asp_set == py:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_set - py))
    print("only in Python:", sorted(py - asp_set))
    return 1


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    hero = args.hero or rng.choice(list(ANIMALS))
    pool = [k for k in HELPERS if k != hero]
    helper1 = args.helper1 or rng.choice(pool)
    pool2 = [k for k in pool if k != helper1]
    helper2 = args.helper2 or rng.choice(pool2)
    if len({hero, helper1, helper2}) < 3:
        raise StoryError("The hero and helpers must be different.")
    return StoryParams(place=place, task=task, hero=hero, helper1=helper1, helper2=helper2)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    world = tell(setting, task, params.hero, params.helper1, params.helper2)
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
    StoryParams(place="hill", task="wall", hero="milo", helper1="nina", helper2="pip"),
    StoryParams(place="riverbank", task="bridge", hero="luna", helper1="otto", helper2="toby"),
    StoryParams(place="grove", task="hut", hero="nina", helper1="milo", helper2="pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible stories:")
        for item in triples:
            print(" ", item)
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
                params = build_story_params(args, random.Random(seed))
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
            header = f"### {p.hero} / {p.task} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
