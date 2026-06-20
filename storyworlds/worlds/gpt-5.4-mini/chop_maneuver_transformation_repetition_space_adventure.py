#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chop_maneuver_transformation_repetition_space_adventure.py
=========================================================================================

A small standalone storyworld for a space-adventure seed: a child on a tiny ship
must use careful maneuvers, repeat a pattern, and perform a "chop" action that
changes a broken object into a useful one.

Premise
-------
Two young space explorers are traveling through a glittery drift of space ice and
old satellite debris. A stubborn obstacle blocks their route. They cannot simply
push through; they must chop a path, maneuver the ship, and repeat the right
motion until the obstacle transforms into a safe tunnel or a helpful beacon.

This world models:
- typed entities with physical meters and emotional memes,
- a small causal engine,
- a transformation/repetition story structure,
- child-facing prose and grounded Q&A,
- a Python reasonableness gate plus an inline ASP twin.

The seed words "chop" and "maneuver" are woven into the simulated action, while
the style stays close to a space adventure.
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
SAFE_MIN = 2

BRAVERY_INIT = 5.0
CALM_TRAITS = {"careful", "patient", "steady", "smart"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    transformed_from: str = ""

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
    name: str
    stars: str
    hazard: str
    detail: str

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
    repeated: str
    effect: str
    hazard: str
    zone: str
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


@dataclass
class Tool:
    id: str
    name: str
    phrase: str
    use_text: str
    transforms_to: str
    safe: bool = True
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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone = World(self.setting)
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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["repeated"] < THRESHOLD:
            continue
        sig = ("repeat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["confidence"] += 1
        out.append("__repeat__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["chopped"] < THRESHOLD:
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["transformed"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("repetition", "social", _r_repetition),
    Rule("transformation", "physical", _r_transformation),
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


def hazard_at_risk(task: Task, tool: Tool) -> bool:
    return task.zone in {"ice", "debris", "asteroid"} and tool.safe


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SAFE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def repeat_count(task: Task) -> int:
    return 2 if task.id == "signal" else 3


def severity(task: Task, delay: int) -> int:
    return 2 + delay if task.id == "ice" else 3 + delay


def contained(response: Response, task: Task, delay: int) -> bool:
    return response.power >= severity(task, delay)


def _do_task(world: World, task_ent: Entity, task: Task, narrate: bool = True) -> None:
    task_ent.meters["repeated"] += 1
    task_ent.meters["chopped"] += 1
    propagate(world, narrate=narrate)


def predict_result(world: World, task_id: str) -> dict:
    sim = world.copy()
    task = sim.get(task_id)
    sim_task = sim.facts["task"]
    _do_task(sim, task, sim_task, narrate=False)
    return {
        "transformed": task.meters["transformed"] >= THRESHOLD,
        "confidence": task.memes["confidence"],
    }


def setup(world: World, hero: Entity, mate: Entity, setting: Setting, task: Task) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"In the {setting.name}, {hero.id} and {mate.id} floated past {setting.stars}. "
        f"{setting.detail}"
    )
    world.say(
        f'"Look," said {hero.id}, "the path is blocked by {task.hazard}. '
        f"We need to maneuver through it."
    )


def tempt(world: World, hero: Entity, task: Task, tool: Tool) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f'{hero.id} pointed at {tool.phrase}. "I know! We can use the {tool.name} to chop '
        f'the way open."'
    )
    world.say("For a second, the idea felt daring and bright.")


def warn(world: World, mate: Entity, hero: Entity, task: Task, tool: Tool) -> None:
    mate.memes["caution"] += 1
    world.say(
        f'{mate.id} touched {mate.pronoun("possessive")} chin and said, '
        f'"Careful. {tool.name.capitalize()} can change the ice, but we should only use it '
        f'where the ship can stay safe."'
    )


def maneuver(world: World, hero: Entity, mate: Entity, task: Task) -> None:
    hero.meters["maneuver"] += 1
    mate.meters["maneuver"] += 1
    world.say(
        f"{hero.id} took the controls and began to maneuver in a slow circle around the "
        f"{task.hazard}. The ship blinked once, then steadied."
    )


def repeat_action(world: World, hero: Entity, mate: Entity, task: Task, tool: Tool) -> None:
    count = repeat_count(task)
    for _ in range(count):
        world.get("hazard").meters["chopped"] += 1
        world.get("hazard").meters["repeated"] += 1
    world.say(
        f"{hero.id} and {mate.id} repeated the same careful move {count} times: chop, glide, "
        f"and hold steady."
    )
    world.say(
        f"Each time they did it, the {task.hazard} changed a little more."
    )


def transform(world: World, hazard: Entity, tool: Tool, task: Task) -> None:
    hazard.meters["chopped"] += 1
    hazard.meters["transformed"] += 1
    hazard.transformed_from = task.hazard
    world.say(
        f"At last, the {tool.name} did what it could. The {task.hazard} transformed into "
        f"{tool.transforms_to}, and the narrow way opened like a shining door."
    )


def rescue(world: World, parent: Entity, response: Response, hazard: Entity, task: Task) -> None:
    hazard.meters["transformed"] = 0.0
    body = response.text.replace("{target}", task.hazard)
    world.say(f"{parent.label_word.capitalize()} came rushing in and {body}.")
    world.say("The danger folded away, leaving only a bright trail through the dark.")


def lesson(world: World, parent: Entity, hero: Entity, mate: Entity, tool: Tool) -> None:
    for kid in (hero, mate):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} smiled and said, "
        f'"That was brave. You kept your heads, repeated the right move, and turned '
        f'{tool.phrase} into a safe way forward."'
    )


