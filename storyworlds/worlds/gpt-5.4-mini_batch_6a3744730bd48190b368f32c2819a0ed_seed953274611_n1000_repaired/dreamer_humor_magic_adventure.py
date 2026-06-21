#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dreamer_humor_magic_adventure.py
=================================================================

A standalone story world for a tiny adventure tale with a dreamer, humor,
and magic. The world keeps a small simulated state: a dreamer, a magical tool,
a funny obstacle, a helper, and a prize. The story begins with a playful
quest, turns when magic behaves in a silly way, and ends when the dreamer
solves the problem and reaches the prize.

This module is self-contained and uses only the standard library plus the
shared result containers in storyworlds/results.py. ASP support is inline and
lazy-imported through storyworlds/asp.py.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    mood: str
    wonder: str
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
class DreamTool:
    id: str
    label: str
    phrase: str
    effect: str
    silly_effect: str
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
class FunnyObstacle:
    id: str
    label: str
    phrase: str
    wobble: str
    easy: bool = True
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
class Prize:
    id: str
    label: str
    phrase: str
    shine: str
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
class Helper:
    id: str
    label: str
    phrase: str
    advice: str
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


def _r_magic_glow(world: World) -> list[str]:
    out = []
    dreamer = world.get("dreamer")
    wand = world.get("wand")
    if dreamer.memes["wonder"] >= THRESHOLD and wand.meters["spark"] >= THRESHOLD:
        sig = ("glow",)
        if sig not in world.fired:
            world.fired.add(sig)
            dreamer.memes["hope"] += 1
            out.append("The magic made the path shine a little brighter.")
    return out


def _r_funny_mess(world: World) -> list[str]:
    out = []
    prism = world.get("prism")
    if prism.meters["tilt"] >= THRESHOLD and ("tilt",) not in world.fired:
        world.fired.add(("tilt",))
        world.get("hall").meters["laugh"] += 1
        out.append("The little prism spun, and the whole room gave a silly sparkle.")
    return out


CAUSAL_RULES = [Rule("glow", _r_magic_glow), Rule("funny_mess", _r_funny_mess)]


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


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("wand").meters["spark"] += 1
    sim.get("prism").meters["tilt"] += 1
    propagate(sim, narrate=False)
    return {
        "glow": sim.get("dreamer").memes["hope"] >= THRESHOLD,
        "laugh": sim.get("hall").meters["laugh"] >= THRESHOLD,
    }


def tell(setting: Setting, tool: DreamTool, obstacle: FunnyObstacle, helper: Helper, prize: Prize,
         name: str = "Milo", gender: str = "boy", parent: str = "mother") -> World:
    world = World()
    dreamer = world.add(Entity(id=name, kind="character", type=gender, role="dreamer"))
    adult = world.add(Entity(id="parent", kind="character", type=parent, role="helper", label="the parent"))
    hall = world.add(Entity(id="hall", type="place", label="the hall"))
    wand = world.add(Entity(id="wand", type="tool", label=tool.label))
    prism = world.add(Entity(id="prism", type="thing", label=obstacle.label))

    dreamer.memes["wonder"] = 1.0
    dreamer.memes["bravery"] = 1.0
    hall.meters["laugh"] = 0.0
    world.facts["setting"] = setting
    world.facts["tool"] = tool
    world.facts["obstacle"] = obstacle
    world.facts["helper"] = helper
    world.facts["prize"] = prize
    world.facts["name"] = name
    world.facts["parent"] = adult

    world.say(
        f"{dreamer.id} was a dreamer who loved {setting.mood} adventures in {setting.place}. "
        f"{setting.wonder}"
    )
    world.say(
        f"One evening, {dreamer.id} found {tool.phrase} and dreamed of a quest for {prize.phrase}."
    )
    world.para()
    world.say(
        f"But the way ahead was blocked by {obstacle.phrase}, and its {obstacle.wobble} made even {dreamer.id} giggle."
    )
    world.say(
        f'"Maybe magic can help," {dreamer.id} said, and {dreamer.pronoun("possessive")} eyes shone with hope.'
    )

    pred = predict(world)
    world.facts["predicted"] = pred
    world.para()

    dreamer.memes["wonder"] += 1
    wand.meters["spark"] += 1
    prism.meters["tilt"] += 1
    world.say(
        f"{dreamer.id} tapped {tool.phrase}; {tool.effect}. Then {obstacle.wobble} sent the prism spinning again, which made everyone laugh."
    )
    propagate(world)

    world.para()
    if pred["glow"]:
        world.say(
            f"{helper.id} smiled and said, \"{helper.advice}\""
        )
    dreamer.memes["joy"] += 1
    dreamer.memes["courage"] += 1
    world.say(
        f"{dreamer.id} listened, steadied the prism, and followed the shining path to {prize.phrase}."
    )
    world.say(
        f"At the end, {prize.shine}, and {dreamer.id} laughed at the very silly magic that had led the way."
    )

    world.facts["outcome"] = "found"
    world.facts["pronoun"] = dreamer.pronoun()
    return world


