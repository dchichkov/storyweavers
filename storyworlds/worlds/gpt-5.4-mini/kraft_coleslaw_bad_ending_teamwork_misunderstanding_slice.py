#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kraft_coleslaw_bad_ending_teamwork_misunderstanding_slice.py
===========================================================================================

A standalone story world for a small slice-of-life kitchen story:
two kids try to work together on a family lunch, but a misunderstanding
about what to buy and how to pack it leads to a bad ending.

Seed words and features:
- kraft
- coleslaw
- teamwork
- misunderstanding
- bad ending
- slice of life
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    afford: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    tags: set[str] = field(default_factory=set)
    spoiled_by: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    verb: str
    aim: str
    mismatch: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["confusion"] < THRESHOLD:
            continue
        sig = ("misunderstanding", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hurt"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True
    if narrate:
        return


def task_risk(task: Task, item: Item) -> bool:
    return item.kind in task.mismatch.split("|") or item.kind == task.mismatch


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            for iid, item in ITEMS.items():
                if task_risk(task, item):
                    combos.append((sid, tid, iid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    item1: str
    item2: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", {"cook", "pack"}),
    "apartment": Setting("apartment", "the apartment kitchen", {"cook", "pack"}),
    "picnic": Setting("picnic", "the picnic table", {"pack"}),
}

TASKS = {
    "lunch": Task("lunch", "make lunch", "sandwiches and a side dish", "salad|sauce"),
    "school": Task("school", "pack the lunchbox", "a neat lunchbox", "spill"),
    "potluck": Task("potluck", "bring food to the party", "a shared dish", "side"),
}

ITEMS = {
    "kraft": Item("kraft", "kraft mac and cheese", "a box of kraft mac and cheese", "sauce", {"kraft", "comfort food"}),
    "coleslaw": Item("coleslaw", "coleslaw", "a bowl of coleslaw", "side", {"coleslaw", "crunchy"}),
    "juice": Item("juice", "juice boxes", "a few juice boxes", "drink", {"drink"}),
    "napkins": Item("napkins", "napkins", "a stack of napkins", "paper", {"paper"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Ben", "Max", "Theo", "Sam"]
TRAITS = ["helpful", "careful", "quiet", "busy", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story world about teamwork, a misunderstanding, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item1", choices=ITEMS)
    ap.add_argument("--item2", choices=ITEMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.item1 is None or c[2] == args.item1)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, item1 = rng.choice(sorted(combos))
    item2 = args.item2 or ("coleslaw" if item1 != "coleslaw" else "kraft")
    name1 = args.name1 or rng.choice(GIRL_NAMES if (args.gender1 or rng.choice(["girl","boy"])) == "girl" else BOY_NAMES)
    gender1 = args.gender1 or ("girl" if name1 in GIRL_NAMES else "boy")
    name2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name1])
    gender2 = args.gender2 or ("girl" if name2 in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, task, item1, item2, name1, gender1, name2, gender2, parent)


def introduce(world: World, a: Entity, b: Entity, task: Task, parent: Entity) -> None:
    world.say(f"On a quiet afternoon, {a.id} and {b.id} decided to help {parent.label_word} with {task.verb}.")
    world.say(f"They wanted to work together and make the kitchen feel calm and useful.")


def misunderstanding(world: World, a: Entity, b: Entity, item1: Item, item2: Item, task: Task) -> None:
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(f"{a.id} thought the important thing was the {item1.label}.")
    world.say(f"{b.id} thought the important thing was the {item2.label}.")
    world.say(f"Each one answered the other too quickly, and the plan got fuzzy before anyone noticed.")


def teamwork(world: World, a: Entity, b: Entity) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(f"Still, they kept helping side by side: one opened containers while the other found spoons and bowls.")
    world.say(f"It was the kind of teamwork that usually makes a small job feel easy.")


def bad_turn(world: World, a: Entity, b: Entity, parent: Entity, task: Task, item1: Item, item2: Item) -> None:
    a.memes["confusion"] += 1
    b.memes["confusion"] += 1
    world.say(f"But they had misunderstood the list.")
    world.say(f"They packed the {item1.label} for the wrong part of the meal and set the {item2.label} aside, thinking the other child had it handled.")
    world.say(f"When {parent.label_word} looked in the bag, the lunch was missing the one thing everyone wanted with it.")


def ending_loss(world: World, a: Entity, b: Entity, parent: Entity, task: Task, item1: Item, item2: Item) -> None:
    for e in (a, b):
        e.memes["sad"] += 1
    world.say(f"At school, there was no fixing it.")
    world.say(f"The lunch was awkward and plain, and the {item2.label} stayed home on the counter.")
    world.say(f"That evening, {parent.label_word} said they could try again tomorrow, but the happy moment had already slipped away.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    a = world.add(Entity(params.child1, kind="character", type=params.child1_gender, role="helper"))
    b = world.add(Entity(params.child2, kind="character", type=params.child2_gender, role="helper"))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    item1 = world.add(Entity("item1", label=ITEMS[params.item1].label, type="thing"))
    item2 = world.add(Entity("item2", label=ITEMS[params.item2].label, type="thing"))

    introduce(world, a, b, TASKS[params.task], parent)
    world.para()
    misunderstanding(world, a, b, ITEMS[params.item1], ITEMS[params.item2], TASKS[params.task])
    teamwork(world, a, b)
    world.para()
    bad_turn(world, a, b, parent, TASKS[params.task], ITEMS[params.item1], ITEMS[params.item2])
    ending_loss(world, a, b, parent, TASKS[params.task], ITEMS[params.item1], ITEMS[params.item2])

    world.facts.update(
        a=a, b=b, parent=parent, task=TASKS[params.task], item1=ITEMS[params.item1], item2=ITEMS[params.item2],
        setting=SETTINGS[params.setting], outcome="bad", teamwork=True, misunderstanding=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child about {f["a"].id} and {f["b"].id} helping with {f["task"].verb}, and include the words "kraft" and "coleslaw".',
        f"Tell a story where two children try teamwork in the kitchen, but a misunderstanding about {f['item1'].label} and {f['item2'].label} leads to a bad ending.",
        f'Write a gentle everyday story about helping, mixed-up instructions, and a disappointing finish with kraft and coleslaw.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent, task, item1, item2 = f["a"], f["b"], f["parent"], f["task"], f["item1"], f["item2"]
    return [
        ("Who tried to help in the story?",
         f"{a.id} and {b.id} tried to help {parent.label_word} with {task.verb}. They worked together at first, even though they did not understand the plan the same way."),
        ("What misunderstanding happened?",
         f"{a.id} thought the important thing was the {item1.label}, while {b.id} thought the important thing was the {item2.label}. Because they each assumed the other understood, they packed the wrong thing and left the meal incomplete."),
        ("How did the story end?",
         f"It ended badly, with a disappointing meal and no chance to fix the mistake in time. The children were left sad because their teamwork was real, but their misunderstanding caused the loss."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is kraft mac and cheese?",
         "Kraft mac and cheese is a boxed food that cooks into soft noodles with a cheesy sauce. It is an easy comfort food many children recognize."),
        ("What is coleslaw?",
         "Coleslaw is a cold side dish made from chopped cabbage, often mixed with dressing. It is crunchy and usually served beside other foods."),
        ("What is teamwork?",
         "Teamwork means people help each other and share the work so a job gets done together. It usually works best when everyone understands the plan."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when people think different things are true and do not realize it right away. It can lead to confusion or mistakes."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in TASKS:
            for iid in ITEMS:
                combos.append((sid, tid, iid))
    return combos


ASP_RULES = r"""
valid(S, T, I) :- setting(S), task(T), item(I).
outcome(bad) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("kitchen", "lunch", "kraft", "coleslaw", "Mia", "girl", "Eli", "boy", "mother"),
    StoryParams("apartment", "school", "coleslaw", "kraft", "Noah", "boy", "Ava", "girl", "father"),
    StoryParams("picnic", "potluck", "kraft", "coleslaw", "Lily", "girl", "Sam", "boy", "mother"),
]


def explain_rejection() -> str:
    return "(No story: the chosen combination does not support a believable misunderstanding."


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}' is not applicable in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.item1 is None or c[2] == args.item1)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, item1 = rng.choice(sorted(combos))
    item2 = args.item2 or ("coleslaw" if item1 != "coleslaw" else "kraft")
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    name1 = args.name1 or rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    gender2 = args.gender2 or rng.choice(["girl", "boy"])
    name2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, task, item1, item2, name1, gender1, name2, gender2, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    ap = argparse.ArgumentParser(description="Slice-of-life story world with teamwork, misunderstanding, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item1", choices=ITEMS)
    ap.add_argument("--item2", choices=ITEMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name1} & {p.name2}: {p.item1} and {p.item2}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
