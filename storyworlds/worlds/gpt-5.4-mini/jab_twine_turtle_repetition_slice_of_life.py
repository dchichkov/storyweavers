#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jab_twine_turtle_repetition_slice_of_life.py
=============================================================================

A small slice-of-life storyworld about a child, a pet turtle, and a bit of twine
that keeps getting used the wrong way until a calm grown-up shows a gentler fix.

Seed words: jab, twine, turtle
Style: Slice of Life
Feature: Repetition

Reference premise:
- A child tries to use twine in a quick, pokey way around a turtle's little home.
- The turtle gets uneasy.
- A patient adult repeats a calmer instruction, swaps the setup, and the child
  learns a gentle routine.
- The ending should feel like an ordinary afternoon that turned softer and safer.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- contains a Python reasonableness gate and inline ASP twin
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
SOFT_MIN = 2


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
    detail: str
    rhythm: str
    calm: str
    repeats: int = 1

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    texture: str
    use: str
    safe: bool = True
    awkward: bool = False
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
class Plan:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["repeat"] < THRESHOLD:
            continue
        sig = ("repeat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] += 1
        out.append("__repeat__")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tight"] < THRESHOLD:
            continue
        sig = ("soothe", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["ease"] += 1
        out.append("__ease__")
    return out


CAUSAL_RULES = [
    Rule("repetition", "social", _r_repetition),
    Rule("soothe", "social", _r_soothe),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def _poke(world: World, child: Entity, thing: ObjectThing, narrate: bool = True) -> None:
    child.memes["jab"] += 1
    child.meters["busy"] += 1
    world.get("turtle").meters["startle"] += 1
    world.get("turtle").memes["wary"] += 1
    propagate(world, narrate=narrate)


def risky_use(tool: ObjectThing, target: ObjectThing) -> bool:
    return tool.awkward and target.safe and target.id == "turtle_home"


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SOFT_MIN]


def best_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: p.sense)


def story_settle(world: World, child: Entity, adult: Entity, thing: ObjectThing) -> None:
    child.memes["calm"] += 1
    child.memes["care"] += 1
    adult.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} smiled and kept the tone soft, the way "
        f"ordinary afternoons get softer when somebody remembers to slow down."
    )
    world.say(
        f'"Let\'s not jab at {thing.label}," {adult.label_word} said again. '
        f'"Let\'s wrap the twine, not poke with it."'
    )
    world.say(
        f"{child.id} nodded and tried it the gentle way this time, because the same "
        f"lesson had been said twice, and twice was enough."
    )


def story_setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"On an ordinary afternoon, {child.id} sat with {adult.label_word} near "
        f"the {setting.place}. {setting.detail}"
    )
    world.say(
        f"The room had an easy rhythm, and {setting.rhythm} made the whole day feel "
        f"like it could keep going forever."
    )


def introduce_turtle(world: World, child: Entity, turtle: Entity) -> None:
    child.memes["fond"] += 1
    turtle.memes["content"] += 1
    world.say(
        f"{child.id} liked the little turtle because it moved slowly and never hurried. "
        f"{turtle.id} blinked, took a step, and blinked again."
    )


def tempt(world: World, child: Entity, twine: ObjectThing) -> None:
    child.memes["curious"] += 1
    world.say(
        f"{child.id} wound the twine around {child.pronoun('possessive')} fingers, "
        f"then said, \"Maybe I can jab it through the little knot and make it hold faster.\""
    )
    world.say("The idea sounded quick, and quick ideas can be the pokiest ones.")


def warn(world: World, adult: Entity, child: Entity, thing: ObjectThing) -> None:
    child.memes["repeat"] += 1
    world.say(
        f"{adult.label_word.capitalize()} looked up and said, \"No jabbing the twine. "
        f"Twine is for tying, not poking.\""
    )
    world.say(
        f"Then {adult.label_word} said it again, more gently: \"Wrap, loop, and knot. "
        f"Twine can be patient.\""
    )


def defy(world: World, child: Entity, thing: ObjectThing) -> None:
    child.memes["jab"] += 1
    world.say(
        f"{child.id} tried once more anyway, with {thing.label} in a hurry and no patience at all."
    )


