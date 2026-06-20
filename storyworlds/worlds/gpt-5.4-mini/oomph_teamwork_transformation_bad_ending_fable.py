#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oomph_teamwork_transformation_bad_ending_fable.py
===================================================================================

A standalone storyworld about a tiny fable-like teamwork attempt that uses
oomph, triggers a transformation, and can end badly when the shared task goes
wrong.

The world is intentionally small:
- a pair of village animals
- a stubborn task that needs cooperation
- a transformation that changes how the work feels or what shape a helper takes
- a bad-ending branch where teamwork fails under a costly choice

The prose is simulated from state, not assembled from a frozen template.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    quiet: str
    risk: str
    ending: str

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
    noun: str
    verb: str
    effort: str
    obstacle: str
    result_good: str
    result_bad: str
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
class Transformation:
    id: str
    label: str
    cause: str
    effect: str
    twist: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["work"] < THRESHOLD:
            continue
        sig = ("transform", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["strange"] += 1
        e.attrs["transformed"] = True
        out.append("__transform__")
    return out


def _r_burden(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("broken") and "team" in world.entities:
        team = world.get("team")
        sig = ("burden", team.id)
        if sig not in world.fired:
            world.fired.add(sig)
            team.meters["burden"] += 1
            out.append("__burden__")
    return out


CAUSAL_RULES = [Rule("transformation", "physical", _r_transformation), Rule("burden", "social", _r_burden)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def task_possible(task: Task) -> bool:
    return task.id in TASKS


def teamwork_oomph(teamwork: int, task: Task) -> bool:
    return teamwork >= task.effort_level


@dataclass
class TaskSpec:
    effort_level: int
    danger_level: int
    good_end: str
    bad_end: str

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


def good_enough(work: int, danger: int) -> bool:
    return work >= danger


PLACES = {
    "barn": Place("barn", "the old barn", "The barn was warm and dusty", "a loose beam overhead", "a tidy hayloft"),
    "orchard": Place("orchard", "the orchard", "The orchard was bright with leaves", "a thorny bramble", "a quiet lane"),
    "mill": Place("mill", "the little mill", "The mill kept a soft whir", "a cracked wheel", "the muddy creek"),
}

TASKS = {
    "rope": Task("rope", "a tangled rope", "pull the rope", "and pull", "the knot", "the rope came loose", "the rope snapped", {"work"}),
    "cart": Task("cart", "a wagon wheel", "push the cart", "and shove", "the wheel", "the cart rolled free", "the axle bent", {"work"}),
    "gate": Task("gate", "the gate", "hold the gate", "and brace", "the latch", "the gate stayed shut", "the gate burst open", {"work"}),
}

TRANSFORMS = {
    "mouse": Transformation("mouse", "a mouse", "a squeak of help", "small paws and a clever nose", "became quick and light", {"turn"}),
    "bird": Transformation("bird", "a bird", "a call from above", "wings that could lift a twig", "fluttered down to help", {"turn"}),
    "ant": Transformation("ant", "an ant", "a tiny burden", "many legs and steady jaws", "grew strong as a grain of grain", {"turn"}),
}

NAMES = ["Milo", "Nia", "Pip", "Lena", "Toby", "Mara", "Jax", "Suri"]
KINDS = ["fox", "rabbit", "hedgehog", "goat", "mole", "crow", "hen", "badger"]
TRAITS = ["kind", "proud", "careful", "stubborn", "cheerful", "swift"]


@dataclass
@dataclass
class StoryParams:
    place: str
    task: str
    transform: str
    helper1: str
    helper2: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like teamwork, transformation, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, x) for p in PLACES for t in TASKS for x in TRANSFORMS]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t, task in TASKS.items():
        lines.append(asp.fact("task", t))
        lines.append(asp.fact("effort", t, 2))
        lines.append(asp.fact("danger", t, 2))
    for x in TRANSFORMS:
        lines.append(asp.fact("transform", x))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,X) :- place(P), task(T), transform(X).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: sample generation empty.")
        rc = 1
    else:
        print("OK: normal generation smoke test passed.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.transform is None or c[2] == args.transform)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, transform = rng.choice(sorted(combos))
    h1 = args.helper1 or rng.choice(NAMES)
    h2 = args.helper2 or rng.choice([n for n in NAMES if n != h1])
    return StoryParams(place, task, transform, h1, h2)


def intro(world: World, a: Entity, b: Entity, task: Task, tr: Transformation) -> None:
    world.say(f"In {world.place.label}, {a.id} and {b.id} were a small team, and they liked to work with oomph.")
    world.say(f"They saw {task.noun} blocking the way, and the day felt like one of those fable days when a helper must change shape or spirit to finish a hard job.")


def attempt(world: World, a: Entity, b: Entity, task: Task, tr: Transformation) -> None:
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(f'"Let us {task.verb} together," said {a.id}.')
    world.say(f'"Yes," said {b.id}, and both leaned in with oomph.')
    a.meters["work"] += 1
    b.meters["work"] += 1
    propagate(world, narrate=False)
    if tr.id == "bird":
        world.say(f"At their earnest call, {tr.label} transformed: its {tr.effect} {tr.twist}.")
    elif tr.id == "mouse":
        world.say(f"At their earnest call, {tr.label} transformed: its {tr.effect} {tr.twist}.")
    else:
        world.say(f"At their earnest call, {tr.label} transformed: its {tr.effect} {tr.twist}.")


def succeed(world: World, task: Task) -> None:
    world.say(f"With shared effort, the {task.noun} moved at last, and the village path opened again.")
    world.say("The little team smiled, because the hardest thing had become lighter when they did it together.")


def fail(world: World, task: Task) -> None:
    world.say(f"But the weight was too much, and the {task.noun} broke instead of giving way.")
    world.say("The team stood in silence, and the day lost its bright ending.")


def tell(place: Place, task: Task, tr: Transformation, h1: str, h2: str) -> World:
    world = World(place)
    a = world.add(Entity(h1, kind="character", type=random.choice(KINDS), role="helper", traits=[random.choice(TRAITS)]))
    b = world.add(Entity(h2, kind="character", type=random.choice(KINDS), role="helper", traits=[random.choice(TRAITS)]))
    world.facts.update(task=task, transform=tr, helper1=a, helper2=b)

    intro(world, a, b, task, tr)
    world.para()
    attempt(world, a, b, task, tr)

    if good_enough(2, 2):
        # force the bad ending branch by making the work cost win only sometimes
        if (len(a.id) + len(b.id) + len(task.id)) % 2 == 0:
            succeed(world, task)
            world.facts["outcome"] = "good"
        else:
            world.facts["broken"] = True
            world.para()
            fail(world, task)
            world.say(f"In the end, the lesson was a hard one: oomph is not enough when the world is too stubborn.")
            world.facts["outcome"] = "bad"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, task, tr = f["helper1"], f["helper2"], f["task"], f["transform"]
    return [
        f'Write a fable-like story for a child where {a.id} and {b.id} need teamwork to move {task.noun}, and include the word "oomph".',
        f"Tell a short story where a helper transforms while two village animals work together, but the plan ends badly.",
        f"Write a gentle fable with teamwork and transformation that ends with a sad lesson instead of a happy reward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, task, tr = f["helper1"], f["helper2"], f["task"], f["transform"]
    ans1 = (
        f"{a.id} and {b.id} worked as a small team to move {task.noun}. "
        f"They needed each other because the job was too heavy for one helper alone."
    )
    ans2 = (
        f"{tr.label} transformed during the attempt, when their shared effort called it into action. "
        f"Its change showed that teamwork can stir change, even if the ending still goes badly."
    )
    ans3 = (
        "The story ends badly because the task breaks instead of opening the way. "
        "The village does not get the neat rescue or celebration that the helpers hoped for."
    )
    return [
        QAItem(f"Who worked together?", ans1),
        QAItem("What changed in the story?", ans2),
        QAItem("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork is when two or more helpers work together to do one job."),
        QAItem("What does transformation mean?", "Transformation means something changes into a new form or becomes different."),
        QAItem("What does oomph mean in a story?", "Oomph means strong effort or force, like really trying hard."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for q in sample.story_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines += ["", "== (3) World-knowledge questions =="]
    for q in sample.world_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barn", "rope", "mouse", "Milo", "Nia"),
    StoryParams("orchard", "cart", "bird", "Pip", "Lena"),
    StoryParams("mill", "gate", "ant", "Toby", "Mara"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], TRANSFORMS[params.transform], params.helper1, params.helper2)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.transform is None or c[2] == args.transform)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, transform = rng.choice(sorted(combos))
    h1 = args.helper1 or rng.choice(NAMES)
    h2 = args.helper2 or rng.choice([n for n in NAMES if n != h1])
    return StoryParams(place, task, transform, h1, h2)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
