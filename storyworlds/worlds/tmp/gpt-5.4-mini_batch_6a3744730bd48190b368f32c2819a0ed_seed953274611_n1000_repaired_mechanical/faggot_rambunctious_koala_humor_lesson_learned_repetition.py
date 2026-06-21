#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/faggot_rambunctious_koala_humor_lesson_learned_repetition.py
=============================================================================================

A small adventure storyworld about a rambunctious koala, a funny camp mishap,
a repeated warning, and a lesson learned.

The seed words are used in a non-hateful way:
- "faggot" means a bundle of sticks for the campfire
- "rambunctious" describes the koala's energetic behavior
- "koala" is the animal hero of the tale
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"koala"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    detail: str
    dark_spot: str
    adventure_name: str
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
class Item:
    id: str
    label: str
    phrase: str
    makes_flame: bool = False
    safe_light: bool = False
    flammable: bool = False
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
class Hazard:
    id: str
    label: str
    near: str
    spread: int = 2
    flammable: bool = True
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["burning"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if ent.role in {"hero", "friend"}:
                ent.memes["alarm"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook)]


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


def hazard_at_risk(tool: Item, target: Hazard) -> bool:
    return tool.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Hazard, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Hazard, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _ignite(sim, sim.get(target_id), narrate=False)
    return {"burning": sim.get(target_id).meters["burning"] >= THRESHOLD}


def _ignite(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} the koala and {friend.id} set off on an "
        f"adventure through {setting.place}. {setting.detail}"
    )
    world.say(
        f"They called it the {setting.adventure_name}, because even a small trail can feel grand."
    )


def need_light(world: World, hero: Entity, setting: Setting, target: Hazard) -> None:
    world.say(
        f"But {setting.dark_spot} was shadowy and hard to see. {hero.id} peered in and "
        f"needed a light for the next step."
    )


def tempt(world: World, hero: Entity, tool: Item) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id} pointed at a bundle of sticks and grinned. "A faggot for a campfire," '
        f'{hero.id} said with rambunctious excitement. "That will make our path glow!"'
    )
    world.say("The idea sounded funny for a moment, which made the mistake easier to notice.")
    world.say("Still, the same warning deserved to be heard twice.")
    world.say('"A faggot is for the fire, not for play," the friend repeated. "A faggot is for the fire, not for play."')


def warn(world: World, friend: Entity, hero: Entity, tool: Item, target: Hazard) -> None:
    pred = predict_fire(world, "target")
    friend.memes["caution"] += 1
    if pred["burning"]:
        world.facts["danger"] = True
    world.say(
        f'{friend.id} shook their head. "The faggot would start a real flame near {target.label}, '
        f'and that could get too hot too fast."'
    )


def defy(world: World, hero: Entity, tool: Item) -> None:
    hero.memes["defiance"] += 1
    world.say(f'But {hero.id} wobbled with rambunctious energy and reached for the sticks anyway.')


def ignite(world: World, tool_ent: Entity, tool: Item, target: Hazard) -> None:
    _ignite(world, tool_ent)
    world.say(
        f"The first spark caught. The faggot flashed bright, then leaned toward {target.near}, "
        f"and a tiny orange tongue climbed up at once."
    )