SETTING_REGISTRY = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="brave",
        wonder="Dusty boxes leaned like sleeping giants, and moonbeams painted stripes across the floor.",
        tags={"attic"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden",
        mood="curious",
        wonder="The flowers glimmered after dusk, as if the night itself wanted to join the game.",
        tags={"garden"},
    ),
    "boat": Setting(
        id="boat",
        place="a little boat",
        mood="bold",
        wonder="The deck rocked softly, and the stars looked close enough to touch.",
        tags={"boat"},
    ),
}

TOOL_REGISTRY = {
    "wand": DreamTool(
        id="wand",
        label="a starry wand",
        phrase="a starry wand",
        effect="a ribbon of silver light hopped into the air",
        silly_effect="a ribbon of silver light hopped into the air and wiggle-waggled like a sleepy snake",
        tags={"magic", "wand"},
    ),
    "lantern": DreamTool(
        id="lantern",
        label="a moon lantern",
        phrase="a moon lantern",
        effect="a warm moon-glow spilled across the floor",
        silly_effect="a warm moon-glow spilled across the floor and tickled the ceiling",
        tags={"magic", "lantern"},
    ),
}

OBSTACLE_REGISTRY = {
    "prism": FunnyObstacle(
        id="prism",
        label="a tiny prism",
        phrase="a tiny prism on a string",
        wobble="its wobble-wobble shimmy",
        easy=True,
        tags={"funny", "prism"},
    ),
    "mop": FunnyObstacle(
        id="mop",
        label="a mop with a ribbon",
        phrase="a mop wearing a ribbon",
        wobble="its fluffy mop-head bobble",
        easy=True,
        tags={"funny", "mop"},
    ),
}

HELPER_REGISTRY = {
    "parent": Helper(
        id="parent",
        label="the parent",
        phrase="the parent",
        advice="A calm hand makes better magic than a rushed one.",
        tags={"helper"},
    ),
    "raccoon": Helper(
        id="raccoon",
        label="a raccoon helper",
        phrase="a raccoon helper",
        advice="Sometimes the cleverest thing is to stop laughing long enough to aim.",
        tags={"helper", "humor"},
    ),
}

