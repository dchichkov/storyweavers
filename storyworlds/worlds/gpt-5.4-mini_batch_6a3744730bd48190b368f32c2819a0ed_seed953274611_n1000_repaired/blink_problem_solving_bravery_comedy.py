#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blink_problem_solving_bravery_comedy.py
======================================================================

A small, self-contained storyworld about a blinking lamp, a brave child, and a
funny problem-solving rescue.

Premise
-------
A child and a helper discover that their only light keeps blinking out while
they try to reach a lost toy in a dark closet. The child must be brave enough
to investigate, solve the problem with an improvised fix, and turn the scary
moment into a comic little victory.

This world is designed to produce complete, child-facing stories with a clear
setup, a turn driven by world state, and an ending image that proves what
changed.

Features
--------
- typed entities with physical meters and emotional memes
- a forward-chained causal world model
- reasonableness gates for compatible story combinations
- a Python gate and inline ASP twin
- three Q&A sets built from world state, not by parsing rendered prose
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
BRAVERY_THRESHOLD = 2.0
PROBLEM_THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Setting:
    id: str
    place: str
    dark_spot: str
    mood: str
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
class Problem:
    id: str
    label: str
    symptom: str
    cause: str
    fix_hint: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
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


def _r_blink(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lamp")
    if lamp is None:
        return out
    if lamp.meters["flicker"] < THRESHOLD:
        return out
    sig = ("blink",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["frustration"] += 1
    world.get("hero").memes["problem"] += 1
    out.append("The light blinked like a nervous firefly.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lamp")
    if lamp is None:
        return out
    if lamp.meters["fixed"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lamp.meters["flicker"] = 0.0
    lamp.meters["steady"] = 1.0
    world.get("hero").memes["relief"] += 1
    out.append("The blinking stopped, and the room stayed bright.")
    return out


CAUSAL_RULES = [Rule("blink", _r_blink), Rule("fix", _r_fix)]


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


def reasonable_problem(problem: Problem) -> bool:
    return problem.id in PROBLEMS and problem.id != "none"


def reasonable_solution(problem: Problem, response: Response, tool: Tool) -> bool:
    return response.sense >= 2 and problem.id in {"dark_closet", "stuck_switch", "dead_battery"} and tool.id in {"battery", "tap_switch", "wiggle_wire"}


def problem_severity(problem: Problem, delay: int) -> int:
    return 1 + delay if problem.id != "none" else 0


def is_solved(response: Response, problem: Problem, delay: int) -> bool:
    return response.power >= problem_severity(problem, delay)


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    if problem.id != "none":
        sim.get("lamp").meters["flicker"] += 1
        propagate(sim, narrate=False)
    return {"problem": sim.get("hero").memes["problem"] >= THRESHOLD}


def open_scene(world: World, hero: Entity, pal: Entity, setting: Setting, problem: Problem) -> None:
    world.say(
        f"On a funny little evening, {hero.id} and {pal.id} tiptoed into {setting.place}. "
        f"{setting.mood.capitalize()} made the place feel extra dramatic."
    )
    world.say(
        f"They were looking for a missing toy in {setting.dark_spot}, but the only lamp there "
        f"kept blinking."
    )


def complain(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["problem"] += 1
    world.say(
        f'"This is bad," {hero.id} said, and then the lamp blinked again, as if it were trying '
        f'to wink at everybody.'
    )


def brave_step(world: World, hero: Entity, pal: Entity, problem: Problem) -> None:
    hero.memes["bravery"] += 1
    pal.memes["cheer"] += 1
    world.say(
        f"{hero.id} took a deep breath. \"I can check it,\" {hero.pronoun()} said, even though "
        f"{hero.pronoun('possessive')} knees did a tiny jelly dance."
    )
    world.say(f"{pal.id} nodded, trying not to laugh at the jelly knees.")


def inspect(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    world.say(
        f"{hero.id} peeked behind the lamp, holding {tool.phrase} like a treasure map clue."
    )
    world.say(
        f'They noticed {problem.symptom}, which matched the clue: {problem.fix_hint}.'
    )


def repair(world: World, hero: Entity, tool: Tool, lamp: Entity, response: Response) -> None:
    lamp.meters["fixed"] += 1
    body = response.text
    world.say(
        f"With a careful little wiggle and a very serious face, {hero.id} {body}."
    )
    propagate(world, narrate=True)


def celebrate(world: World, hero: Entity, pal: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"Then they found the missing toy under a sock, because of course it had been hiding "
        f"there the whole time."
    )
    world.say(
        f"{hero.id} and {pal.id} laughed so hard they blinked at each other, and the lamp stayed "
        f"steady while the silly treasure hunt went on."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, response: Response,
         hero_name: str = "Mina", hero_gender: str = "girl",
         pal_name: str = "Pip", pal_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_gender, role="pal"))
    lamp = world.add(Entity(id="lamp", type="thing", label="lamp"))
    world.add(Entity(id="toy", type="thing", label="toy"))

    hero.memes["bravery"] = 1.0
    pal.memes["cheer"] = 1.0

    open_scene(world, hero, pal, setting, problem)
    world.para()
    complain(world, hero, problem)
    brave_step(world, hero, pal, problem)
    inspect(world, hero, tool, problem)

    if problem.id == "none":
        world.say("But the lamp was actually fine, and everyone stared at it like it had told a joke.")
    else:
        if not is_solved(response, problem, delay=0):
            world.say(
                f'{hero.id} tried a guess, but it only made the lamp blink harder. '
                f'That was no help at all.'
            )
        repair(world, hero, tool, lamp, response)
        world.para()
        celebrate(world, hero, pal, setting)

    world.facts.update(
        hero=hero, pal=pal, lamp=lamp, setting=setting, problem=problem, tool=tool,
        response=response, solved=lamp.meters["steady"] >= THRESHOLD, blinked=problem.id != "none"
    )
    return world


SETTINGS = {
    "closet": Setting(id="closet", place="the closet", dark_spot="the back shelf", mood="the dark made everyone whisper", tags={"dark"}),
    "attic": Setting(id="attic", place="the attic", dark_spot="the old trunk", mood="the floorboards creaked like old jokes", tags={"dark"}),
    "basement": Setting(id="basement", place="the basement", dark_spot="the workbench corner", mood="the pipes hummed like sleepy robots", tags={"dark"}),
}

PROBLEMS = {
    "stuck_switch": Problem(id="stuck_switch", label="stuck switch", symptom="the switch felt wobbly", cause="dust", fix_hint="it probably needed a careful tap", tags={"electric"}),
    "dead_battery": Problem(id="dead_battery", label="dead battery", symptom="the lamp blinked and dimmed", cause="weak battery", fix_hint="it probably needed a fresh battery", tags={"battery"}),
    "loose_wire": Problem(id="loose_wire", label="loose wire", symptom="the lamp only worked when tilted", cause="a loose wire", fix_hint="it probably needed a gentle wiggle", tags={"wire"}),
}

TOOLS = {
    "battery": Tool(id="battery", label="battery", phrase="a fresh battery", helps="replace power", tags={"battery"}),
    "tap_switch": Tool(id="tap_switch", label="tap-switch trick", phrase="two careful taps", helps="unstick switch", tags={"switch"}),
    "wiggle_wire": Tool(id="wiggle_wire", label="wire-wiggle trick", phrase="a tiny wiggle", helps="tighten wire", tags={"wire"}),
}

RESPONSES = {
    "replace": Response(id="replace", sense=3, power=3, text="replaced the battery and gave the lamp a brave little pat", fail="replaced the battery, but the lamp still blinked like a shy squirrel", qa_text="replaced the battery", tags={"battery"}),
    "tap": Response(id="tap", sense=3, power=2, text="tapped the switch twice and it clicked into place", fail="tapped the switch, but it answered with more blinking", qa_text="tapped the switch twice", tags={"switch"}),
    "wiggle": Response(id="wiggle", sense=2, power=2, text="wiggled the wire until the lamp stopped hiccuping", fail="wiggled the wire, but the lamp kept hiccuping anyway", qa_text="wiggled the wire", tags={"wire"}),
}

@dataclass
class StoryParams:
    theme: str
    problem: str
    tool: str
    response: str
    hero_name: str
    hero_gender: str
    pal_name: str
    pal_gender: str
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


CURATED = [
    StoryParams(theme="closet", problem="dead_battery", tool="battery", response="replace", hero_name="Mina", hero_gender="girl", pal_name="Pip", pal_gender="boy", seed=0),
    StoryParams(theme="attic", problem="stuck_switch", tool="tap_switch", response="tap", hero_name="Nia", hero_gender="girl", pal_name="Bo", pal_gender="boy", seed=1),
    StoryParams(theme="basement", problem="loose_wire", tool="wiggle_wire", response="wiggle", hero_name="Otto", hero_gender="boy", pal_name="June", pal_gender="girl", seed=2),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if problem.id == "dead_battery" and tool.id == "battery":
                    combos.append((sid, pid, tid))
                if problem.id == "stuck_switch" and tool.id == "tap_switch":
                    combos.append((sid, pid, tid))
                if problem.id == "loose_wire" and tool.id == "wiggle_wire":
                    combos.append((sid, pid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A blinky comedy storyworld with bravery and problem solving.")
    ap.add_argument("--theme", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--pal-name")
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, problem, tool = rng.choice(sorted(combos))
    response = args.response or {"dead_battery": "replace", "stuck_switch": "tap", "loose_wire": "wiggle"}[problem]
    hero_name = args.hero_name or rng.choice(["Mina", "Nia", "Otto", "Rae", "Zed"])
    pal_name = args.pal_name or rng.choice(["Pip", "Bo", "June", "Dot", "Fay"])
    if pal_name == hero_name:
        pal_name = pal_name + "2"
    hero_gender = rng.choice(["girl", "boy"])
    pal_gender = "boy" if hero_gender == "girl" else "girl"
    return StoryParams(theme=theme, problem=problem, tool=tool, response=response,
                       hero_name=hero_name, hero_gender=hero_gender,
                       pal_name=pal_name, pal_gender=pal_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "blink" and features {f["hero"].id} solving a light problem.',
        f"Tell a comedy story where {f['hero'].id} is brave, notices a blinking lamp, and fixes it with a simple tool.",
        "Write a small, child-friendly problem-solving story with a brave character, a blinking light, and a silly ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    setting = f["setting"]
    problem = f["problem"]
    response = f["response"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        ("What was the main problem in the story?",
         f"The main problem was that the lamp kept blinking instead of staying steady. That made the dark place harder to explore."),
        (f"What did {hero.id} do first?",
         f"{hero.id} took a brave breath, looked behind the lamp, and tried to figure out what was wrong. {hero.id} did not give up when the lamp acted silly."),
        (f"How did {hero.id} fix it?",
         f"{hero.id} used {tool.phrase} and {response.qa_text} to solve the problem. After that, the lamp stayed on and the room felt much easier to search."),
        ("How did the story end?",
         f"It ended with everyone laughing after the fix, because the missing toy was found in a funny hiding spot. The blinking stopped, so the search could continue safely."),
    ]
    if f.get("solved"):
        qa.append((f"Why was {hero.id} being brave important?",
                    f"{hero.id} had to be brave enough to check the lamp instead of just complaining about it. That brave choice led to the fix and made the whole silly search work."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["tool"].tags) | {"blink"}
    out: list[tuple[str, str]] = []
    if "blink" in tags:
        out.append(("What does blink mean?",
                    "When something blinks, it turns on and off quickly. A light can blink when it is having trouble staying steady."))
    if "battery" in tags:
        out.append(("What does a battery do?",
                    "A battery gives power to things like lamps and toys. Without power, a light may get weak or stop working."))
    if "switch" in tags:
        out.append(("What does a switch do?",
                    "A switch helps turn something on or off. If a switch is stuck, it may need a careful tap or adjustment."))
    if "wire" in tags:
        out.append(("Why can a loose wire be a problem?",
                    "A loose wire can make a light work only sometimes. A gentle fix can help the connection stay steady again."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(problem_id) :- problem(problem_id).
tool(tool_id) :- tool(tool_id).
combo(S, P, T) :- setting(S), problem(P), tool(T), compatible(P, T).
blinked(P) :- problem(P), not fixed(P).
fixed(P) :- response(r), good_response(P, r).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    for pid in PROBLEMS:
        if pid == "dead_battery":
            lines.append(asp.fact("good_response", pid, "replace"))
            lines.append(asp.fact("compatible", pid, "battery"))
        if pid == "stuck_switch":
            lines.append(asp.fact("good_response", pid, "tap"))
            lines.append(asp.fact("compatible", pid, "tap_switch"))
        if pid == "loose_wire":
            lines.append(asp.fact("good_response", pid, "wiggle"))
            lines.append(asp.fact("compatible", pid, "wiggle_wire"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, problem=None, tool=None, response=None, hero_name=None, pal_name=None), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.theme not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.theme], PROBLEMS[params.problem], TOOLS[params.tool], RESPONSES[params.response],
                 hero_name=params.hero_name, hero_gender=params.hero_gender,
                 pal_name=params.pal_name, pal_gender=params.pal_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
