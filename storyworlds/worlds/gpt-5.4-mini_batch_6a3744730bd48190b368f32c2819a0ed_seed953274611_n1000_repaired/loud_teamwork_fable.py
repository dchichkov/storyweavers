#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/loud_teamwork_fable.py
======================================================

A standalone story world for a small fable-like tale about teamwork and a loud
problem: a farmyard task goes wrong because one helper makes too much noise, the
animals lose focus, and then the group succeeds once they work together more
carefully.

The world is designed to read like a compact fable:
- a clear setup in a humble place,
- a problem caused by loudness,
- a turn through cooperation,
- an ending image that proves the change.

It follows the shared StorySample / QAItem / StoryError contract and includes a
Python reasonableness gate plus an inline ASP twin.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen"}
        male = {"boy", "father", "fox"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    has_echo: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Task:
    id: str
    title: str
    goal: str
    shared: str
    trouble: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class NoiseTool:
    id: str
    label: str
    purpose: str
    loudness: int
    trouble: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    title: str
    method: str
    power: int
    gentleness: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str = "barnyard"
    task: str = "stack_hay"
    noise_tool: str = "bell"
    fix: str = "hand_signs"
    leader_name: str = "Mina"
    helper_name: str = "Pip"
    leader_type: str = "girl"
    helper_type: str = "boy"
    leader_trait: str = "thoughtful"
    helper_trait: str = "eager"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    for task in world.characters():
        if task.meters["confusion"] < THRESHOLD:
            continue
        sig = ("scatter", task.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for helper in world.characters():
            helper.memes["frustration"] += 1
        out.append("__scatter__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if "group" not in world.entities:
        return out
    group = world.get("group")
    if group.meters["teamwork"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    group.meters["progress"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("scatter", "social", _r_scatter),
    Rule("repair", "social", _r_repair),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_noise(world: World, place_id: str, noise_id: str) -> dict:
    sim = world.copy()
    place = sim.get(place_id)
    noise = NOISE_TOOLS[noise_id]
    if place.has_echo or noise.loudness >= 5:
        sim.get("group").meters["confusion"] += 1
    propagate(sim, narrate=False)
    return {
        "confusion": sim.get("group").meters["confusion"],
        "teamwork": sim.get("group").meters["teamwork"],
    }


def valid_combo(place_id: str, task_id: str, noise_id: str, fix_id: str) -> bool:
    place = PLACES[place_id]
    task = TASKS[task_id]
    noise = NOISE_TOOLS[noise_id]
    fix = FIXES[fix_id]
    return (
        task_id in place.tags
        and noise_id in task.tags
        and fix_id in task.tags
        and fix.power >= noise.trouble
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for n in NOISE_TOOLS:
                for f in FIXES:
                    if valid_combo(p, t, n, f):
                        combos.append((p, t, n, f))
    return combos


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.gentleness >= 2]


def explain_rejection(place_id: str, task_id: str, noise_id: str, fix_id: str) -> str:
    place = PLACES[place_id]
    task = TASKS[task_id]
    noise = NOISE_TOOLS[noise_id]
    fix = FIXES[fix_id]
    if noise.trouble > fix.power:
        return (
            f"(No story: {noise.label} makes more trouble than {fix.title} can "
            f"calm. Try a stronger fix.)"
        )
    if task_id not in place.tags:
        return f"(No story: {task.title} does not fit the setting at {place.label}.)"
    return "(No story: this combination does not make a reasonable teamwork tale.)"


def explain_fix_rejection(fid: str) -> str:
    fix = FIXES[fid]
    return (
        f"(Refusing fix '{fid}': it is too rough for a fable-like teamwork story. "
        f"Try one of: {', '.join(f.id for f in sensible_fixes())}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small teamwork fable with a loud problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--noise-tool", choices=NOISE_TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--leader-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--leader-type", choices=["girl", "boy", "hen", "fox"])
    ap.add_argument("--helper-type", choices=["girl", "boy", "hen", "fox"])
    ap.add_argument("--leader-trait")
    ap.add_argument("--helper-trait")
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


def _pick(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.fix not in sensible_fixes_ids():
        raise StoryError(explain_fix_rejection(args.fix))
    combo_pool = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.noise_tool is None or c[2] == args.noise_tool)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combo_pool:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, noise, fix = rng.choice(sorted(combo_pool))
    leader_type = args.leader_type or rng.choice(["girl", "boy", "hen", "fox"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "hen", "fox"])
    leader_name = args.leader_name or rng.choice(["Mina", "Ada", "Nora", "Finn", "Jules"])
    helper_name = args.helper_name or rng.choice(["Pip", "Toby", "Lia", "Bea", "Oren"])
    leader_trait = args.leader_trait or rng.choice(["thoughtful", "steady", "kind", "careful"])
    helper_trait = args.helper_trait or rng.choice(["eager", "brave", "helpful", "quick"])
    return StoryParams(
        place=place,
        task=task,
        noise_tool=noise,
        fix=fix,
        leader_name=leader_name,
        helper_name=helper_name,
        leader_type=leader_type,
        helper_type=helper_type,
        leader_trait=leader_trait,
        helper_trait=helper_trait,
    )


def sensible_fixes_ids() -> list[str]:
    return [f.id for f in sensible_fixes()]


def tell(params: StoryParams) -> World:
    if not all(k in PLACES for k in (params.place,)) or params.task not in TASKS:
        raise StoryError("Invalid story parameters.")
    if params.noise_tool not in NOISE_TOOLS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    if not valid_combo(params.place, params.task, params.noise_tool, params.fix):
        raise StoryError(explain_rejection(params.place, params.task, params.noise_tool, params.fix))

    world = World()
    place = world.add(Entity(id="place", type="place", label=PLACES[params.place].label))
    group = world.add(Entity(id="group", type="group", label="the team"))
    leader = world.add(Entity(id=params.leader_name, kind="character", type=params.leader_type, role="leader", traits=[params.leader_trait]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper", traits=[params.helper_trait]))
    group.meters["teamwork"] = 0.0

    task = TASKS[params.task]
    noise = NOISE_TOOLS[params.noise_tool]
    fix = FIXES[params.fix]

    leader.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"At {place.label}, {leader.id} and {helper.id} began a small task: "
        f"{task.goal}. They believed {task.shared}."
    )
    world.say(
        f"But {noise.label} was so loud that {task.trouble}."
    )

    world.para()
    pred = predict_noise(world, "place", params.noise_tool)
    if pred["confusion"] >= THRESHOLD:
        leader.memes["caution"] += 1
        world.say(
            f"{leader.id} frowned and lifted a hand. \"{noise.label.capitalize()} is too loud,\" "
            f"{leader.pronoun()} said. \"We must use teamwork, not noise.\""
        )
        world.say(
            f"{helper.id} nodded and held still, ready to help in a quieter way."
        )

    if noise.trouble >= 4:
        group.meters["confusion"] += 1
        propagate(world, narrate=False)

    world.para()
    group.meters["teamwork"] += 1
    world.say(
        f"Then they chose {fix.title}: {fix.method}."
    )
    world.say(
        f"{leader.id} guided the plan, and {helper.id} carried the pieces. Little by little, the work moved."
    )
    if fix.power >= noise.trouble:
        group.meters["progress"] += 1
        leader.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f"With quiet hands and shared steps, they finished {task.ending}."
        )
        world.say(
            f"In the end, even the {place.label} felt calm, and the loud trouble was gone."
        )
    else:
        world.say(
            f"Their plan was not strong enough, and the task stayed tangled."
        )

    world.facts.update(
        place=PLACES[params.place],
        task=task,
        noise=noise,
        fix=fix,
        leader=leader,
        helper=helper,
        group=group,
        outcome="done" if fix.power >= noise.trouble else "stuck",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable for a child about {f['leader'].id} and {f['helper'].id}, where a loud helper problem is solved through teamwork.",
        f"Tell a small fable at {f['place'].label} that includes the word 'loud' and ends with the team working together.",
        f"Write a story where noise causes trouble, then cooperation fixes it in a gentle, moral-like ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader, helper, task, noise, fix, place = f["leader"], f["helper"], f["task"], f["noise"], f["fix"], f["place"]
    return [
        QAItem(
            question="What was the loud problem?",
            answer=f"{noise.label} was the loud thing that upset the team. It made the task hard to finish until they changed how they worked.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {fix.title.lower()} and worked together in a calmer way. The leader guided the plan, and the helper carried pieces so the task could be finished.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {task.ending} at {place.label}. The last image shows the team calm, the work complete, and the loud trouble gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and share the work. When each helper does a part, hard jobs become easier.",
        ),
        QAItem(
            question="Why can loud noise be a problem?",
            answer="Loud noise can make it hard to think, listen, or stay calm. When a group is trying to work, too much noise can break their focus.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a simple lesson. It often uses animals or humble characters to show how to act wisely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "barnyard": Place(id="barnyard", label="the barnyard", scene="a simple farmyard", has_echo=False, tags={"stack_hay", "carry_water", "mend_fence"}),
    "orchard": Place(id="orchard", label="the orchard", scene="a quiet orchard", has_echo=False, tags={"pick_apples", "stack_hay"}),
    "courtyard": Place(id="courtyard", label="the courtyard", scene="a stone courtyard", has_echo=True, tags={"carry_water", "mend_fence"}),
}

TASKS = {
    "stack_hay": Task(
        id="stack_hay",
        title="stack hay",
        goal="stack the hay into a neat pile",
        shared="the two could do the work faster together",
        trouble="the hay kept slipping when they rushed",
        ending="a tall, tidy hay stack stood where the mess had been",
        tags={"barnyard", "orchard", "bell", "whistle", "hand_signs", "cloth_cover"},
    ),
    "carry_water": Task(
        id="carry_water",
        title="carry water",
        goal="carry the water buckets to the trough",
        shared="careful steps would keep the water from spilling",
        trouble="the buckets bumped and sloshed when the path got noisy",
        ending="the trough was full and no water was wasted",
        tags={"barnyard", "courtyard", "bell", "whistle", "hand_signs"},
    ),
    "mend_fence": Task(
        id="mend_fence",
        title="mend the fence",
        goal="fix the loose fence rails before dusk",
        shared="steady hands and clear signals would help them fit the boards",
        trouble="the nails kept dropping when everyone talked at once",
        ending="the fence stood straight with every rail in place",
        tags={"barnyard", "courtyard", "whistle", "hand_signs", "cloth_cover"},
    ),
    "pick_apples": Task(
        id="pick_apples",
        title="pick apples",
        goal="gather apples into the basket",
        shared="one could reach high while the other held the basket",
        trouble="the apples rolled away whenever the helper clanged too loudly",
        ending="the basket was full of shining apples",
        tags={"orchard", "hand_signs", "cloth_cover"},
    ),
}

NOISE_TOOLS = {
    "bell": NoiseTool(id="bell", label="a bell", purpose="to call everyone in", loudness=5, trouble=2, tags={"stack_hay", "carry_water", "mend_fence"}),
    "whistle": NoiseTool(id="whistle", label="a whistle", purpose="to signal with a sharp sound", loudness=6, trouble=3, tags={"stack_hay", "carry_water", "mend_fence"}),
    "bucket_clang": NoiseTool(id="bucket_clang", label="a clanging bucket", purpose="to make a big racket", loudness=8, trouble=4, tags={"carry_water", "mend_fence", "stack_hay", "pick_apples"}),
}

FIXES = {
    "hand_signs": Fix(id="hand_signs", title="hand signs", method="they used hand signs instead of shouting", power=4, gentleness=3, tags={"stack_hay", "carry_water", "mend_fence", "pick_apples"}),
    "cloth_cover": Fix(id="cloth_cover", title="a cloth cover", method="they wrapped the noisy tool and spoke softly", power=3, gentleness=2, tags={"stack_hay", "mend_fence", "pick_apples"}),
    "team_steps": Fix(id="team steps", title="team steps", method="they counted their steps together and took turns", power=5, gentleness=3, tags={"stack_hay", "carry_water", "mend_fence"}),
}

CURATED = [
    StoryParams(place="barnyard", task="stack_hay", noise_tool="bell", fix="hand_signs", leader_name="Mina", helper_name="Pip", leader_type="girl", helper_type="boy", leader_trait="thoughtful", helper_trait="eager"),
    StoryParams(place="orchard", task="pick_apples", noise_tool="bucket_clang", fix="cloth_cover", leader_name="Lia", helper_name="Moss", leader_type="girl", helper_type="fox", leader_trait="kind", helper_trait="helpful"),
    StoryParams(place="courtyard", task="carry_water", noise_tool="whistle", fix="team_steps", leader_name="Ned", helper_name="Hana", leader_type="boy", helper_type="girl", leader_trait="steady", helper_trait="quick"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_echo:
            lines.append(asp.fact("echo", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for x in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, x))
    for nid, n in NOISE_TOOLS.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("trouble", nid, n.trouble))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
        lines.append(asp.fact("gentle", fid, f.gentleness))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,N,F) :- place(P), task(T), noise(N), fix(F), affords(P,T), task_tag(T,N), task_tag(T,F), trouble(N,TR), power(F,PO), PO >= TR.
sensible(F) :- fix(F), gentle(F,G), G >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos")
        rc = 1
    if set(asp_sensible_fixes()) == set(sensible_fixes_ids()):
        print("OK: sensible fixes match.")
    else:
        print("MISMATCH in sensible fixes")
        rc = 1
    try:
        s = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not s.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.noise_tool not in NOISE_TOOLS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    if not valid_combo(params.place, params.task, params.noise_tool, params.fix):
        raise StoryError(explain_rejection(params.place, params.task, params.noise_tool, params.fix))
    world = World()
    place = world.add(Entity(id="place", type="place", label=PLACES[params.place].label))
    group = world.add(Entity(id="group", type="group", label="the team"))
    leader = world.add(Entity(id=params.leader_name, kind="character", type=params.leader_type, role="leader", traits=[params.leader_trait]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper", traits=[params.helper_trait]))
    task = TASKS[params.task]
    noise = NOISE_TOOLS[params.noise_tool]
    fix = FIXES[params.fix]
    group.meters["teamwork"] = 0.0

    world.say(f"In {place.label}, {leader.id} and {helper.id} set out to {task.goal}.")
    world.say(f"But {noise.label} made the work feel {task.trouble}.")

    world.para()
    pred = predict_noise(world, "place", params.noise_tool)
    if pred["confusion"] >= THRESHOLD:
        world.say(f"{leader.id} lifted a hand and said, \"{noise.label.capitalize()} is too loud for good work.\"")
        world.say(f"{helper.id} listened at once, and the two began again more quietly.")

    world.para()
    group.meters["teamwork"] += 1
    world.say(f"They chose {fix.title} and followed {fix.method}.")
    world.say(f"{leader.id} guided, {helper.id} helped, and the loudness did not rule the day.")
    if fix.power >= noise.trouble:
        group.meters["progress"] += 1
        leader.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(f"By sunset they had {task.ending}.")
        world.say("So the little place was calm again, and the team was stronger for having worked as one.")
    else:
        world.say("Still, the work stayed tangled, and the task was not finished.")

    world.facts.update(place=place, task=task, noise=noise, fix=fix, leader=leader, helper=helper, group=group)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about {f['leader'].id} and {f['helper'].id} that includes the word loud and teaches teamwork.",
        f"Tell a short animal-friendly moral story about a noisy task at {f['place'].label}.",
        f"Write a child-friendly fable where a loud problem becomes calm through cooperation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What caused the trouble?", answer=f"{f['noise'].label} was too loud, so the helpers could not focus well at first."),
        QAItem(question="What fixed the trouble?", answer=f"They used {f['fix'].title.lower()} and worked together more carefully. The leader guided the plan and the helper followed it."),
        QAItem(question="How did it end?", answer=f"It ended with {f['task'].ending}. The team was calm, and the loudness no longer mattered."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is teamwork?", answer="Teamwork is when people help each other and share a job. It makes hard work easier."),
        QAItem(question="Why is loud noise a problem when people are working?", answer="Loud noise can make it hard to listen and think. A calm voice helps a team stay together."),
        QAItem(question="What is a fable?", answer="A fable is a short story that teaches a lesson. It often uses simple characters and a clear ending."),
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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
