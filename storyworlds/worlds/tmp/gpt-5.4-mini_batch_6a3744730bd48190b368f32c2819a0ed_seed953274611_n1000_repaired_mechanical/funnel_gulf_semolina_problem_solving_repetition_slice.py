#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/funnel_gulf_semolina_problem_solving_repetition_slice.py
=========================================================================================

A small slice-of-life storyworld about a kitchen helper, a stubborn funnel, and
a bowl of semolina that keeps needing one more careful try.

Seed words:
- funnel
- gulf
- semolina

Story shape:
- A child helps in the kitchen.
- A dry ingredient keeps missing the jar on the first try.
- The pair solve the problem by changing the method, trying again, and finishing
  the job neatly.

The world is intentionally tiny and state-driven: the narrative comes from the
simulated kitchen state, not from swapping nouns in a fixed paragraph.
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
TRIALS_TO_TURN = 2


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
    full_name: str = ""
    plural: bool = False

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
class Setting:
    id: str
    place: str
    mood: str
    allowed_tasks: set[str] = field(default_factory=set)
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


@dataclass
class Task:
    id: str
    name: str
    repeat_line: str
    problem_line: str
    use_funnel: bool
    needs_gulf: bool
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
class Ingredient:
    id: str
    label: str
    phrase: str
    fine: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Tool:
    id: str
    label: str
    phrase: str
    helps: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    label: str
    action: str
    success_line: str
    retry_line: str
    power: int
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
        clone.facts = dict(self.facts)
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    task = world.facts.get("task")
    if child.meters["tries"] >= TRIALS_TO_TURN and child.memes["frustration"] >= THRESHOLD:
        sig = ("repeat_turn",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["determination"] += 1
        out.append(task.repeat_line)
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["tries"] >= TRIALS_TO_TURN and world.get("jar").meters["filled"] >= THRESHOLD:
        sig = ("finish",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["pride"] += 1
        out.append("At last, the jar was full and the counter was clean.")
    return out


CAUSAL_RULES = [Rule("repeat", "social", _r_repeat), Rule("finish", "physical", _r_finish)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def task_risky(task: Task, ingredient: Ingredient, tool: Tool) -> bool:
    return task.use_funnel and tool.helps and ingredient.fine


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.power >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, task in TASKS.items():
            for iid, ing in INGREDIENTS.items():
                for tool_id, tool in TOOLS.items():
                    if task_risky(task, ing, tool):
                        combos.append((sid, tid, iid))
    return combos


@dataclass
class StoryParams:
    setting: str
    task: str
    ingredient: str
    tool: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None
    repeats: int = 2
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a kitchen helper, a funnel, and semolina.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=["mother", "father", "grandparent"])
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
    if args.tool and args.ingredient and not task_risky(TASKS[args.task or "pour"], INGREDIENTS[args.ingredient], TOOLS[args.tool]):
        raise StoryError(f"(No story: {TOOLS[args.tool].label} does not help with {INGREDIENTS[args.ingredient].label} in this task.)")
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              if args.task is None or c[1] == args.task
              if args.ingredient is None or c[2] == args.ingredient]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, ingredient = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    fix = args.fix or rng.choice(sorted(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    helper_role = args.helper_role or rng.choice(["mother", "father", "grandparent"])
    return StoryParams(setting=setting, task=task, ingredient=ingredient, tool=tool, fix=fix,
                       child_name=child_name, child_gender=gender, helper_name=helper_name,
                       helper_gender=helper_gender, helper_role=helper_role)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child", label=params.child_name, traits=["careful"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper", label=params.helper_name))
    counter = world.add(Entity(id="counter", type="place", label="the kitchen counter"))
    jar = world.add(Entity(id="jar", type="thing", label=INGREDIENTS[params.ingredient].label))
    funnel = world.add(Entity(id="funnel", type="tool", label=TOOLS[params.tool].label))
    child.memes["joy"] += 1
    world.say(f"On a quiet morning, {params.child_name} helped {helper.label} in {SETTINGS[params.setting].place}.")
    world.say(f'They were working with {INGREDIENTS[params.ingredient].phrase} and a {TOOLS[params.tool].label}.')
    world.para()
    world.say(f"{params.child_name} wanted to use the {TOOLS[params.tool].label} to move the semolina without making a mess.")
    world.say(f"But there was a small gulf between the bowl and the jar, and the first pour wavered.")
    child.meters["tries"] += 1
    child.memes["frustration"] += 1
    jar.meters["filled"] += 0.4
    world.say(f"{params.child_name} tried once, then again, but the grains slid along the edge.")
    child.meters["tries"] += 1
    child.memes["frustration"] += 1
    if params.fix == "tap":
        jar.meters["filled"] += 0.6
        world.say("So they tapped the funnel lightly with a spoon, and the dry grains began to move.")
    elif params.fix == "spoon":
        jar.meters["filled"] += 0.6
        world.say("So they used a spoon to guide the semolina down the funnel, a little at a time.")
    else:
        jar.meters["filled"] += 0.6
        world.say("So they lifted the funnel higher, then lowered it close to the jar until the grains fell neatly.")
    propagate(world)
    world.para()
    world.say(f"{helper.label_word.capitalize()} smiled and said it was fine to need a second try.")
    world.say(f"In the end, the semolina went where it belonged, and the counter stayed mostly clean.")
    world.facts.update(child=child, helper=helper, setting=SETTINGS[params.setting], task=TASKS[params.task],
                       ingredient=INGREDIENTS[params.ingredient], tool=TOOLS[params.tool], fix=FIXES[params.fix],
                       jar=jar, funnel=funnel)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story about {f['child'].label} helping in the kitchen with semolina and a funnel.",
        f"Tell a gentle story where the word funnel appears and a child solves a pouring problem by trying again.",
        f"Write a simple story that includes the words gulf and semolina, and ends with a neat kitchen fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label} and {helper.label}, who were working together in the kitchen."),
        ("What problem did they have?",
         f"The semolina did not pour neatly at first, because there was a little gulf between the bowl and the jar. They had to change the method and try again."),
        ("How did they solve it?",
         f"They used the funnel more carefully and made a small adjustment. After a second try, the grains moved into the jar instead of spilling out."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a funnel for?",
         "A funnel helps guide small things into a narrow opening so they do not spill."),
        ("What is semolina?",
         "Semolina is a dry grainy food, often used for cooking pasta or porridge.") ,
        ("Why is it helpful to try again when something goes wrong?",
         "Trying again can help you notice a better way. A small change can turn a messy problem into a neat solution."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


SETTING_REGISTRY = {
    "kitchen": Setting(id="kitchen", place="the kitchen", mood="quiet", allowed_tasks={"pour"}),
    "breakfast_table": Setting(id="breakfast_table", place="the breakfast table", mood="sunny", allowed_tasks={"pour"}),
}
TASKS = {
    "pour": Task(id="pour", name="pouring semolina", repeat_line="So they tried again, a little slower this time.", problem_line="The grains kept sliding away from the opening.", use_funnel=True, needs_gulf=True, tags={"funnel", "semolina", "problem"}),
}
INGREDIENTS = {
    "semolina": Ingredient(id="semolina", label="semolina", phrase="a bowl of semolina", fine=True, tags={"semolina"}),
}
TOOLS = {
    "funnel": Tool(id="funnel", label="funnel", phrase="a funnel", helps=True, tags={"funnel"}),
}
FIXES = {
    "tap": Fix(id="tap", label="tap the funnel", action="tap", success_line="They tapped the funnel and the semolina slipped through.", retry_line="A tiny tap helped the grains move.", power=2, tags={"repetition"}),
    "spoon": Fix(id="spoon", label="spoon-guide", action="spoon", success_line="They used a spoon to guide the semolina through the funnel.", retry_line="The spoon kept the pour steady.", power=2, tags={"repetition"}),
    "lower": Fix(id="lower", label="lower the funnel", action="lower", success_line="They lowered the funnel close to the jar and the semolina fell neatly.", retry_line="Moving the funnel closer made the pour easier.", power=2, tags={"repetition"}),
}
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for iid in INGREDIENTS:
        lines.append(asp.fact("ingredient", iid))
        lines.append(asp.fact("fine", iid))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
        lines.append(asp.fact("helps", uid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fx.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,I) :- setting(S), task(T), ingredient(I), use_funnel(T), fine(I), helps(funnel).
repeat_turn :- tries(2), frustration(1).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py != cl:
            rc = 1
            print("MISMATCH in valid combos")
        else:
            print(f"OK: gate matches valid_combos() ({len(py)} combos).")
        sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, ingredient=None, tool=None, fix=None, name=None, gender=None, helper=None, helper_gender=None, helper_role=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("setting", SETTING_REGISTRY), ("task", TASKS), ("ingredient", INGREDIENTS), ("tool", TOOLS), ("fix", FIXES)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"invalid {field_name}: {getattr(params, field_name)}")
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child", label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper", label=params.helper_name))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    filt = [c for c in combos
            if args.setting is None or c[0] == args.setting
            if args.task is None or c[1] == args.task
            if args.ingredient is None or c[2] == args.ingredient]
    if not filt:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, ingredient = rng.choice(sorted(filt))
    tool = args.tool or "funnel"
    fix = args.fix or rng.choice(sorted(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    helper_role = args.helper_role or rng.choice(["mother", "father", "grandparent"])
    return StoryParams(setting=setting, task=task, ingredient=ingredient, tool=tool, fix=fix,
                       child_name=name, child_gender=gender, helper_name=helper, helper_gender=helper_gender,
                       helper_role=helper_role)


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
        for combo in combos:
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(setting=s, task=t, ingredient=i, tool="funnel", fix="tap",
                                        child_name="Lily", child_gender="girl", helper_name="Mom", helper_gender="girl",
                                        helper_role="mother"))
                   for s, t, i in valid_combos()]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
