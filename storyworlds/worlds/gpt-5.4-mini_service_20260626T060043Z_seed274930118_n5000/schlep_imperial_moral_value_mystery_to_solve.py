#!/usr/bin/env python3
"""
A folk-tale storyworld about a small, stubborn mystery and a moral choice.

Premise:
A child or helper must schlep a heavy parcel to the imperial hall, but along
the road a mystery appears: a missing token, a wrong label, or a hidden owner.
The story turns on whether the traveler tells the truth, helps someone in need,
or chooses the kind road over the easy road.

This script keeps the domain small and constraint-checked:
- one setting
- one travel task
- one mystery object
- one moral value at stake
- one resolved ending image
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Task:
    action: str
    gerund: str
    burden: str
    path: str
    cost: str
    keyword: str = "schlep"


@dataclass
class Mystery:
    label: str
    phrase: str
    clue: str
    reveal: str
    moral: str
    value: str


@dataclass
class StoryParams:
    place: str
    task: str
    mystery: str
    value: str
    name: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "village": Setting(place="the old village road", features={"road", "market", "well", "inn"}),
    "bridge": Setting(place="the stone bridge", features={"road", "river", "bank"}),
    "courtyard": Setting(place="the imperial courtyard", features={"hall", "gate", "steps"}),
}

TASKS = {
    "schlep": Task(
        action="schlep the heavy basket",
        gerund="schlepping the heavy basket",
        burden="the basket was heavy enough to make arms ache",
        path="the road to the imperial hall",
        cost="it would be quicker to drop it and run",
        keyword="schlep",
    ),
    "carry": Task(
        action="carry the wrapped parcel",
        gerund="carrying the wrapped parcel",
        burden="the parcel had a square stone tucked in its base",
        path="the path to the imperial gate",
        cost="it would be quicker to leave it by the road",
        keyword="imperial",
    ),
}

MYSTERIES = {
    "seal": Mystery(
        label="lost seal",
        phrase="the imperial seal wrapped in blue cloth",
        clue="a blue thread was caught on the gate latch",
        reveal="the seal had fallen from a courier's sleeve and been found by kindness",
        moral="honesty",
        value="Moral Value",
    ),
    "ring": Mystery(
        label="silver ring",
        phrase="a silver ring with a tiny moon on it",
        clue="the ring left a bright half-circle in the dust",
        reveal="the ring belonged to the miller, who had dropped it at dawn",
        moral="kindness",
        value="Moral Value",
    ),
    "key": Mystery(
        label="iron key",
        phrase="an iron key tied to a red string",
        clue="the red string was snagged on a thorn by the path",
        reveal="the key opened a poor widow's pantry, and the traveler chose to return it",
        moral="fairness",
        value="Moral Value",
    ),
}

COMPANIONS = {
    "fox": "a quick fox",
    "goat": "a patient goat",
    "bird": "a small black bird",
    "child": "a younger child",
}

NAMES = ["Mira", "Tobin", "Hana", "Soren", "Lina", "Perry", "Milo", "Esme"]
MORALS = ["honesty", "kindness", "fairness"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def valid_combo(place: str, task: str, mystery: str) -> bool:
    return place in SETTINGS and task in TASKS and mystery in MYSTERIES


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(s.features):
            lines.append(asp.fact("features", sid, feat))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("burden", tid, t.keyword))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("moral", mid, m.moral))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Task, Mystery) :- setting(Place), task(Task), mystery(Mystery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, t, m) for p in SETTINGS for t in TASKS for m in MYSTERIES if valid_combo(p, t, m)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: a schlep, an imperial mystery, and a moral turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--value", choices=MORALS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = [(p, t, m) for p in SETTINGS for t in TASKS for m in MYSTERIES if valid_combo(p, t, m)]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.mystery:
        combos = [c for c in combos if c[2] == args.mystery]
    if args.value:
        combos = [c for c in combos if MYSTERIES[c[2]].moral == args.value]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, mystery = rng.choice(sorted(combos))
    value = args.value or MYSTERIES[mystery].moral
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(list(COMPANIONS))
    return StoryParams(place=place, task=task, mystery=mystery, value=value, name=name, companion=companion)


def _intro(world: World, hero: Entity, task: Task, mystery: Mystery, companion: str) -> None:
    world.say(
        f"Once, in {world.setting.place}, there lived {hero.label}, who could schlep a basket as steadily as a river carries leaves."
    )
    world.say(
        f"{hero.label} was sent to {task.path} with {mystery.phrase}, while {COMPANIONS[companion]} kept pace at {hero.label}'s side."
    )
    world.say(
        f"But {hero.label} knew the {task.burden}, and the road felt long enough to test any heart."
    )


def _mystery_turn(world: World, hero: Entity, task: Task, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"Halfway along the way, {hero.label} found a clue: {mystery.clue}."
    )
    world.say(
        f"That was the mystery to solve. If {hero.label} kept walking, nobody might notice; if {hero.label} spoke true, someone might be helped."
    )
    world.say(
        f"Still, {hero.label} could feel the easy road calling, because {task.cost}."
    )


def _moral_choice(world: World, hero: Entity, mystery: Mystery) -> None:
    world.para()
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes[mystery.moral] = hero.memes.get(mystery.moral, 0.0) + 1
    world.say(
        f"{hero.label} chose {mystery.moral} instead."
    )
    world.say(
        f"{hero.label} carried the matter to the imperial gate and told the keeper what had been seen."
    )
    world.say(
        f"Because the truth was spoken, the keeper smiled and sent help at once."
    )


def _resolution(world: World, hero: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"By dusk, the mystery was solved: {mystery.reveal}."
    )
    world.say(
        f"{hero.label} went home lighter in spirit, though the road had been hard, and the imperial hall shone behind like a lantern in the dark."
    )
    world.say(
        f"The moral of the tale was clear: {mystery.moral} can make a heavy walk feel light."
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    mystery = MYSTERIES[params.mystery]
    task = TASKS[params.task]
    world.facts.update(params=params, hero=hero, mystery=mystery, task=task, setting=world.setting)
    _intro(world, hero, task, mystery, params.companion)
    _mystery_turn(world, hero, task, mystery)
    _moral_choice(world, hero, mystery)
    _resolution(world, hero, mystery)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    m: Mystery = world.facts["mystery"]
    t: Task = world.facts["task"]
    return [
        f"Write a folk tale about {p.name} who must {t.action} through {world.setting.place} while solving a mystery.",
        f"Tell a short story with an imperial road, a clue, and a moral choice about {m.moral}.",
        f"Make a gentle mystery story where a traveler has to schlep something heavy and do the right thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    m: Mystery = world.facts["mystery"]
    t: Task = world.facts["task"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, who must {t.action} and solve the mystery of {m.label}.",
        ),
        QAItem(
            question=f"What made the walk hard for {p.name}?",
            answer=f"The walk was hard because {t.burden}, so the trip to the imperial place took courage.",
        ),
        QAItem(
            question=f"What was the mystery to solve?",
            answer=f"The mystery to solve was {m.phrase}. The clue was {m.clue}, and it led to the reveal that {m.reveal}.",
        ),
        QAItem(
            question=f"What moral value mattered most in the story?",
            answer=f"{m.value} mattered most, and {m.moral} was the choice that helped solve the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does imperial mean?",
            answer="Imperial means belonging to an emperor or a great empire, like an important court or hall ruled from the top.",
        ),
        QAItem(
            question="What does schlep mean?",
            answer="To schlep means to carry something heavy or awkward, usually with a lot of effort over a long way.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that needs clues and careful thinking to understand.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: {e.label or e.kind}")
    lines.append(f"  setting: {world.setting.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="village", task="schlep", mystery="seal", value="honesty", name="Mira", companion="bird"),
    StoryParams(place="bridge", task="carry", mystery="ring", value="kindness", name="Tobin", companion="fox"),
    StoryParams(place="courtyard", task="schlep", mystery="key", value="fairness", name="Hana", companion="goat"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(str(e))
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
