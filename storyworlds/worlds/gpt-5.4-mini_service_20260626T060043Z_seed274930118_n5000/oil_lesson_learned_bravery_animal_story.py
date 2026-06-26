#!/usr/bin/env python3
"""
storyworlds/worlds/oil_lesson_learned_bravery_animal_story.py
=============================================================

A small animal-story world about bravery, a slippery problem, and a lesson
learned.

Premise:
- A young animal wants to do a helpful job.
- The job needs a little oil to make something work again.
- The hero feels nervous at first because oil is slick and strange.
- With a kind helper and a careful plan, the hero gets brave, solves the
  problem, and learns that trying a hard thing can be worth it.

The world is intentionally tiny and constraint-checked:
- the story is always grounded in a live simulation state;
- the ending changes the hero's emotions and the object's physical state;
- invalid combinations raise StoryError with a clear explanation.

The domain keeps the gentle, concrete feel of an animal story.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        by_type = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "bear": {"subject": "he", "object": "him", "possessive": "his"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
            "otter": {"subject": "they", "object": "them", "possessive": "their"},
            "badger": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return by_type.get(self.type, {"subject": "it", "object": "it", "possessive": "its"}).get(case, "it")

    def it(self) -> str:
        return "them" if self.type in {"otter", "badger"} else "it"


@dataclass
class Place:
    name: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    problem: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    use_line: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.last_tool: Optional[Tool] = None

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.last_tool = self.last_tool
        return w


PLACES = {
    "barn": Place("the barn", supports={"oil"}),
    "shed": Place("the shed", supports={"oil"}),
    "workshop": Place("the workshop", supports={"oil"}),
    "dock": Place("the dock", supports={"oil"}),
}

TASKS = {
    "wheel": Task(
        id="wheel",
        verb="fix the squeaky wheel",
        gerund="fixing the squeaky wheel",
        problem="it kept making a loud squeal",
        risk="the wheel would stay stuck",
        keyword="oil",
        tags={"oil", "help", "noise"},
    ),
    "door": Task(
        id="door",
        verb="quiet the stubborn door",
        gerund="quieting the stubborn door",
        problem="it creaked and stuck every time it moved",
        risk="the door would not open smoothly",
        keyword="oil",
        tags={"oil", "help", "door"},
    ),
    "hinge": Task(
        id="hinge",
        verb="smooth the rusty hinge",
        gerund="smoothing the rusty hinge",
        problem="it grumbled whenever the gate swung shut",
        risk="the gate would keep complaining",
        keyword="oil",
        tags={"oil", "help", "gate"},
    ),
}

TOOLS = {
    "oil_can": Tool(
        id="oil_can",
        label="a tiny oil can",
        phrase="a tiny oil can with a shiny spout",
        helps="oil the stuck part carefully",
        use_line="With a careful tilt, the oil slid exactly where it was needed.",
    ),
    "rag": Tool(
        id="rag",
        label="a soft rag",
        phrase="a soft rag for wiping spills",
        helps="wipe away extra oil",
        use_line="The rag caught the extra drops before they could spread.",
    ),
    "funnel": Tool(
        id="funnel",
        label="a little funnel",
        phrase="a little funnel to guide the oil",
        helps="pour the oil neatly",
        use_line="The funnel kept the oil from wobbling all over the floor.",
    ),
}

HERO_NAMES = ["Milo", "Pip", "Tara", "Nina", "Bram", "Penny", "Daisy", "Toby"]
HERO_TYPES = ["fox", "rabbit", "otter", "mouse", "badger"]
HELPERS = ["grandma", "grandpa", "uncle", "aunt", "older sibling", "neighbor"]
TRAITS = ["careful", "curious", "brave", "small", "gentle", "helpful"]


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    animal: str
    helper: str
    trait: str
    seed: Optional[int] = None


def can_do(task: Task, place: Place) -> bool:
    return "oil" in place.supports and task.keyword == "oil"


def explain_invalid(task: Task, place: Place) -> str:
    if "oil" not in place.supports:
        return f"(No story: {place.name} is not a good place for an oil job.)"
    return f"(No story: the task {task.id} does not fit this little oil lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="An animal story about bravery, oil, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if can_do(task, place):
                combos.append((place_id, task_id))
    if args.place and args.task:
        if not can_do(TASKS[args.task], PLACES[args.place]):
            raise StoryError(explain_invalid(TASKS[args.task], PLACES[args.place]))
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, name=name, animal=animal, helper=helper, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, meters={"nervous": 0.0}, memes={"bravery": 0.0, "joy": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper, meters={}, memes={"kindness": 1.0}))
    task = TASKS[params.task]
    object_ = world.add(Entity(id="task", kind="thing", type=task.id, label=task.id, phrase=task.problem, caretaker=helper.id, meters={"stuck": 1.0}))
    world.facts.update(hero=hero, helper=helper, task=task, object=object_, params=params)
    return world


def predict_success(world: World, tool: Tool) -> bool:
    sim = world.copy()
    obj = sim.get("task")
    if tool.id == "oil_can":
        obj.meters["stuck"] = max(0.0, obj.meters["stuck"] - 1.0)
    return obj.meters["stuck"] < THRESHOLD


def narrate_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    params: StoryParams = f["params"]

    hero.memes["love_help"] = 1.0
    world.say(f"{hero.id} was a {params.trait} {hero.type} who loved helping around {world.place.name}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {task.verb}, but {task.problem}.")

    world.para()
    hero.memes["nervous"] = 1.0
    world.say(f"{hero.id} stared at the jar of oil and took a tiny step back.")
    world.say(f"{hero.pronoun().capitalize()} worried that the oil might slip away or make a mess.")

    world.para()
    tool = TOOLS["oil_can"]
    world.last_tool = tool
    if predict_success(world, tool):
        world.say(f"{helper.label.capitalize()} smiled and said, 'We can do this gently. Bravery means trying.'")
        world.say(f"{hero.id} took {tool.phrase} and listened closely.")
        world.say(tool.use_line)
        obj = world.get("task")
        obj.meters["stuck"] = 0.0
        obj.meters["oiled"] = 1.0
        hero.memes["bravery"] += 1.0
        hero.memes["nervous"] = 0.0
        hero.memes["joy"] += 1.0
        world.say(f"The squeak faded away at last.")
        world.say(f"{hero.id} grinned. {hero.pronoun().capitalize()} had been brave, and the hard job worked.")
    else:
        raise StoryError("The story setup failed to find a believable oil solution.")

    world.para()
    world.say(f"After that, {hero.id} learned that a scary-looking job can feel easier with a calm helper.")
    world.say(f"{hero.pronoun().capitalize()} also learned that a little oil can help things move again, if it is used carefully.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who was the brave animal in the story?",
            answer=f"The brave animal was {hero.id}, a {params.trait} {hero.type}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} want to solve?",
            answer=f"{hero.id} wanted to {task.verb}, because {task.problem}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} feel brave?",
            answer=f"{helper.label.capitalize()} helped by staying calm and showing {hero.id} how to be careful.",
        ),
        QAItem(
            question=f"What did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that bravery means trying a hard thing carefully, and that oil can help a stuck part move again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is oil used for in simple machines?",
            answer="Oil can help moving parts slide or turn more smoothly when they are stuck or squeaky.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means trying to do something even when you feel a little scared.",
        ),
        QAItem(
            question="Why is oil handled carefully?",
            answer="Oil is slippery, so it can make a spill if it is poured too quickly.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    task: Task = f["task"]
    return [
        f"Write a short animal story about {hero.id}, bravery, and a small oil job.",
        f"Tell a gentle story where {hero.id} wants to {task.verb} but feels nervous about the oil.",
        f"Write a child-friendly story with a helper, a squeaky problem, and a lesson learned.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P).
task_ok(T) :- task(T).

valid(P,T) :- place_ok(P), task_ok(T), supports(P,oil), wants_oil(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "oil" in place.supports:
            lines.append(asp.fact("supports", pid, "oil"))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        if task.keyword == "oil":
            lines.append(asp.fact("wants_oil", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t) for p in PLACES for t in TASKS if can_do(TASKS[t], PLACES[p])}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    narrate_story(world)
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
    StoryParams(place="barn", task="wheel", name="Milo", animal="fox", helper="grandpa", trait="brave"),
    StoryParams(place="shed", task="door", name="Pip", animal="rabbit", helper="aunt", trait="careful"),
    StoryParams(place="workshop", task="hinge", name="Tara", animal="otter", helper="older sibling", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible (place, task) combos:\n")
        for p, t in vals:
            print(f"  {p:10} {t}")
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
