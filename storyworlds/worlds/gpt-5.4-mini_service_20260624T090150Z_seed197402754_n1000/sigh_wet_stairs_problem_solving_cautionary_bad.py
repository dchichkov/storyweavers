#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/sigh_wet_stairs_problem_solving_cautionary_bad.py
==============================================================================================================

A small storyworld about a child on wet stairs, a careful warning, a problem
to solve, and a bad ending that still feels like a complete little adventure.

Seed tale:
---
Nia and her big brother were climbing the wet stairs behind the garden shed.
Nia carried a basket of cherries for their grandma. Halfway up, she slipped,
sighed, and hugged the railing. Her brother told her to slow down and wipe her
shoes first. Nia tried to balance the basket with both hands and take one step
at a time, but the stairs were slick. The basket tipped, the cherries rolled
down the steps, and Nia sat on the top stair with muddy knees, sighing again.
---

Story shape:
- Setup: a child, a task, and a wet stairway
- Cautionary turn: a warning about slick steps and a risky load
- Problem solving: the child tries a safer method
- Bad ending: the steps win anyway; the child is left disappointed and bruised
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the wet stairs"
    slippery: bool = True
    affords: set[str] = field(default_factory=lambda: {"carry", "climb"})


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    caution: str
    risk: str
    problem: str
    fix: str
    consequence: str
    keyword: str = "sigh"
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    type: str = "basket"
    plural: bool = False
    fragile: bool = True
    risky_on_wet_stairs: bool = True


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    helps: str
    protective: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "wet_stairs": Setting(place="the wet stairs", slippery=True),
    "garden_steps": Setting(place="the wet garden steps", slippery=True),
    "porch_steps": Setting(place="the porch stairs after rain", slippery=True),
}

TASKS = {
    "deliver": Task(
        id="deliver",
        verb="bring the basket up",
        gerund="carefully carrying the basket",
        caution="The stairs are slick",
        risk="the basket could tip and spill",
        problem="the child must carry a fragile load without slipping",
        fix="use both hands, slow down, and hold the rail",
        consequence="the cherries rolled down the steps",
        tags={"stairs", "wet", "sigh"},
    ),
    "lamp": Task(
        id="lamp",
        verb="carry the lamp upstairs",
        gerund="walking slowly with the lamp",
        caution="The glass lamp is easy to drop",
        risk="the lamp could crack on a hard step",
        problem="the child must climb without jostling the lamp",
        fix="keep one hand under the lamp and one on the rail",
        consequence="the lamp bumped a step and went dark",
        tags={"stairs", "wet", "sigh"},
    ),
    "tea": Task(
        id="tea",
        verb="take the tea tray up",
        gerund="balancing the tea tray",
        caution="Hot tea and wet steps do not mix",
        risk="the cups could splash and slide",
        problem="the child must keep the tray level",
        fix="pause on each step and steady the tray",
        consequence="the tea sloshed over the rim",
        tags={"stairs", "wet", "sigh"},
    ),
}

CARGOS = {
    "basket": Cargo(
        id="basket",
        label="basket of cherries",
        phrase="a basket full of cherries",
        type="basket",
        plural=False,
    ),
    "lamp": Cargo(
        id="lamp",
        label="glass lamp",
        phrase="a small glass lamp",
        type="lamp",
    ),
    "tea": Cargo(
        id="tea",
        label="tea tray",
        phrase="a tea tray with two cups",
        type="tray",
    ),
}

GEAR = {
    "rail": Gear(
        id="rail",
        label="the handrail",
        prep="grab the handrail",
        helps="steady the climb",
    ),
    "towel": Gear(
        id="towel",
        label="a dry towel",
        prep="wipe the shoes first",
        helps="keep the shoes from sliding",
    ),
    "bothhands": Gear(
        id="bothhands",
        label="both hands free",
        prep="set the load down and take a breath",
        helps="let the child climb more carefully",
    ),
}

NAMES = ["Nia", "Milo", "Sana", "Theo", "Lina", "Arlo", "Mina", "Jules"]
ADJ = ["brave", "small", "careful", "curious", "lively", "determined"]


def risk_exists(task: Task, cargo: Cargo) -> bool:
    return cargo.risky_on_wet_stairs


def select_help(task: Task, cargo: Cargo) -> Optional[Gear]:
    if task.id == "deliver":
        return GEAR["rail"]
    if task.id == "lamp":
        return GEAR["bothhands"]
    if task.id == "tea":
        return GEAR["rail"]
    return None


def explain_rejection(task: Task, cargo: Cargo) -> str:
    return f"(No story: {task.gerund} and {cargo.label} do not make a clear wet-stairs problem.)"