def calm_fix(world: World, adult: Entity, child: Entity, turtle: Entity, plan: Plan) -> None:
    turtle.meters["startle"] = 0.0
    turtle.memes["wary"] = 0.0
    child.memes["repeat"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{adult.label_word.capitalize()} took the twine, showed the loop one step at a time, "
        f"and {plan.text}."
    )
    world.say(
        f"The turtle settled down again, and the room felt ordinary in the nicest way."
    )
    world.say(
        f"{child.id} watched the knot hold, then watched the turtle blink, and the afternoon "
        f"moved on quietly."
    )


def gentle_end(world: World, child: Entity, adult: Entity, turtle: Entity) -> None:
    world.say(
        f"By the end, {child.id} was helping in the calmest way possible, and {turtle.id} "
        f"was back to its slow little steps."
    )


def tell(setting: Setting, twine: ObjectThing, turtle_item: ObjectThing, plan: Plan,
         child_name: str = "Mina", child_gender: str = "girl",
         adult_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id="Parent", kind="character", type=adult_gender, role="adult"))
    turtle = world.add(Entity(id="turtle", kind="character", type="thing", label="the turtle"))
    turtle_home = world.add(Entity(id="turtle_home", label="the turtle's little home"))

    world.facts["setting"] = setting
    world.facts["twine"] = twine
    world.facts["turtle_item"] = turtle_item
    world.facts["plan"] = plan

    story_setup(world, child, adult, setting)
    introduce_turtle(world, child, turtle)
    world.para()
    tempt(world, child, twine)
    warn(world, adult, child, twine)
    defy(world, child, twine)

    world.para()
    if plan.sense >= SOFT_MIN:
        calm_fix(world, adult, child, turtle, plan)
        gentle_end(world, child, adult, turtle)
        outcome = "gentle"
    else:
        turtle.meters["startle"] += 1
        world.say(
            f"{adult.label_word.capitalize()} moved the twine out of reach and reminded {child.id} "
            f"that the turtle liked soft hands more than quick jabs."
        )
        world.say(
            f"{child.id} set the twine down, and the turtle calmed once the poking stopped."
        )
        outcome = "warned"

    world.facts.update(child=child, adult=adult, turtle=turtle, turtle_home=turtle_home,
                       outcome=outcome, repeated=child.memes["repeat"] >= THRESHOLD)
    return world


SETTINGS = {
    "kitchen_table": Setting(
        "kitchen_table",
        "kitchen table",
        "A bowl of apple slices sat nearby, and the afternoon light moved slowly across the table.",
        "the clock ticked softly",
        "the whole room stayed calm",
        repeats=2,
    ),
    "porch": Setting(
        "porch",
        "porch",
        "A little plant leaned in the corner, and the screen door made a sleepy sound when the wind touched it.",
        "the breeze came and went",
        "the chairs stayed still",
        repeats=2,
    ),
    "living_room": Setting(
        "living_room",
        "living room",
        "A folded blanket waited on the couch, and a lamp made the carpet glow warm and yellow.",
        "the afternoon had an easy hush",
        "the house felt gentle",
        repeats=3,
    ),
}

OBJECTS = {
    "twine": ObjectThing("twine", "twine", "a coil of twine", "rough and springy", "tying things", safe=True, awkward=True, tags={"twine"}),
    "turtle": ObjectThing("turtle", "turtle", "a little turtle", "smooth and slow", "being watched", safe=True, awkward=False, tags={"turtle"}),
    "toy_turtle": ObjectThing("toy_turtle", "toy turtle", "a toy turtle", "smooth and bright", "being played with", safe=True, awkward=False, tags={"turtle"}),
}

PLANS = {
    "wrap": Plan(
        "wrap", 3, 3,
        "wrapped the twine around the tiny tag and tied it in a neat bow",
        "kept poking at the knot until it slipped apart",
        "wrapped the twine around the tag and tied a neat bow",
        tags={"twine", "gentle"},
    ),
    "line_up": Plan(
        "line_up", 2, 2,
        "lined the twine up along the edge, then tied it with two calm loops",
        "kept jabbing at the edge, but the twine only bounced away",
        "lined the twine up and tied it with two calm loops",
        tags={"twine", "repetition"},
    ),
}



