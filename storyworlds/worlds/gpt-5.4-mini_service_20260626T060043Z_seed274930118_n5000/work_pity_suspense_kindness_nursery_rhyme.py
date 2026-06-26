#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/work_pity_suspense_kindness_nursery_rhyme.py
============================================================================================================================

A tiny nursery-rhyme story world about work, pity, suspense, and kindness.

Source tale shape, imagined from the seed:
- A small child sees a tired worker trying to finish a chore.
- The child feels pity, waits in suspense, and chooses kindness.
- The helpful act eases the work, and the ending image shows the change.

This world is intentionally small and constraint-checked. It builds a live
simulation with physical meters and emotional memes, then renders prose from
that state.
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
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    strain: str
    ending: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
    id: str
    verb: str
    result: str
    gift: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.turn: str = ""

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.turn = self.turn
        return w


def _story_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _story_mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def add_meter(e: Entity, key: str, value: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + value


def add_mem(e: Entity, key: str, value: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + value


def task_at_risk(task: Task, place: Setting) -> bool:
    return task.id in place.affords


def choose_kind(task: Task) -> Optional[KindAct]:
    for k in KIND_ACTS:
        if task.id in k.tags:
            return k
    return None


def predict_turn(world: World, child: Entity, worker: Entity, task: Task) -> dict:
    sim = world.copy()
    do_work(sim, sim.get(child.id), sim.get(worker.id), task, narrate=False)
    return {
        "too_hard": _story_meter(sim.get(worker.id), "strain") >= THRESHOLD,
        "helped": _story_meter(sim.get(worker.id), "kindness") >= THRESHOLD,
    }


def do_work(world: World, child: Entity, worker: Entity, task: Task, narrate: bool = True) -> None:
    if not task_at_risk(task, world.setting):
        raise StoryError("That task does not fit this setting.")
    worker.meters["work"] = worker.meters.get("work", 0.0) + 1
    worker.meters["strain"] = worker.meters.get("strain", 0.0) + 1
    add_mem(child, "pity", 1)
    world.turn = task.id
    if narrate:
        world.say(f"{worker.label} kept on with {task.gerund}, though the load was heavy.")


def suspense_beats(world: World, child: Entity, worker: Entity, task: Task) -> None:
    add_mem(child, "suspense", 1)
    world.say(
        f"{child.label} watched in suspense, for {worker.label} had one more {task.keyword} to move."
    )
    world.say(
        f"The little heart felt pity, as still as a pearl, and waited to see what would be done."
    )


def offer_kindness(world: World, child: Entity, worker: Entity, task: Task, act: KindAct) -> None:
    add_mem(child, "kindness", 1)
    add_mem(worker, "relief", 1)
    worker.meters["strain"] = max(0.0, worker.meters.get("strain", 0.0) - 1)
    worker.meters["help"] = worker.meters.get("help", 0.0) + 1
    world.say(
        f"{child.label} said, \"Let me help you,\" and {act.verb} {act.gift}."
    )
    world.say(
        f"{act.result}. Soon the work felt lighter, as soft as wool in the sun."
    )


def ending_image(world: World, child: Entity, worker: Entity, task: Task) -> None:
    if worker.meters.get("help", 0.0) >= THRESHOLD:
        world.say(
            f"And {child.label} and {worker.label} went on together, with {task.ending}, "
            f"while the path looked bright and neat."
        )
    else:
        world.say(
            f"And the day went slow and low, with the little one still thinking of the hard work."
        )


def build_scene(setting: Setting, task: Task, kind: KindAct,
                child_name: str = "Mina", child_type: str = "girl",
                worker_name: str = "Moss", worker_type: str = "mouse") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    worker = world.add(Entity(id=worker_name, kind="character", type=worker_type, label=worker_name))
    tool = world.add(Entity(id=f"{task.id}_thing", type="thing", label=task.keyword, phrase=task.keyword))
    tool.carries = worker.id

    world.say(f"At {setting.place}, {worker.label} was busy with {task.gerund}.")
    world.say(f"{child.label} saw the work and felt pity right away.")
    world.para()
    do_work(world, child, worker, task)
    suspense_beats(world, child, worker, task)
    world.say(f"The little one held still, wondering if kindness would come.")
    world.para()
    offer_kindness(world, child, worker, task, kind)
    ending_image(world, child, worker, task)

    world.facts.update(
        child=child, worker=worker, task=task, kind=kind, setting=setting,
        helped=worker.meters.get("help", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "lane": Setting(place="the little lane", affords={"baskets", "stones"}, mood="windy"),
    "garden": Setting(place="the garden gate", affords={"watering", "weeding"}, mood="bright"),
    "kitchen": Setting(place="the kitchen door", affords={"dishes", "baking"}, mood="warm"),
}

TASKS = {
    "baskets": Task(
        id="baskets",
        verb="carry the baskets",
        gerund="carrying baskets",
        rush="hurry with the baskets",
        strain="heavy and slow",
        ending="the baskets were stacked by the door",
        risk="the baskets might tumble",
        keyword="basket",
        tags={"baskets"},
    ),
    "weeding": Task(
        id="weeding",
        verb="pull the weeds",
        gerund="pulling weeds",
        rush="tug the weeds free",
        strain="tired and thorny",
        ending="the weeds were gone from the path",
        risk="the roots could snag",
        keyword="weed",
        tags={"weeding"},
    ),
    "watering": Task(
        id="watering",
        verb="water the flowers",
        gerund="watering flowers",
        rush="tip the pail too fast",
        strain="splashy and slippery",
        ending="the flowers stood tall and bright",
        risk="the pail might spill",
        keyword="pail",
        tags={"watering"},
    ),
    "dishes": Task(
        id="dishes",
        verb="wash the dishes",
        gerund="washing dishes",
        rush="scrub the plates quick",
        strain="soapy and long",
        ending="the cups shone like little moons",
        risk="the cups could slip",
        keyword="dish",
        tags={"dishes"},
    ),
    "baking": Task(
        id="baking",
        verb="stir the batter",
        gerund="stirring batter",
        rush="mix the bowl too fast",
        strain="sticky and sweet",
        ending="the cake rose golden and round",
        risk="the spoon might stick",
        keyword="bowl",
        tags={"baking"},
    ),
}

KIND_ACTS = [
    KindAct(id="help_lift", verb="helped lift", result="The load grew light", gift="the baskets", tags={"baskets"}),
    KindAct(id="help_pull", verb="helped pull", result="The roots came free", gift="the weeds", tags={"weeding"}),
    KindAct(id="help_pour", verb="helped pour", result="The flowers drank their fill", gift="the water", tags={"watering"}),
    KindAct(id="dry", verb="helped dry", result="The dishes sparkled", gift="the towels", tags={"dishes"}),
    KindAct(id="stir", verb="helped stir", result="The batter became smooth", gift="the spoon", tags={"baking"}),
]

CHILD_NAMES = ["Mina", "Pia", "Nell", "Luna", "Tia"]
WORKER_NAMES = ["Moss", "Pip", "Willow", "Hugo", "Fern"]


@dataclass
class StoryParams:
    place: str
    task: str
    kind: str
    child_name: str
    child_type: str
    worker_name: str
    worker_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for kind in KIND_ACTS:
                if task_id in kind.tags:
                    combos.append((place, task_id, kind.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about "work" and "pity" at {f["setting"].place}.',
        f"Tell a gentle story where {f['child'].label} sees {f['worker'].label} doing {f['task'].gerund} and chooses kindness.",
        f'Write a child-friendly rhyme that uses the words "work" and "pity" and ends with a helpful turn.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, worker, task, kind = f["child"], f["worker"], f["task"], f["kind"]
    return [
        QAItem(
            question=f"Who was doing the {task.keyword} work at {world.setting.place}?",
            answer=f"{worker.label} was doing the work, and {child.label} watched with pity and care.",
        ),
        QAItem(
            question=f"Why did {child.label} wait in suspense before helping?",
            answer=f"{child.label} waited in suspense because the work looked hard, and the little one wanted to see if kindness was needed.",
        ),
        QAItem(
            question=f"What did {child.label} do to help {worker.label}?",
            answer=f"{child.label} chose kindness and {kind.verb} {kind.gift}, which made the task easier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is doing something gentle and helpful for someone else.",
        ),
        QAItem(
            question="What is pity?",
            answer="Pity is the soft feeling you get when you see someone having a hard time and wish to help.",
        ),
        QAItem(
            question="Why can work feel tiring?",
            answer="Work can feel tiring because it asks the body to keep going, lift, carry, or sort for a long time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that could make this story ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions -- child-level knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lane", "baskets", "help_lift", "Mina", "girl", "Moss", "mouse"),
    StoryParams("garden", "weeding", "help_pull", "Luna", "girl", "Willow", "mouse"),
    StoryParams("garden", "watering", "help_pour", "Pia", "girl", "Fern", "mouse"),
    StoryParams("kitchen", "dishes", "dry", "Nell", "girl", "Hugo", "mouse"),
    StoryParams("kitchen", "baking", "stir", "Tia", "girl", "Pip", "mouse"),
]


def explain_rejection(task: Task, kind: KindAct) -> str:
    return f"(No story: the kindness move '{kind.id}' does not fit the work '{task.id}' in this tiny world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small nursery-rhyme story world about work, pity, suspense, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--kind", choices=[k.id for k in KIND_ACTS])
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--worker-name")
    ap.add_argument("--worker-type", choices=["mouse", "hen", "fox"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.kind:
        combos = [c for c in combos if c[2] == args.kind]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, kind = rng.choice(sorted(combos))
    child_type = args.child_type or "girl"
    worker_type = args.worker_type or rng.choice(["mouse", "hen", "fox"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    worker_name = args.worker_name or rng.choice(WORKER_NAMES)
    return StoryParams(
        place=place,
        task=task,
        kind=kind,
        child_name=child_name,
        child_type=child_type,
        worker_name=worker_name,
        worker_type=worker_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_scene(
        SETTINGS[params.place],
        TASKS[params.task],
        next(k for k in KIND_ACTS if k.id == params.kind),
        params.child_name,
        params.child_type,
        params.worker_name,
        params.worker_type,
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


ASP_RULES = r"""
work_task(T) :- task(T).
kind_fit(K,T) :- kind(K), task(T), fit(K,T).
valid(Place, T, K) :- affords(Place, T), kind_fit(K, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", place, t))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for k in KIND_ACTS:
        lines.append(asp.fact("kind", k.id))
        for t in sorted(k.tags):
            lines.append(asp.fact("fit", k.id, t))
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
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