PRIZE_REGISTRY = {
    "crown": Prize(
        id="crown",
        label="a cloud crown",
        phrase="a cloud crown",
        shine="the cloud crown glowed like a tiny sunrise",
        tags={"prize"},
    ),
    "map": Prize(
        id="map",
        label="a treasure map",
        phrase="a treasure map",
        shine="the treasure map glittered with a silver X",
        tags={"prize"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "Pia", "Ava"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Owen", "Leo"]
TRAITS = ["curious", "gentle", "bold", "sly", "dreamy"]


@dataclass
class StoryParams:
    setting: str
    tool: str
    obstacle: str
    helper: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTING_REGISTRY:
        for t in TOOL_REGISTRY:
            for o in OBSTACLE_REGISTRY:
                for h in HELPER_REGISTRY:
                    for p in PRIZE_REGISTRY:
                        combos.append((s, t, o, h, p))
    return combos


def explain_rejection(_: str) -> str:
    return "(No story: the chosen mix is too thin for an adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny dreamer adventure with humor and magic.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--tool", choices=TOOL_REGISTRY)
    ap.add_argument("--obstacle", choices=OBSTACLE_REGISTRY)
    ap.add_argument("--helper", choices=HELPER_REGISTRY)
    ap.add_argument("--prize", choices=PRIZE_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.obstacle is None or c[2] == args.obstacle)
              and (args.helper is None or c[3] == args.helper)
              and (args.prize is None or c[4] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, obstacle, helper, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        tool=tool,
        obstacle=obstacle,
        helper=helper,
        prize=prize,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure for a child dreamer and include the word "{f["name"]}".',
        f"Tell a funny magical quest where {f['name']} uses {f['tool'].phrase} to reach {f['prize'].phrase}.",
        f"Write a gentle story with humor and magic where a dreamer keeps going after a silly obstacle makes the quest wobble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    e = world.get(f["name"])
    tool: DreamTool = f["tool"]
    obstacle: FunnyObstacle = f["obstacle"]
    prize: Prize = f["prize"]
    helper: Helper = f["helper"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {f['name']}, a dreamer who wants a tiny adventure. {f['name']} keeps going even when the magic gets silly.",
        ),
        QAItem(
            question="What made the adventure funny?",
            answer=f"The funny part was {obstacle.phrase} and its {obstacle.wobble}. The magic kept wobbling, so the quest turned into a laughing kind of puzzle.",
        ),
        QAItem(
            question="How did the dreamer solve the problem?",
            answer=f"{f['name']} steadied the magic and listened to {helper.id}. That kept the path shining, and then {f['name']} reached {prize.phrase}.",
        ),
        QAItem(
            question="What did the magic tool do?",
            answer=f"It was {tool.phrase}, and it made a trail of light. The light helped the dreamer keep the adventure moving forward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    tool: DreamTool = f["tool"]
    return [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a pretend force that can make impossible things happen in a story. It can glow, change shapes, or help a hero in a special way.",
        ),
        QAItem(
            question="Why do adventure stories have a helper?",
            answer="A helper gives advice, courage, or a clue when the hero is stuck. That makes the journey feel bigger and safer at the same time.",
        ),
        QAItem(
            question=f"What kind of place is {setting.place}?",
            answer=f"{setting.place.capitalize()} is the story's setting, where the dreamer can begin the quest. It gives the adventure its mood and its clues.",
        ),
        QAItem(
            question=f"What is {tool.label} for?",
            answer=f"{tool.phrase} is a magic tool for making light and guiding the way. In this story, it helps the dreamer keep moving.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTING_REGISTRY or params.tool not in TOOL_REGISTRY or params.obstacle not in OBSTACLE_REGISTRY or params.helper not in HELPER_REGISTRY or params.prize not in PRIZE_REGISTRY:
        raise StoryError("(Invalid params: unknown registry key.)")
    setting = SETTING_REGISTRY[params.setting]
    tool = TOOL_REGISTRY[params.tool]
    obstacle = OBSTACLE_REGISTRY[params.obstacle]
    helper = HELPER_REGISTRY[params.helper]
    prize = PRIZE_REGISTRY[params.prize]
    world = World()
    dreamer = world.add(Entity(id=params.name, kind="character", type=params.gender, role="dreamer"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, role="helper", label="the parent"))
    hall = world.add(Entity(id="hall", type="place", label=setting.place))
    wand = world.add(Entity(id="wand", type="tool", label=tool.label))
    prism = world.add(Entity(id="prism", type="thing", label=obstacle.label))
    dreamer.memes["wonder"] = 1.0
    world.facts.update(setting=setting, tool=tool, obstacle=obstacle, helper=helper, prize=prize, name=params.name, parent=parent)

    world.say(
        f"{params.name} was a dreamer in {setting.place}, where every shadow looked ready for an adventure. {setting.wonder}"
    )
    world.say(
        f"One night, {params.name} found {tool.phrase} and imagined finding {prize.phrase}."
    )
    world.para()
    world.say(
        f"Then {params.name} met {obstacle.phrase}; its {obstacle.wobble} made the whole quest wobble like a joke."
    )
    world.say(
        f'"Maybe magic can guide me," {params.name} said, and {params.name} grinned at the sparkle.'
    )
    world.para()
    dreamer.memes["wonder"] += 1
    wand.meters["spark"] += 1
    prism.meters["tilt"] += 1
    propagate(world)
    world.say(
        f"{params.name} steadied the magic, and {helper.id} reminded {dreamer.pronoun()} to keep going one careful step at a time."
    )
    world.say(
        f"At last, {params.name} reached {prize.phrase}, and {prize.shine}."
    )
    world.say(
        f"The adventure ended with a laugh, a bright trail, and a dreamer who felt braver than before."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTING_REGISTRY:
        lines.append(asp.fact("setting", s))
    for t in TOOL_REGISTRY:
        lines.append(asp.fact("tool", t))
    for o in OBSTACLE_REGISTRY:
        lines.append(asp.fact("obstacle", o))
    for h in HELPER_REGISTRY:
        lines.append(asp.fact("helper", h))
    for p in PRIZE_REGISTRY:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,O,H,P) :- setting(S), tool(T), obstacle(O), helper(H), prize(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


CURATED = [
    StoryParams(setting="attic", tool="wand", obstacle="prism", helper="parent", prize="crown", name="Milo", gender="boy", parent="mother", trait="dreamy"),
    StoryParams(setting="garden", tool="lantern", obstacle="mop", helper="raccoon", prize="map", name="Maya", gender="girl", parent="father", trait="curious"),
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