@dataclass
class StoryParams:
    setting: str
    tool: str
    focus: str
    plan: str
    child: str
    gender: str
    adult: str
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

CURATED = [
    StoryParams("kitchen_table", "twine", "turtle", "wrap", "Mina", "girl", "mother"),
    StoryParams("porch", "twine", "turtle", "line_up", "Jesse", "boy", "father"),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tool in OBJECTS:
            for focus in OBJECTS:
                for plan in PLANS:
                    if tool == "twine" and focus == "turtle" and plan in PLANS:
                        combos.append((sid, tool, focus, plan))
    return combos


def explain_rejection(tool: ObjectThing, focus: ObjectThing) -> str:
    return (
        f"(No story: this scene needs a gentle twine-and-turtle moment. "
        f"Try tool=twine and focus=turtle instead of {tool.label} with {focus.label}.)"
    )


def explain_plan(pid: str) -> str:
    p = PLANS[pid]
    if p.sense < SOFT_MIN:
        return f"(Refusing plan '{pid}': it is too pokey for this gentle turtle story.)"
    return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: twine, a turtle, repetition, and a slice of ordinary life."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=OBJECTS)
    ap.add_argument("--focus", choices=OBJECTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.tool and args.focus and (args.tool != "twine" or args.focus != "turtle"):
        raise StoryError(explain_rejection(OBJECTS[args.tool], OBJECTS[args.focus]))
    if args.plan and args.plan not in PLANS:
        raise StoryError(explain_plan(args.plan))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.focus is None or c[2] == args.focus)
              and (args.plan is None or c[3] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, focus, plan = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mina", "Jesse", "Noah", "Lia", "Ruby"])
    gender = args.gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, tool, focus, plan, child, gender, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.tool], OBJECTS[params.focus], PLANS[params.plan], params.child, params.gender, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        "Write a slice-of-life story about a child, a turtle, and a bit of twine, with the word 'jab' used in a gentle warning scene.",
        f"Tell a calm everyday story where {child.id} keeps touching twine near a turtle, hears the same warning twice, and then learns a softer way.",
        "Write a small home story that repeats the instruction 'twine is for tying, not poking' and ends with a peaceful turtle."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    turtle = f["turtle"]
    plan = f["plan"]
    return [
        ("Who is the story about?", f"It is about {child.id}, {adult.label_word}, and the little turtle. The whole story stays close to an ordinary afternoon at home."),
        ("What did the child want to do with the twine?", f"{child.id} wanted to jab at the twine and make the knot hold faster. {adult.label_word} stopped that idea and repeated a gentler way."),
        ("How did the adult help?", f"{adult.label_word.capitalize()} showed the same instruction twice: wrap, loop, and knot. That repetition helped {child.id} slow down and use the twine gently."),
        ("How did the story end?", f"It ended with {plan.qa_text}. The turtle was calm again, so the scene felt peaceful and complete."),
    ]


WORLD_KNOWLEDGE = {
    "twine": [("What is twine?", "Twine is a thin string used for tying things together. It is helpful when you want a small knot that stays in place.")],
    "turtle": [("What is a turtle?", "A turtle is a slow animal with a hard shell. It likes quiet spaces and gentle handling.")],
    "jab": [("What does jab mean?", "To jab means to poke quickly or sharply. A gentle story can use that word to show a wrong choice that should stop.")],
    "repetition": [("What is repetition in a story?", "Repetition is when words or actions happen again. It can help a child remember a rule or feel the rhythm of a calm day.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"twine", "turtle", "jab", "repetition"}
    out: list[tuple[str, str]] = []
    for k in ["jab", "twine", "turtle", "repetition"]:
        if k in tags:
            out.extend(WORLD_KNOWLEDGE[k])
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
repeat(C) :- child(C), wants_jab(C).
soothed(T) :- turtle(T), calm_fix(T).
outcome(gentle) :- repeat(C), soothed(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    lines.append(asp.fact("soft_min", SOFT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_plan", params.plan),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def valid_story_combo(sid: str, tool: str, focus: str, plan: str) -> bool:
    return tool == "twine" and focus == "turtle" and plan in PLANS and sid in SETTINGS


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(sid, "twine", "turtle", pid) for sid in SETTINGS for pid in PLANS]


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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos")
        for c in valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