def alarm(world: World, hero: Entity, friend: Entity, target: Hazard) -> None:
    world.say(f'"{hero.id}!" {friend.id} cried. "Fire at {target.label}!"')


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: Hazard) -> None:
    target_ent.meters["burning"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    world.say("The flames went out with a hiss, and the smoke drifted away in a soft gray ribbon.")


def lesson(world: World, parent: Entity, hero: Entity, friend: Entity, tool: Item) -> None:
    for e in (hero, friend):
        e.memes["lesson"] += 1
        e.memes["fear"] += 1
        e.memes["relief"] += 1
    world.say(
        f'Then {parent.label_word.capitalize()} knelt down and said, "That was close. '
        f'A faggot belongs in a safe fire, and rambunctious paws belong away from sparks."'
    )
    world.say(
        '"We remember," the friend said, and the koala nodded.'
    )
    world.say(
        'The message was repeated one more time so nobody could miss it: "A faggot is for the fire, not for play."'
    )


def gift(world: World, parent: Entity, hero: Entity, friend: Entity, light: Item) -> None:
    for e in (hero, friend):
        e.memes["joy"] += 1
        e.memes["safety"] += 1
    world.say(
        f"After the lesson, {parent.label_word.capitalize()} handed them a safe lantern that "
        f"glowed without any flame."
    )
    world.say(
        f'{hero.id} held up the lantern, {friend.id} laughed, and the two of them marched on '
        f'through the trail, bright as explorers.'
    )
    world.say("This time the adventure stayed fun, and the faggot stayed tied neatly in a bundle by the campfire ring.")


SENSE_MIN = 2

SETTINGS = {
    "trail": Setting(
        id="trail",
        place="the winding bush trail",
        detail="Tall trees leaned overhead, and the wind made the leaves whisper like secret maps.",
        dark_spot="the hollow under the roots",
        adventure_name="Bush-Trail Adventure",
    ),
    "cave": Setting(
        id="cave",
        place="the cave mouth",
        detail="The rocks were round and warm in the sun, but the path ahead turned dark and echoey.",
        dark_spot="the cave passage",
        adventure_name="Echo Cave Adventure",
    ),
}

TOOLS = {
    "faggot": Item(
        id="faggot",
        label="faggot",
        phrase="a faggot of sticks",
        makes_flame=True,
        tags={"fire", "stick_bundle"},
    ),
    "lantern": Item(
        id="lantern",
        label="lantern",
        phrase="a safe lantern",
        safe_light=True,
        tags={"light"},
    ),
}

TARGETS = {
    "roots": Hazard(
        id="roots",
        label="the roots",
        near="the dry roots",
        spread=2,
        flammable=True,
        tags={"roots", "fire"},
    ),
    "brush": Hazard(
        id="brush",
        label="the brush",
        near="the dry brush",
        spread=3,
        flammable=True,
        tags={"brush", "fire"},
    ),
}

RESPONSES = {
    "stomp": Response(
        id="stomp",
        sense=2,
        power=2,
        text="stomped the little flames out before they could spread across {target}",
        fail="stomped, but the fire leapt out of reach",
        qa_text="stomped the little flames out",
        tags={"fire"},
    ),
    "smother": Response(
        id="smother",
        sense=3,
        power=3,
        text="pulled a jacket over the flame and smothered it before it could spread across {target}",
        fail="tried to smother it, but the fire was already too lively",
        qa_text="pulled a jacket over the flame and smothered it",
        tags={"fire"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Max", "Leo"]
TRAITS = ["curious", "careful", "cheerful", "brave"]

CURATED = [
    {"setting": "trail", "tool": "faggot", "target": "roots", "response": "stomp"},
    {"setting": "cave", "tool": "faggot", "target": "brush", "response": "smother"},
]


@dataclass
class StoryParams:
    setting: str
    tool: str
    target: str
    response: str
    hero_name: str = "Kip"
    friend_name: str = "Mira"
    hero_gender: str = "koala"
    friend_gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOOLS:
            for tg in TARGETS:
                if hazard_at_risk(TOOLS[t], TARGETS[tg]):
                    combos.append((s, t, tg))
    return combos


def explain_rejection(tool: Item, target: Hazard) -> str:
    return f"(No story: {tool.label} can make a flame, but {target.label} would not make a good adventure hazard.)"


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': the story prefers safer, sensible actions.)"


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    tool = TOOLS[params.tool]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]

    hero = world.add(Entity(id=params.hero_name, kind="character", type="koala", role="hero", traits=[params.trait]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="girl", role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    tool_ent = world.add(Entity(id="tool", type="thing", label=tool.label, attrs={"tool": tool.label}))
    target_ent = world.add(Entity(id="target", type="thing", label=target.label, attrs={"target": target.label}))

    setup(world, hero, friend, setting)
    world.para()
    need_light(world, hero, setting, target)
    tempt(world, hero, tool)
    warn(world, friend, hero, tool, target)
    defy(world, hero, tool)
    world.para()
    ignite(world, tool_ent, tool, target)
    alarm(world, hero, friend, target)
    rescue(world, parent, response, target_ent, target)
    lesson(world, parent, hero, friend, tool)
    world.para()
    gift(world, parent, hero, friend, TOOLS["lantern"])

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        setting=setting,
        tool=tool,
        target=target,
        response=response,
        outcome="contained",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write an adventure story for a young child that includes the words "koala", "rambunctious", and "faggot".',
        f"Tell a funny adventure story where {f['hero'].id} the koala gets rambunctious near a campfire bundle, learns a lesson, and repeats the warning.",
        "Write a child-friendly camp adventure with humor, a mistake, a repeated lesson, and a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} the koala and {friend.id}. They go on a bush adventure and learn what to do with fire safely."),
        ("Why did the koala get in trouble?",
         f"{hero.id} got in trouble because the koala was rambunctious and reached for a faggot near a place that could catch fire. That made the scene funny for a moment, but it was also dangerous."),
        ("What did the friend say twice?",
         'The friend repeated, "A faggot is for the fire, not for play." Repeating it helped make the lesson stick.' ),
        ("How did the story end?",
         f"{parent.label_word.capitalize()} gave them a safe lantern, and the adventure kept going without any flame trouble. The koala stayed excited, but the choice was wiser.")
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a koala?",
         "A koala is a tree-climbing animal from Australia. Koalas like to hug branches and sleep a lot."),
        ("What does rambunctious mean?",
         "Rambunctious means noisy, bouncy, and full of energy. It often describes someone who is hard to keep still."),
        ("What is a faggot in this story?",
         "Here, a faggot means a bundle of sticks used for a campfire. It is part of the fire, not a toy."),
        ("Why should fire be handled carefully?",
         "Fire can spread quickly and get hot fast. That is why children should use it only with grown-up help."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(k for k, v in RESPONSES.items() if v.sense >= SENSE_MIN))
    hero_name = rng.choice(BOY_NAMES + GIRL_NAMES + ["Kip"])
    friend_name = rng.choice([n for n in GIRL_NAMES if n != hero_name] or GIRL_NAMES)
    return StoryParams(
        setting=setting,
        tool=tool,
        target=target,
        response=response,
        hero_name=hero_name,
        friend_name=friend_name,
        trait=rng.choice(TRAITS),
    )


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


ASP_RULES = r"""
hazard(Tool, Target) :- makes_flame(Tool), flammable(Target).
valid(Setting, Tool, Target) :- setting(Setting), tool(Tool), target(Target), hazard(Tool, Target).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.makes_flame:
            lines.append(asp.fact("makes_flame", tid))
    for tg, h in TARGETS.items():
        lines.append(asp.fact("target", tg))
        if h.flammable:
            lines.append(asp.fact("flammable", tg))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, tool=None, target=None, response=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        return 1
    if ok:
        print("OK: ASP matches Python and smoke test passed.")
        return 0
    print("MISMATCH: ASP and Python differ.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(setting=s, tool=t, target=g, response="stomp")) for s, t, g in CURATED_COMBOS()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


def CURATED_COMBOS():
    return [("trail", "faggot", "roots"), ("cave", "faggot", "brush")]


if __name__ == "__main__":
    main()