def finale(world: World, hero: Entity, mate: Entity, setting: Setting, tool: Tool) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"{hero.id} and {mate.id} watched the transformed path sparkle behind them. "
        f"They maneuvered through the new opening, bright and proud, while {setting.stars} "
        f"glimmered like tiny lanterns."
    )


def tell(setting: Setting, task: Task, tool: Tool, response: Response,
         hero_name: str = "Lia", hero_gender: str = "girl",
         mate_name: str = "Pax", mate_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, role="parent", label="the captain"))
    hazard = world.add(Entity(id="hazard", type="thing", label=task.hazard))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.name))
    world.facts["task"] = task
    world.facts["response"] = response
    world.facts["tool"] = tool

    setup(world, hero, mate, setting, task)
    world.para()
    tempt(world, hero, task, tool)
    warn(world, mate, hero, task, tool)
    maneuver(world, hero, mate, task)
    repeat_action(world, hero, mate, task, tool)

    world.para()
    if contained(response, task, delay):
        transform(world, hazard, tool, task)
        lesson(world, parent, hero, mate, tool)
        finale(world, hero, mate, setting, tool)
        outcome = "contained"
    else:
        rescue(world, parent, response, hazard, task)
        world.say("They drifted back to the airlock and watched the obstacle fade from view.")
        outcome = "broken"

    world.facts.update(hero=hero, mate=mate, parent=parent, hazard=hazard, tool_ent=tool_ent,
                       outcome=outcome, delay=delay)
    return world


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
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
    "asteroid": Setting("asteroid belt", "asterisks", "Stars drifted in the window like spilled sugar.", "old space ice", "The ship's walls hummed softly."),
    "moon": Setting("moon base", "moonlight", "The moonlight silvered every panel.", "frozen dust", "The base felt quiet and careful."),
    "nebula": Setting("nebula lane", "violet sparks", "The nebula glowed like a painted sky.", "swirling debris", "The ship rode a pink-and-blue current."),
}

TASKS = {
    "ice": Task("ice", "chop the ice", "chopping the ice again and again", "a clear tunnel", "old space ice", "ice", {"ice"}),
    "debris": Task("debris", "chop the debris", "chopping the debris again and again", "a neat lane", "swirling debris", "debris", {"debris"}),
    "signal": Task("signal", "chop the signal post", "chopping the signal post again and again", "a bright beacon", "a stuck signal post", "asteroid", {"signal"}),
}

TOOLS = {
    "laser_chop": Tool("laser_chop", "laser chopper", "a little laser chopper", "flicked it on and chopped", "a glowing seam", True, {"laser"}),
    "ice_blade": Tool("ice_blade", "ice blade", "an ice blade", "swung it in a safe arc", "a crystal tunnel", True, {"blade"}),
    "pulse_saw": Tool("pulse_saw", "pulse saw", "a pulse saw", "buzzed through the hard stuff", "a shining bridge", True, {"saw"}),
}

RESPONSES = {
    "shield": Response("shield", 3, 4,
                       "raised the shield and steered the ship around the hazard until it was safe",
                       "raised the shield, but the hazard was too wide to stop",
                       "raised the shield and steered the ship to safety",
                       {"shield"}),
    "tractor": Response("tractor", 3, 3,
                        "turned on the tractor beam and pulled the hazard into a tidy line",
                        "turned on the tractor beam, but the hazard kept spinning",
                        "used the tractor beam to pull the hazard aside",
                        {"tractor"}),
    "boost": Response("boost", 2, 2,
                      "threw the ship into a quick boost and slipped away from the hazard",
                      "tried a boost, but there was not enough room to escape",
                      "boosted away from the hazard",
                      {"boost"}),
    "water": Response("water", 1, 1,
                      "sprayed water on the control panel",
                      "sprayed water, but it only made the sparks worse",
                      "sprayed water on the hazard",
                      {"water"}),
}