ASP_RULES = r"""
risk(task(T), cargo(C)) :- task(T), cargo(C), fragile(C), wet_stairs.
help(task(T), gear(G)) :- task(T), gear(G), can_use(T,G).
valid(T,C,G) :- risk(task(T), cargo(C)), help(task(T), gear(G)).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("wet_stairs"))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
    for c in CARGOS.values():
        lines.append(asp.fact("cargo", c.id))
        if c.fragile:
            lines.append(asp.fact("fragile", c.id))
    for g in GEAR.values():
        lines.append(asp.fact("gear", g.id))
    for t in TASKS.values():
        if t.id in {"deliver", "lamp", "tea"}:
            lines.append(asp.fact("can_use", t.id, "rail"))
        if t.id == "lamp":
            lines.append(asp.fact("can_use", t.id, "bothhands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    place: str
    task: str
    cargo: str
    name: str
    trait: str
    seed: Optional[int] = None


class StoryWorld(World):
    pass


def build_story(world: World, hero: Entity, helper: Entity, task: Task, cargo: Cargo, gear: Gear) -> None:
    hero.memes["hope"] = 1.0
    hero.memes["worry"] = 0.0
    cargo_ent = world.add(Entity(id="cargo", type=cargo.type, label=cargo.label, phrase=cargo.phrase, plural=cargo.plural))
    gear_ent = world.add(Entity(id="gear", type="gear", label=gear.label))

    world.say(f"{hero.id} was a {hero.type} who loved little adventures and noticed every sound on {world.setting.place}.")
    world.say(f"One afternoon, {hero.id} had to {task.verb} for {helper.label}.")
    world.say(f"{task.caution}, and {hero.id} let out a soft sigh before taking the first step.")
    world.para()
    world.say(f"{hero.id} looked at the {cargo.label} and knew the problem right away: {task.problem}.")
    world.say(f"{helper.id} pointed at the stairs and said, '{task.caution}. Slow steps are safer than fast ones.'")
    world.say(f"So {hero.id} tried to solve it by {task.fix}.")
    gear_ent.carried_by = hero.id
    hero.memes["caution"] = 1.0
    world.para()
    world.say(f"{hero.id} reached for {gear.label} and tried again, one careful step at a time.")
    world.say(f"But the stairs were wetter than they looked. {task.consequence.capitalize()}, and {hero.id} sighed.")
    cargo_ent.meters["damage"] = 1.0
    hero.meters["bruise"] = 1.0
    hero.memes["sadness"] = 1.0
    hero.memes["resolve"] = 0.5
    world.para()
    world.say(f"In the end, {hero.id} sat on a stair with damp knees while {helper.label} picked up the mess.")
    world.say(f"The little adventure ended badly, but the warning was true: wet stairs can win if you rush them.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, cargo = f["hero"], f["task"], f["cargo"]
    return [
        f'Write a short adventure story for a young child that includes the word "sigh" and a wet staircase.',
        f"Tell a cautionary story where {hero.id} tries to {task.verb} but the wet stairs make the problem hard.",
        f"Write a small problem-solving story about {cargo.label} on slippery stairs that ends badly but teaches care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    cargo: Cargo = f["cargo"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do on the wet stairs?",
            answer=f"{hero.id} was trying to {task.verb}. It was a small adventure with a careful job to do.",
        ),
        QAItem(
            question=f"Why did {hero.id} sigh before the climb got harder?",
            answer=f"{hero.id} sighed because the stairs were slippery and the load was fragile. {task.caution}.",
        ),
        QAItem(
            question=f"What smart idea did {hero.id} try to solve the problem?",
            answer=f"{hero.id} tried to solve it by {task.fix}. That was the careful part of the story.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {cargo.label}?",
            answer=f"It ended badly. {task.consequence.capitalize()}, and {hero.id} ended up tired and disappointed on the wet stairs.",
        ),
        QAItem(
            question=f"What did {gear.label} help with in the story?",
            answer=f"{gear.label} was supposed to help {hero.id} stay steady and make the climb safer, even though it did not stop the bad ending.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the stairs?",
            answer=f"{helper.label} gave the warning and reminded {hero.id} to go slowly because wet stairs are slippery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why are wet stairs dangerous?",
            answer="Wet stairs are dangerous because shoes can slip on the smooth water, and a person can fall if they hurry.",
        ),
        QAItem(
            question="Why should someone hold the rail on stairs?",
            answer="Holding the rail gives a hand to lean on, which helps keep a person steady while climbing.",
        ),
        QAItem(
            question="What does a sigh usually mean?",
            answer="A sigh is a long breath people often make when they feel worried, tired, or disappointed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {', '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    task_id = args.task or rng.choice(list(TASKS))
    cargo_id = args.cargo or rng.choice(list(CARGOS))
    task = TASKS[task_id]
    cargo = CARGOS[cargo_id]
    if not risk_exists(task, cargo):
        raise StoryError(explain_rejection(task, cargo))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(ADJ)
    return StoryParams(place=place, task=task_id, cargo=cargo_id, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Nia", "Sana", "Lina", "Mina"} else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type="father", label="the helper"))
    task = TASKS[params.task]
    cargo = CARGOS[params.cargo]
    gear = select_help(task, cargo) or GEAR["rail"]
    build_story(world, hero, helper, task, cargo, gear)
    world.facts.update(hero=hero, helper=helper, task=task, cargo=cargo, gear=gear)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary adventure on wet stairs.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def asp_verify() -> int:
    py = {(p, t, c) for p in SETTINGS for t in TASKS for c in CARGOS if risk_exists(TASKS[t], CARGOS[c])}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n")
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, (t, c) in enumerate((("deliver", "basket"), ("lamp", "lamp"), ("tea", "tea"))):
            params = StoryParams(place="wet_stairs", task=t, cargo=c, name=NAMES[i], trait=ADJ[i], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