HEROES = ["Lia", "Nia", "Ari", "Zed", "Milo", "Nova", "Kai", "Rin"]
TRAITS = ["careful", "patient", "steady", "smart", "curious"]
PARTNER = ["Pax", "Tess", "Bo", "Luz", "Ren", "Juno"]

CURATED = [
    StoryParams("asteroid", "ice", "laser_chop", "shield", "Lia", "girl", "Pax", "boy", "mother", 0),
    StoryParams("nebula", "debris", "ice_blade", "tractor", "Nova", "girl", "Ren", "boy", "father", 0),
    StoryParams("moon", "signal", "pulse_saw", "boost", "Kai", "boy", "Luz", "girl", "mother", 0),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for task_id in setting.hazard and TASKS:
            task = TASKS[task_id]
            for tool_id, tool in TOOLS.items():
                if hazard_at_risk(task, tool):
                    combos.append((sid, task_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with chop and maneuver.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SAFE_MIN:
        raise StoryError("(Refusing the low-sense response.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero = args.hero or rng.choice(HEROES)
    mate = args.mate or rng.choice([n for n in PARTNER if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, task, tool, response, hero, hero_gender, mate, mate_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], TOOLS[params.tool], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.mate, params.mate_gender, params.parent, params.delay)
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
    task = f["task"]
    tool = f["tool"]
    return [
        f"Write a space-adventure story for a preschooler that uses the words chop and maneuver and includes {tool.name}.",
        f"Tell a story where two young astronauts must {task.verb}, repeat the same move, and transform the obstacle into a safe passage.",
        f"Write a gentle space story with repetition and transformation where a child says they can chop the hazard and maneuver the ship through the opening.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, parent, task, tool = f["hero"], f["mate"], f["parent"], f["task"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {mate.id}, two young space explorers aboard a tiny ship."),
        ("What problem did they face?",
         f"They had to get past {task.hazard}, which blocked their route through space."),
        ("What repeated action helped them?",
         f"They kept repeating the same careful move over and over, chopping and maneuvering until the path changed."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the obstacle change?",
            f"It transformed into {tool.transforms_to}, so the explorers could move through safely. The repeated chopping helped make the transformation happen."
        ))
        qa.append((
            "What did the grown-up say at the end?",
            f"{parent.label_word.capitalize()} praised them for staying calm and choosing the safe way. The grown-up was glad they used a careful plan instead of rushing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["task"].tags) | set(world.facts["tool"].tags)
    out = []
    if "ice" in tags:
        out.append(("Why can space ice be slippery?", "Space ice can be slippery because it is smooth and hard, so tiny ships can slide around on it."))
    if "debris" in tags:
        out.append(("What is space debris?", "Space debris is old broken pieces floating in space, like bits of metal or tools that are left behind."))
    if "laser" in tags:
        out.append(("What does a laser tool do?", "A laser tool can cut or slice hard material when it is used carefully."))
    if "saw" in tags:
        out.append(("What is a saw for?", "A saw helps cut through something tough when a straight chop would not be enough."))
    if "shield" in tags:
        out.append(("What does a ship shield do?", "A ship shield helps protect the ship from danger while it moves."))
    if "tractor" in tags:
        out.append(("What is a tractor beam?", "A tractor beam is a machine-made pull that can move an object without touching it."))
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
        if e.transformed_from:
            bits.append(f"from={e.transformed_from}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: {tool.name} and {task.hazard} don't make a reasonable space-action pair.)"


ASP_RULES = r"""
hazard(T, U) :- task(T), tool(U).
valid(S, T, U) :- setting(S), task(T), tool(U), hazard(T, U).
repeatable(T) :- task(T).
outcome(contained) :- chosen_response(R), power(R, P), chosen_task(T), severity(T, V), P >= V.
outcome(broken) :- chosen_response(R), power(R, P), chosen_task(T), severity(T, V), P < V.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("severity", tid, 2 if tid == "ice" else 3))
    for uid in TOOLS:
        lines.append(asp.fact("tool", uid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_task", params.task),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    cases = CURATED[:]
    for s in range(20):
        try:
            cases.append(resolve_params(argparse.Namespace(setting=None, task=None, tool=None, response=None,
                                                           hero=None, mate=None, parent=None, delay=None),
                                        random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != ("contained" if contained(RESPONSES[p.response], TASKS[p.task], p.delay) else "broken"))
    if bad == 0:
        print("OK: ASP outcome parity passed.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcome(s).")
    return rc


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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t in combos[:20]:
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
